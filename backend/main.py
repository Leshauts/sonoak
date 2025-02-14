# backend/main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect
from contextlib import asynccontextmanager
from typing import Dict, Any
import asyncio  # Ajoutez cette ligne
import logging
import logging.handlers
import os
from datetime import datetime

from services.audio.manager import AudioManager
from services.volume.manager import VolumeManager
import uvicorn

# Vos imports existants
from services.bluetooth.manager import BluetoothManager
from services.bluetooth.events import BluetoothEventHandler
from services.bluetooth.routes import router as bluetooth_router, init_routes
from services.snapcast.manager import SnapcastManager
from services.snapcast.routes import router as snapcast_router, init_routes as init_snapcast_routes
from services.spotify.manager import SpotifyManager
from services.spotify.player_manager import SpotifyPlayerManager
from services.spotify.routes import router as spotify_router, init_routes as init_spotify_routes
from services.navigation.manager import NavigationManager
from services.volume.rotary_controller import RotaryVolumeController
from websocket.manager import WebSocketManager

# Créer le dossier logs s'il n'existe pas
log_directory = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_directory, exist_ok=True)

# Configuration du logging de base
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Création du logger principal
logger = logging.getLogger(__name__)

# Configuration du file handler avec rotation
file_handler = logging.handlers.RotatingFileHandler(
    os.path.join(log_directory, 'backend.log'),
    maxBytes=1024 * 1024,  # 1MB
    backupCount=5
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(file_handler)

# Ajout d'un handler pour la console
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(console_handler)

# Gestionnaires globaux
websocket_manager = None
bluetooth_manager = None
snapcast_manager = None
spotify_manager = None
spotify_player = None
navigation_manager = None
bluetooth_events = None
volume_manager = None
audio_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global websocket_manager, bluetooth_manager, snapcast_manager, spotify_manager
    global spotify_player, audio_manager, bluetooth_events, volume_manager, rotary_controller

    logger.info("Initializing services...")
    
    try:
        # Websocket Manager
        websocket_manager = WebSocketManager()
        logger.debug("WebSocket Manager initialized")
        
        # Volume Manager
        volume_manager = VolumeManager(websocket_manager)
        await volume_manager.initialize()
        logger.debug("Volume Manager initialized")
        
        # Rotary Controller
        rotary_controller = RotaryVolumeController(volume_manager)
        await rotary_controller.initialize()
        logger.debug("Rotary Controller initialized")
        
        # Audio Manager
        audio_manager = AudioManager(websocket_manager)
        await audio_manager.initialize()
        logger.debug("Audio Manager initialized")
        
        # Service Managers
        bluetooth_manager = BluetoothManager(websocket_manager, audio_manager)
        logger.debug("Bluetooth Manager initialized")
        
        snapcast_manager = SnapcastManager(websocket_manager, audio_manager)
        logger.debug("Snapcast Manager initialized")
        
        spotify_manager = SpotifyManager(websocket_manager, audio_manager)
        logger.debug("Spotify Manager initialized")
        
        spotify_player = SpotifyPlayerManager(websocket_manager, spotify_manager)
        logger.debug("Spotify Player Manager initialized")

        # Event handlers
        bluetooth_events = BluetoothEventHandler(bluetooth_manager)
        bluetooth_events.setup_signal_handlers()
        logger.debug("Event handlers initialized")

        # Initialize routes
        init_routes(bluetooth_manager)
        init_snapcast_routes(snapcast_manager)
        init_spotify_routes(spotify_manager)
        logger.debug("Routes initialized")

        # Start services
        logger.info("Starting services...")
        await snapcast_manager.get_clients_status()
        await spotify_manager.connect_to_events()
        await spotify_player.start_polling()

        yield
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise
    finally:
        logger.info("Shutting down services...")
        # Nettoyage du rotary controller
        if 'rotary_controller' in globals():
            rotary_controller.cleanup()
        
app = FastAPI(lifespan=lifespan)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Inclure les routes
app.include_router(bluetooth_router, prefix="/api/bluetooth", tags=["bluetooth"])
app.include_router(snapcast_router, prefix="/api/snapcast", tags=["snapcast"])
app.include_router(spotify_router, prefix="/api/spotify", tags=["spotify"])

@app.websocket("/ws/{service}")
async def websocket_endpoint(websocket: WebSocket, service: str):
    """Enhanced WebSocket endpoint with better disconnect handling"""
    client_id = id(websocket)
    logger.debug(f"New WebSocket connection request for service: {service} (client_id: {client_id})")
    
    if not await websocket_manager.connect(websocket, service):
        logger.error(f"Failed to establish WebSocket connection for {service}")
        return
    
    logger.info(f"WebSocket connected for service: {service} (client_id: {client_id})")
    
    try:
        while True:
            try:
                data = await websocket.receive_json()
                logger.debug(f"Received WebSocket message for {service} (client_id: {client_id}): {data}")
                
                # Handle ping/pong for connection health check
                if data.get("type") == "pong":
                    continue
                
                # Service-specific message handling with timeouts
                try:
                    async with asyncio.timeout(5.0):
                        if service == "audio":
                            await audio_manager.handle_message(data)
                        elif service == "volume":
                            await volume_manager.handle_message(data)
                        elif service == "bluetooth":
                            await bluetooth_manager.handle_message(data)
                        elif service == "snapcast":
                            await snapcast_manager.handle_message(data)
                        elif service == "spotify":
                            message_type = data.get("type")
                            if message_type in ["play_pause", "next_track", "previous_track", "get_status"]:
                                await spotify_player.handle_message(data)
                            else:
                                await spotify_manager.handle_message(data)
                        else:
                            logger.warning(f"Unknown service: {service} (client_id: {client_id})")
                except asyncio.TimeoutError:
                    logger.error(f"Timeout processing message for {service}")
                    try:
                        await websocket.send_json({
                            "type": "error",
                            "error": "Request timeout",
                            "service": service
                        })
                    except Exception as e:
                        logger.error(f"Failed to send timeout error: {e}")
                    
            except starlette.websockets.WebSocketDisconnect:
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
                except Exception as send_error:
                    logger.error(f"Failed to send error message: {send_error}")
                    break
                
    except starlette.websockets.WebSocketDisconnect:
        logger.info(f"WebSocket disconnected normally for {service} (client_id: {client_id})")
    except Exception as e:
        logger.error(f"WebSocket error for {service}: {e}", exc_info=True)
    finally:
        try:
            logger.info(f"Cleaning up WebSocket for service: {service} (client_id: {client_id})")
            websocket_manager.disconnect(websocket, service)
        except Exception as cleanup_error:
            logger.error(f"Error during WebSocket cleanup: {cleanup_error}")

# Add this rate limiting class
class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
        
    async def can_proceed(self, client_id: str) -> bool:
        now = datetime.now()
        if client_id not in self.requests:
            self.requests[client_id] = []
            
        # Remove old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if (now - req_time).total_seconds() < self.time_window
        ]
        
        if len(self.requests[client_id]) >= self.max_requests:
            return False
            
        self.requests[client_id].append(now)
        return True

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Endpoint de vérification de santé"""
    return {
        "status": "healthy",
        "services": {
            "bluetooth": bluetooth_manager is not None,
            "snapcast": snapcast_manager is not None,
            "spotify": spotify_manager is not None,
            "volume": volume_manager is not None
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
    
        # reload=True,
        # log_level="debug"