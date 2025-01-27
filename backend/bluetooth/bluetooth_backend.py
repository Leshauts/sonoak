from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import dbus
import dbus.mainloop.glib
import json

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class BluetoothManager:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.websockets = set()
        self.pending_devices = {}
        self.approved_devices = set()

    async def notify_new_device(self, device_path, device_name):
        message = {
            "type": "new_device",
            "device": {
                "id": device_path,
                "name": device_name
            }
        }
        for ws in self.websockets:
            await ws.send_json(message)

    def add_websocket(self, websocket):
        self.websockets.add(websocket)

    def remove_websocket(self, websocket):
        self.websockets.remove(websocket)

    def approve_device(self, device_path):
        try:
            self.approved_devices.add(device_path)
            return True
        except Exception as e:
            print(f"Error approving device: {e}")
            return False

bluetooth_manager = BluetoothManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    bluetooth_manager.add_websocket(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except:
        bluetooth_manager.remove_websocket(websocket)

@app.get("/api/bluetooth/waiting/{device_path}")
async def device_waiting(device_path: str):
    return {"approved": device_path in bluetooth_manager.approved_devices}

@app.post("/api/bluetooth/approve/{device_path}")
async def approve_device(device_path: str):
    success = bluetooth_manager.approve_device(device_path)
    return {"success": success}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)