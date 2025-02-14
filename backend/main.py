# backend/main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any
from services.audio.manager import AudioManager
from services.volume.manager import VolumeManager
import uvicorn
import logging

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

# Configuration du logging plus détaillée
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    """Endpoint WebSocket pour tous les services"""
    client_id = id(websocket)  # Identifiant unique pour chaque connexion
    logger.debug(f"New WebSocket connection request for service: {service} (client_id: {client_id})")
    
    await websocket_manager.connect(websocket, service)
    logger.info(f"WebSocket connected for service: {service} (client_id: {client_id})")
    
    try:
        while True:
            data = await websocket.receive_json()
            logger.debug(f"Received WebSocket message for {service} (client_id: {client_id}): {data}")
            
            try:
                if service == "audio":
                    logger.debug(f"Handling audio message (client_id: {client_id})")
                    await audio_manager.handle_message(data)
                    
                elif service == "volume":
                    logger.debug(f"Handling volume message (client_id: {client_id})")
                    await volume_manager.handle_message(data)
                    
                elif service == "bluetooth":
                    logger.debug(f"Handling bluetooth message (client_id: {client_id})")
                    await bluetooth_manager.handle_message(data)
                    
                elif service == "snapcast":
                    logger.debug(f"Handling snapcast message (client_id: {client_id})")
                    await snapcast_manager.handle_message(data)
                    
                elif service == "spotify":
                    message_type = data.get("type")
                    logger.debug(f"Handling spotify message type '{message_type}' (client_id: {client_id})")
                    if message_type in ["play_pause", "next_track", "previous_track", "get_status"]:
                        await spotify_player.handle_message(data)
                    else:
                        await spotify_manager.handle_message(data)
                        
                else:
                    logger.warning(f"Unknown service: {service} (client_id: {client_id})")
                    
            except Exception as e:
                logger.error(f"Error handling {service} message (client_id: {client_id}): {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "error": str(e),
                    "service": service
                })
                
    except Exception as e:
        logger.error(f"WebSocket error for {service} (client_id: {client_id}): {e}", exc_info=True)
    finally:
        logger.info(f"Disconnecting WebSocket for service: {service} (client_id: {client_id})")
        websocket_manager.disconnect(websocket, service)

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