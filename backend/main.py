from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect
from contextlib import asynccontextmanager
from typing import Dict, Any
import json
import traceback
import asyncio
import logging
import logging.handlers
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

from core.event_bus import EventBus
from core.plugin_registry import PluginRegistry
from plugins.system_service.volume import VolumePlugin

from services.audio.manager import AudioManager, AudioSource
from services.volume.manager import VolumeManager
from services.bluetooth.manager import BluetoothManager
from services.bluetooth.events import BluetoothEventHandler
from services.bluetooth.routes import router as bluetooth_router, init_routes
from services.snapcast.manager import SnapcastManager
from services.snapcast.routes import router as snapcast_router, init_routes as init_snapcast_routes
from services.spotify.manager import SpotifyManager
from services.spotify.player_manager import SpotifyPlayerManager
from services.spotify.routes import router as spotify_router, init_routes as init_spotify_routes
from services.volume.rotary_controller import RotaryVolumeController
from websocket.manager import WebSocketManager

import uvicorn

# Configuration du logging
log_directory = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_directory, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Configuration commune pour tous les handlers
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configurer pour les erreurs uniquement
logger.setLevel(logging.ERROR)

# Handlers de logging
file_handler = logging.handlers.RotatingFileHandler(
    os.path.join(log_directory, 'backend.log'),
    maxBytes=1024 * 1024,
    backupCount=5
)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# Pour réactiver tous les logs (y compris INFO), décommenter le bloc ci-dessous:
"""
# Configuration pour tous les logs (INFO et plus)
logger.setLevel(logging.INFO)
"""

# Gestionnaires globaux
class ServiceManager:
    def __init__(self):
        self.websocket_manager = None
        self.volume_manager = None
        self.audio_manager = None
        self.bluetooth_manager = None
        self.snapcast_manager = None
        self.spotify_manager = None
        self.spotify_player = None
        self.rotary_controller = None
        self.bluetooth_events = None
        self.services_status = {}
        self.event_bus = None
        self.plugin_registry = None

    async def initialize_services(self):
        try:
            # 1. WebSocket Manager (dépendance fondamentale)
            self.websocket_manager = WebSocketManager()
            logger.info("WebSocket Manager initialized")

            # NOUVEAU: Initialiser le système de plugins
            self.event_bus = EventBus()
            self.plugin_registry = PluginRegistry(self.websocket_manager, self.event_bus)
            logger.info("Plugin system initialized")
            
            # 2. Volume Manager (ancien système)
            self.volume_manager = VolumeManager(self.websocket_manager)
            await self.volume_manager.initialize()
            logger.info("Volume Manager initialized")
            
            # NOUVEAU: Enregistrer et initialiser le plugin Volume
            # Nous gardons les deux systèmes en parallèle pour l'instant
            volume_plugin = VolumePlugin(self.plugin_registry)
            self.plugin_registry.register_plugin(volume_plugin)
            logger.info("Volume Plugin registered")

            # 3. Rotary Controller
            self.rotary_controller = RotaryVolumeController(self.volume_manager)
            await self.rotary_controller.initialize()
            logger.info("Rotary Controller initialized")

            # 4. Audio Manager (dépend de WebSocket)
            self.audio_manager = AudioManager(self.websocket_manager)
            await self.audio_manager.initialize()
            logger.info("Audio Manager initialized")

            # 5. Services de lecture (dépendent de Audio Manager)
            self.bluetooth_manager = BluetoothManager(self.websocket_manager, self.audio_manager)
            logger.info("Bluetooth Manager initialized")

            self.snapcast_manager = SnapcastManager(self.websocket_manager, self.audio_manager)
            logger.info("Snapcast Manager initialized")

            try:
                self.spotify_manager = SpotifyManager(self.websocket_manager, self.audio_manager)
                logger.info("Spotify Manager initialized")

                self.spotify_player = SpotifyPlayerManager(self.websocket_manager, self.spotify_manager)
                logger.info("Spotify Player Manager initialized")
            except Exception as e:
                logger.error(f"Error initializing Spotify services: {e}", exc_info=True)
                self.spotify_manager = None
                self.spotify_player = None

            # Enregistrer les gestionnaires de service dans l'AudioManager
            self.audio_manager.register_service_managers(
                spotify_manager=self.spotify_manager,
                bluetooth_manager=self.bluetooth_manager,
                snapcast_manager=self.snapcast_manager
            )

            # 6. Event handlers
            self.bluetooth_events = BluetoothEventHandler(self.bluetooth_manager)
            self.bluetooth_events.setup_signal_handlers()
            logger.info("Bluetooth events handler initialized")

            # 7. Démarrage des services
            await self.start_services()
            
            await self.plugin_registry.initialize_plugins()
            logger.info("All plugins initialized")
            
            return True

        except Exception as e:
            logger.error(f"Error during services initialization: {e}", exc_info=True)
            return False

    async def start_services(self):
        """Démarre les services dans l'ordre approprié"""
        try:
            # Vérifie d'abord si Bluetooth est disponible avant de démarrer Snapcast
            bluetooth_available = self.bluetooth_manager is not None and getattr(self.bluetooth_manager, 'initialized', False)
            
            # Démarrage de Spotify (seulement si initialisé)
            if self.spotify_manager is not None:
                try:
                    await self.spotify_manager.connect_to_events()
                    if self.spotify_player is not None:
                        await self.spotify_player.start_polling()
                    logger.info("Spotify services started")
                except Exception as e:
                    logger.error(f"Error starting Spotify services: {e}", exc_info=True)
            
            # Démarrage conditionnel de Snapcast (seulement si explicitement demandé ou si le source actuelle est MACOS)
            if self.audio_manager:
                current_source = getattr(self.audio_manager, 'current_source', None)
                if current_source and current_source.value == "macos" and self.snapcast_manager:
                    logger.info("Starting Snapcast because current source is MACOS")
                    await self.snapcast_manager.get_clients_status()
                    logger.info("Snapcast service started")
                else:
                    logger.info("Skipping automatic Snapcast startup")
            
            self.update_services_status()
            logger.info("All services started successfully")
        
        except Exception as e:
            logger.error(f"Error starting services: {e}", exc_info=True)
            # Ne pas lever l'exception pour permettre au serveur de continuer malgré les erreurs
            # raise

    def update_services_status(self):
        """Met à jour le statut de tous les services"""
        self.services_status = {
            "bluetooth": {
                "active": self.bluetooth_manager is not None,
                "initialized": getattr(self.bluetooth_manager, 'initialized', False) if self.bluetooth_manager else False
            },
            "snapcast": {
                "active": self.snapcast_manager is not None,
                "connected": getattr(self.snapcast_manager, 'server_available', False) if self.snapcast_manager else False
            },
            "spotify": {
                "active": self.spotify_manager is not None,
                "connected": getattr(self.spotify_manager, 'connected', False) if self.spotify_manager else False
            },
            "volume": {
                "active": self.volume_manager is not None,
                "initialized": getattr(self.volume_manager, 'mixer', None) is not None if self.volume_manager else False
            }
        }

    def cleanup(self):
        """Nettoie les ressources des services"""
        if self.rotary_controller:
            self.rotary_controller.cleanup()
        
        # Autres nettoyages si nécessaire
        logger.info("Services cleanup completed")

service_manager = ServiceManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    logger.info("Starting application...")
    
    try:
        if await service_manager.initialize_services():
            logger.info("All services initialized successfully")
        else:
            logger.error("Failed to initialize all services")
            
        yield
        
    except Exception as e:
        logger.error(f"Critical error during startup: {e}", exc_info=True)
        raise
    finally:
        logger.info("Shutting down application...")
        service_manager.cleanup()

app = FastAPI(lifespan=lifespan)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Gestionnaire d'exceptions global pour éviter les erreurs 500 silencieuses"""
    
    # Journaliser l'erreur avec la stack trace complète
    logger.error(f"Exception non gérée lors du traitement de {request.url}:")
    logger.error(traceback.format_exc())
    
    # Détecter des types d'erreurs spécifiques
    error_type = type(exc).__name__
    error_message = str(exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": error_type,
            "message": error_message,
            "path": str(request.url),
            "method": request.method
        }
    )
    
# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialisation des routes 
if service_manager.bluetooth_manager:
    init_routes(service_manager.bluetooth_manager)  # Pour Bluetooth
if service_manager.snapcast_manager:
    init_snapcast_routes(service_manager.snapcast_manager)  # Pour Snapcast
if service_manager.spotify_manager and service_manager.spotify_player:
    init_spotify_routes(service_manager.spotify_manager, service_manager.spotify_player)  # Pour Spotify

# Routes API
app.include_router(bluetooth_router, prefix="/api/bluetooth", tags=["bluetooth"])
app.include_router(snapcast_router, prefix="/api/snapcast", tags=["snapcast"])
app.include_router(spotify_router, prefix="/api/spotify", tags=["spotify"])

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = id(websocket)
    logger.debug(f"Nouvelle connexion WebSocket (client_id: {client_id})")

    # Établir la connexion avec gestion d'erreur
    try:
        await service_manager.websocket_manager.connect(websocket, "global")
        logger.info(f"WebSocket connecté (client_id: {client_id})")
    except Exception as e:
        logger.error(f"Erreur lors de la connexion WebSocket: {e}")
        return

    try:
        while True:
            try:
                data = await websocket.receive_json()
                
                # Ignorer les messages pong (réponse aux pings)
                if data.get("type") == "pong":
                    continue

                # Extraire le service cible et le message
                service = data.get("service", "global")
                message = data.get("message", {})
                
                if not message:
                    logger.warning(f"Message sans contenu pour le service {service}")
                    continue
                
                logger.debug(f"Message reçu pour {service}: {message}")
                
                # Ajouter un timeout pour éviter les blocages
                try:
                    async with asyncio.timeout(5.0):
                        # Traitement selon le service avec vérification que le service existe
                        if service == "audio":
                            if service_manager.audio_manager:
                                await service_manager.audio_manager.handle_message(message)
                            else:
                                await websocket.send_json({
                                    "service": service,
                                    "type": "error",
                                    "error": "Audio manager not available"
                                })
                        elif service == "volume":
                            if service_manager.volume_manager:
                                await service_manager.volume_manager.handle_message(message)
                            else:
                                await websocket.send_json({
                                    "service": service,
                                    "type": "error",
                                    "error": "Volume manager not available"
                                })
                        elif service == "bluetooth":
                            if service_manager.bluetooth_manager:
                                await service_manager.bluetooth_manager.handle_message(message)
                            else:
                                await websocket.send_json({
                                    "service": service,
                                    "type": "error",
                                    "error": "Bluetooth manager not available"
                                })
                        elif service == "snapcast":
                            if service_manager.snapcast_manager:
                                await service_manager.snapcast_manager.handle_message(message)
                            else:
                                await websocket.send_json({
                                    "service": service,
                                    "type": "error",
                                    "error": "Snapcast manager not available"
                                })
                        elif service == "spotify":
                            message_type = message.get("type")
                            if message_type in ["play_pause", "next_track", "previous_track", "get_playback_status", "seek"]:
                                if service_manager.spotify_player:
                                    await service_manager.spotify_player.handle_message(message)
                                else:
                                    await websocket.send_json({
                                        "service": service,
                                        "type": "error",
                                        "error": "Spotify player not available"
                                    })
                            else:
                                if service_manager.spotify_manager:
                                    await service_manager.spotify_manager.handle_message(message)
                                else:
                                    await websocket.send_json({
                                        "service": service,
                                        "type": "error",
                                        "error": "Spotify manager not available"
                                    })
                        elif service_manager.plugin_registry:
                            try:
                                await service_manager.plugin_registry.handle_message(service, message)
                            except Exception as e:
                                logger.error(f"Erreur plugin pour {service}: {e}")
                                await websocket.send_json({
                                    "service": service,
                                    "type": "error",
                                    "error": f"Plugin error: {str(e)}"
                                })
                        # Le else final reste inchangé
                        else:
                            logger.warning(f"Service inconnu: {service}")
                            await websocket.send_json({
                                "service": service,
                                "type": "error",
                                "error": "Unknown service"
                            })
                            
                except asyncio.TimeoutError:
                    logger.error(f"Timeout pendant le traitement du message pour {service}")
                    await websocket.send_json({
                        "service": service,
                        "type": "error",
                        "error": "Request timeout"
                    })

            except WebSocketDisconnect:
                logger.info(f"WebSocket déconnecté normalement (client_id: {client_id})")
                break
            except json.JSONDecodeError:
                logger.error(f"Erreur de décodage JSON pour le client {client_id}")
                try:
                    await websocket.send_json({
                        "service": "global",
                        "type": "error",
                        "error": "Invalid JSON format"
                    })
                except:
                    break
            except Exception as e:
                logger.error(f"Erreur de traitement du message: {e}", exc_info=True)
                try:
                    await websocket.send_json({
                        "service": "global",
                        "type": "error",
                        "error": str(e)
                    })
                except:
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket déconnecté normalement (client_id: {client_id})")
    except Exception as e:
        logger.error(f"Erreur WebSocket: {e}", exc_info=True)
    finally:
        try:
            logger.info(f"Nettoyage de la connexion WebSocket (client_id: {client_id})")
            service_manager.websocket_manager.disconnect(websocket, "global")
        except Exception as cleanup_error:
            logger.error(f"Erreur pendant le nettoyage WebSocket: {cleanup_error}")

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    service_manager.update_services_status()
    
    plugins_status = {}
    if service_manager.plugin_registry:
        for plugin_id, plugin in service_manager.plugin_registry.plugins.items():
            plugins_status[plugin_id] = {
                "name": plugin.name,
                "active": plugin.is_active,
                "type": plugin.plugin_type
            }
    
    return {
        "status": "healthy",
        "services": service_manager.services_status,
        "audio": {
            "current_source": service_manager.audio_manager.current_source.value if service_manager.audio_manager else None
        },
        "plugins": plugins_status  # Ajouter cette info
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )