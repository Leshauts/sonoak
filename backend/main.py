from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any
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
from websocket.manager import WebSocketManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application"""
    global websocket_manager, bluetooth_manager, snapcast_manager, spotify_manager
    global spotify_player, navigation_manager, bluetooth_events

    logger.info("Initializing services...")
    
    try:
        # Initialisation des gestionnaires
        websocket_manager = WebSocketManager()
        bluetooth_manager = BluetoothManager(websocket_manager)
        snapcast_manager = SnapcastManager(websocket_manager)
        spotify_manager = SpotifyManager(websocket_manager)
        spotify_player = SpotifyPlayerManager(websocket_manager, spotify_manager)
        navigation_manager = NavigationManager(websocket_manager)

        # Initialisation des gestionnaires d'événements
        bluetooth_events = BluetoothEventHandler(bluetooth_manager)
        bluetooth_events.setup_signal_handlers()

        # Initialisation des routes
        init_routes(bluetooth_manager)
        init_snapcast_routes(snapcast_manager)
        init_spotify_routes(spotify_manager)

        # Démarrage des services
        logger.info("Starting services...")
        await snapcast_manager.get_clients_status()
        await spotify_manager.connect_to_events()
        await spotify_player.start_polling()

        yield
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        logger.info("Shutting down services...")
        # Ajoutez ici le code de nettoyage si nécessaire

# Création de l'application FastAPI
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
    await websocket_manager.connect(websocket, service)
    try:
        while True:
            data = await websocket.receive_json()
            try:
                if service == "bluetooth":
                    await bluetooth_manager.handle_message(data)
                elif service == "snapcast":
                    await snapcast_manager.handle_message(data)
                elif service == "spotify":
                    message_type = data.get("type")
                    if message_type in ["play_pause", "next_track", "previous_track", "get_status"]:
                        await spotify_player.handle_message(data)
                    else:
                        await spotify_manager.handle_message(data)
                elif service == "navigation":
                    await navigation_manager.handle_message(data)
                else:
                    logger.warning(f"Unknown service: {service}")
            except Exception as e:
                logger.error(f"Error handling {service} message: {e}")
                await websocket.send_json({"error": str(e)})
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        websocket_manager.disconnect(websocket, service)

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Endpoint de vérification de santé"""
    return {
        "status": "healthy",
        "services": {
            "bluetooth": bluetooth_manager is not None,
            "snapcast": snapcast_manager is not None,
            "spotify": spotify_manager is not None
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )