from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect
from contextlib import asynccontextmanager
from typing import Dict, Any
import asyncio
import logging
import logging.handlers
import os
from datetime import datetime

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

# Handlers de logging "INFO" + "ERROR" + "CRITICAL" (TEMPORAIREMENT DESACTIVE)
'''
file_handler = logging.handlers.RotatingFileHandler(
    os.path.join(log_directory, 'backend.log'),
    maxBytes=1024 * 1024,
    backupCount=5
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(console_handler)
'''

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

    async def initialize_services(self):
        try:
            # 1. WebSocket Manager (dépendance fondamentale)
            self.websocket_manager = WebSocketManager()
            logger.info("WebSocket Manager initialized")

            # 2. Volume Manager
            self.volume_manager = VolumeManager(self.websocket_manager)
            await self.volume_manager.initialize()
            logger.info("Volume Manager initialized")

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

            self.spotify_manager = SpotifyManager(self.websocket_manager, self.audio_manager)
            logger.info("Spotify Manager initialized")

            self.spotify_player = SpotifyPlayerManager(self.websocket_manager, self.spotify_manager)
            logger.info("Spotify Player Manager initialized")

            # 6. Event handlers
            self.bluetooth_events = BluetoothEventHandler(self.bluetooth_manager)
            self.bluetooth_events.setup_signal_handlers()
            logger.info("Bluetooth events handler initialized")

            # 7. Démarrage des services
            await self.start_services()
            
            return True

        except Exception as e:
            logger.error(f"Error during services initialization: {e}", exc_info=True)
            return False

    async def start_services(self):
        """Démarre les services dans l'ordre approprié"""
        try:
            # Vérifie d'abord si Bluetooth est disponible avant de démarrer Snapcast
            bluetooth_available = self.bluetooth_manager is not None and getattr(self.bluetooth_manager, 'initialized', False)
            
            # Démarrage de Spotify
            await self.spotify_manager.connect_to_events()
            await self.spotify_player.start_polling()
            logger.info("Spotify services started")
            
            # Démarrage conditionnel de Snapcast (seulement si explicitement demandé ou si le source actuelle est MACOS)
            current_source = getattr(self.audio_manager, 'current_source', None)
            if current_source and current_source.value == "macos":
                logger.info("Starting Snapcast because current source is MACOS")
                await self.snapcast_manager.get_clients_status()
                logger.info("Snapcast service started")
            else:
                logger.info("Skipping automatic Snapcast startup")
            
            self.update_services_status()
            logger.info("All services started successfully")
        
        except Exception as e:
            logger.error(f"Error starting services: {e}", exc_info=True)
            raise

    def update_services_status(self):
        """Met à jour le statut de tous les services"""
        self.services_status = {
            "bluetooth": {
                "active": self.bluetooth_manager is not None,
                "initialized": getattr(self.bluetooth_manager, 'initialized', False)
            },
            "snapcast": {
                "active": self.snapcast_manager is not None,
                "connected": getattr(self.snapcast_manager, 'server_available', False)
            },
            "spotify": {
                "active": self.spotify_manager is not None,
                "connected": getattr(self.spotify_manager, 'connected', False)
            },
            "volume": {
                "active": self.volume_manager is not None,
                "initialized": getattr(self.volume_manager, 'mixer', None) is not None
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

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Routes API
app.include_router(bluetooth_router, prefix="/api/bluetooth", tags=["bluetooth"])
app.include_router(snapcast_router, prefix="/api/snapcast", tags=["snapcast"])
app.include_router(spotify_router, prefix="/api/spotify", tags=["spotify"])

@app.websocket("/ws/{service}")
async def websocket_endpoint(websocket: WebSocket, service: str):
    client_id = id(websocket)
    logger.debug(f"New WebSocket connection request for service: {service} (client_id: {client_id})")

    if not await service_manager.websocket_manager.connect(websocket, service):
        logger.error(f"Failed to establish WebSocket connection for {service}")
        return

    logger.info(f"WebSocket connected for service: {service} (client_id: {client_id})")

    try:
        while True:
            try:
                data = await websocket.receive_json()
                
                if data.get("type") == "pong":
                    continue

                try:
                    async with asyncio.timeout(5.0):
                        if service == "audio":
                            await service_manager.audio_manager.handle_message(data)
                        elif service == "volume":
                            await service_manager.volume_manager.handle_message(data)
                        elif service == "bluetooth":
                            await service_manager.bluetooth_manager.handle_message(data)
                        elif service == "snapcast":
                            await service_manager.snapcast_manager.handle_message(data)
                        elif service == "spotify":
                            message_type = data.get("type")
                            if message_type in ["play_pause", "next_track", "previous_track", "get_status"]:
                                await service_manager.spotify_player.handle_message(data)
                            else:
                                await service_manager.spotify_manager.handle_message(data)
                        else:
                            logger.warning(f"Unknown service: {service}")
                            
                except asyncio.TimeoutError:
                    logger.error(f"Timeout processing message for {service}")
                    await websocket.send_json({
                        "type": "error",
                        "error": "Request timeout",
                        "service": service
                    })

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected normally for {service} (client_id: {client_id})")
                break
            except Exception as e:
                logger.error(f"Error handling {service} message: {e}", exc_info=True)
                try:
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e),
                        "service": service
                    })
                except:
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected normally for {service} (client_id: {client_id})")
    except Exception as e:
        logger.error(f"WebSocket error for {service}: {e}", exc_info=True)
    finally:
        try:
            logger.info(f"Cleaning up WebSocket for service: {service} (client_id: {client_id})")
            service_manager.websocket_manager.disconnect(websocket, service)
        except Exception as cleanup_error:
            logger.error(f"Error during WebSocket cleanup: {cleanup_error}")

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Endpoint de vérification de santé détaillé"""
    service_manager.update_services_status()
    return {
        "status": "healthy",
        "services": service_manager.services_status,
        "audio": {
            "current_source": service_manager.audio_manager.current_source.value if service_manager.audio_manager else None
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )