from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from services.bluetooth.manager import BluetoothManager
from services.bluetooth.events import BluetoothEventHandler
from services.bluetooth.routes import router as bluetooth_router, init_routes
from services.snapcast.manager import SnapcastManager  # Nouveau import
from services.snapcast.routes import router as snapcast_router, init_routes as init_snapcast_routes  # Nouveau import
from websocket.manager import WebSocketManager
import uvicorn

app = FastAPI()

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialisation des gestionnaires
websocket_manager = WebSocketManager()
bluetooth_manager = BluetoothManager(websocket_manager)
snapcast_manager = SnapcastManager(websocket_manager)  # Nouveau gestionnaire

# Initialisation des gestionnaires d'événements
bluetooth_events = BluetoothEventHandler(bluetooth_manager)
bluetooth_events.setup_signal_handlers()

# Initialisation des routes
init_routes(bluetooth_manager)
init_snapcast_routes(snapcast_manager)  # Initialisation des routes Snapcast

# Inclure les routes
app.include_router(bluetooth_router, prefix="/api/bluetooth", tags=["bluetooth"])
app.include_router(snapcast_router, prefix="/api/snapcast", tags=["snapcast"])  # Nouvelles routes

@app.websocket("/ws/{service}")
async def websocket_endpoint(websocket: WebSocket, service: str):
    await websocket_manager.connect(websocket, service)
    try:
        while True:
            data = await websocket.receive_json()
            if service == "bluetooth":
                await bluetooth_manager.handle_message(data)
            elif service == "snapcast":
                await snapcast_manager.handle_message(data)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        websocket_manager.disconnect(websocket, service)

@app.on_event("startup")
async def startup_event():
    """Événement de démarrage de l'application"""
    print("Starting Bluetooth and Snapcast Services...")
    # Initialisation du statut Snapcast
    await snapcast_manager.get_clients_status()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)