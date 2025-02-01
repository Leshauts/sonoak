# sonoak/backend/services/spotify/routes.py

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

# Référence au manager spotify (sera initialisé dans main.py)
spotify_manager = None

def init_routes(manager):
    global spotify_manager
    spotify_manager = manager

@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Récupère l'état actuel de la connexion Spotify"""
    if not spotify_manager:
        raise HTTPException(status_code=500, detail="Spotify manager not initialized")
    
    return {
        "status": spotify_manager.current_status,
        "connected": spotify_manager.is_connected() if hasattr(spotify_manager, 'is_connected') else False
    }

@router.get("/playback")
async def get_playback() -> Dict[str, Any]:
    """Récupère l'état actuel de la lecture Spotify"""
    if not spotify_manager:
        raise HTTPException(status_code=500, detail="Spotify manager not initialized")
    
    try:
        playback_status = spotify_manager.get_playback_status() if hasattr(spotify_manager, 'get_playback_status') else None
        return {
            "track_name": playback_status.get("track_name") if playback_status else None,
            "artist_names": playback_status.get("artist_names", []) if playback_status else [],
            "album_name": playback_status.get("album_name") if playback_status else None,
            "album_cover_url": playback_status.get("album_cover_url") if playback_status else None,
            "duration": playback_status.get("duration", 0) if playback_status else 0,
            "position": playback_status.get("position", 0) if playback_status else 0,
            "is_playing": playback_status.get("is_playing", False) if playback_status else False,
            "volume": playback_status.get("volume", 0) if playback_status else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))