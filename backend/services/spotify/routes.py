from fastapi import APIRouter, HTTPException

router = APIRouter()

# Référence au manager spotify (sera initialisé dans main.py)
spotify_manager = None

def init_routes(manager):
    global spotify_manager
    spotify_manager = manager

@router.get("/status")
async def get_status():
    """Récupère l'état actuel de la connexion Spotify"""
    if not spotify_manager:
        raise HTTPException(status_code=500, detail="Spotify manager not initialized")
    
    return spotify_manager.current_status
