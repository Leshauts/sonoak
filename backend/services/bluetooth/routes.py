from fastapi import APIRouter, HTTPException
from typing import Dict, List

router = APIRouter()

# Référence au manager bluetooth (sera initialisé dans main.py)
bluetooth_manager = None

def init_routes(manager):
    global bluetooth_manager
    bluetooth_manager = manager

@router.get("/status")
async def get_status():
    """Récupère l'état actuel de la connexion Bluetooth"""
    if not bluetooth_manager:
        raise HTTPException(status_code=500, detail="Bluetooth manager not initialized")
    
    return {
        "connected_device": bluetooth_manager.connected_device,
        "has_active_connection": bluetooth_manager.connected_device is not None
    }

@router.post("/disconnect")
async def disconnect_current():
    """Déconnecte l'appareil actuellement connecté"""
    if not bluetooth_manager:
        raise HTTPException(status_code=500, detail="Bluetooth manager not initialized")
    
    if not bluetooth_manager.connected_device:
        raise HTTPException(status_code=404, detail="No device currently connected")
    
    success = await bluetooth_manager.disconnect_current_device()
    return {"success": success}