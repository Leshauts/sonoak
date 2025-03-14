# backend/services/snapcast/routes.py

from fastapi import APIRouter, HTTPException
from typing import Dict

router = APIRouter()

# Référence au manager snapcast (sera initialisé dans main.py)
snapcast_manager = None

def init_routes(manager):
    global snapcast_manager
    snapcast_manager = manager

@router.get("/status")
async def get_status():
    """Récupère l'état actuel des clients Snapcast"""
    if not snapcast_manager:
        raise HTTPException(status_code=500, detail="Snapcast manager not initialized")
    
    success = await snapcast_manager.get_clients_status()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to get Snapcast status")
    
    return {
        "clients": snapcast_manager.clients
    }

@router.post("/volume/{client_id}")
async def set_client_volume(client_id: str, volume: int):
    """Modifie le volume d'un client Snapcast"""
    if not snapcast_manager:
        raise HTTPException(status_code=500, detail="Snapcast manager not initialized")
    
    if volume < 0 or volume > 100:
        raise HTTPException(status_code=400, detail="Volume must be between 0 and 100")
    
    success = await snapcast_manager.set_client_volume(client_id, volume)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to set client volume")
    
    return {"success": True}