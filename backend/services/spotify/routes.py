#backend/services/spotify/routes.py

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

# Référence au manager spotify (sera initialisé dans main.py)
spotify_manager = None
spotify_player_manager = None  # Ajoutez cette ligne

def init_routes(manager, player_manager=None):  # Modifiez cette ligne pour accepter player_manager
    global spotify_manager, spotify_player_manager
    spotify_manager = manager
    spotify_player_manager = player_manager  # Initialisez spotify_player_manager

@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Récupère l'état actuel de la connexion Spotify"""
    if not spotify_manager:
        raise HTTPException(status_code=500, detail="Spotify manager not initialized")
    
    # Retourner l'état de la connexion
    return {
        "status": {
            "connected": getattr(spotify_manager, 'current_status', {}).get('connected', False),
            "username": getattr(spotify_manager, 'current_status', {}).get('username'),
            "device_name": getattr(spotify_manager, 'current_status', {}).get('device_name')
        }
    }

@router.get("/playback")
async def get_playback() -> Dict[str, Any]:
    """Récupère l'état actuel de la lecture Spotify"""
    if not spotify_manager:
        raise HTTPException(status_code=500, detail="Spotify manager not initialized")
    
    if not spotify_player_manager:
        # Si spotify_player_manager n'est pas disponible, retourner des valeurs par défaut
        return {
            "track_name": None,
            "artist_names": [],
            "album_name": None,
            "album_cover_url": None,
            "duration": 0,
            "position": 0,
            "is_playing": False,
            "volume": 0
        }
    
    try:
        # Récupérer l'état actuel si disponible
        track_meta = getattr(spotify_player_manager, 'current_track_metadata', None)
        playback_state = getattr(spotify_player_manager, 'playback_state', {})
        
        if not track_meta:
            return {
                "track_name": None,
                "artist_names": [],
                "album_name": None,
                "album_cover_url": None,
                "duration": 0,
                "position": 0,
                "is_playing": False,
                "volume": 0
            }
        
        return {
            "track_name": track_meta.get("track_name"),
            "artist_names": track_meta.get("artist_names", []),
            "album_name": track_meta.get("album_name"),
            "album_cover_url": track_meta.get("album_cover_url"),
            "duration": track_meta.get("duration", 0),
            "position": track_meta.get("position", 0),
            "is_playing": playback_state.get("is_playing", False),
            "volume": playback_state.get("volume", 0)
        }
    except Exception as e:
        # Log l'erreur mais retourner un objet valide plutôt qu'une erreur 500
        print(f"Erreur lors de la récupération du playback: {e}")
        return {
            "track_name": None,
            "artist_names": [],
            "album_name": None,
            "album_cover_url": None,
            "duration": 0,
            "position": 0,
            "is_playing": False,
            "volume": 0
        }