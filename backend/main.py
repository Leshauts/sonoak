from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from services.bluetooth.manager import BluetoothManager
from services.bluetooth.events import BluetoothEventHandler
from services.bluetooth.routes import router as bluetooth_router, init_routes
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

# Initialisation des gestionnaires d'événements
bluetooth_events = BluetoothEventHandler(bluetooth_manager)
bluetooth_events.setup_signal_handlers()

# Initialisation des routes
init_routes(bluetooth_manager)

# Inclure les routes
app.include_router(bluetooth_router, prefix="/api/bluetooth", tags=["bluetooth"])

@app.websocket("/ws/{service}")
async def websocket_endpoint(websocket: WebSocket, service: str):
    await websocket_manager.connect(websocket, service)
    try:
        while True:
            data = await websocket.receive_json()
            if service == "bluetooth":
                await bluetooth_manager.handle_message(data)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        websocket_manager.disconnect(websocket, service)

@app.on_event("startup")
async def startup_event():
    """Événement de démarrage de l'application"""
    print("Starting Bluetooth Service...")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)