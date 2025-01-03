import React, { useState, useEffect, useCallback } from 'react';

const SpotifyController = () => {
  const [playerState, setPlayerState] = useState({
    playing: false,
    currentTrack: {
      title: "Aucune piste en lecture",
      artist: "",
      album: "",
      albumArt: ""
    },
    lastUpdate: Date.now()
  });
  const [isLoading, setIsLoading] = useState(false);

  const fetchCurrentTrack = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:3001/api/player/current-track');
      if (!response.ok) throw new Error('Failed to fetch current track');
      const data = await response.json();
      
      if (data.currentTrack?.title && 
          data.currentTrack?.artist) {
        setPlayerState(data);
      }
    } catch (error) {
      console.error('Error fetching current track:', error);
    }
  }, []);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:3001');
    
    ws.onopen = () => {
      console.log('WebSocket Connected');
      fetchCurrentTrack();
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'state_update') {
        console.log('Received state update:', {
          title: data.currentTrack?.title,
          hasArt: !!data.currentTrack?.albumArt
        });

        setPlayerState(prevState => {
          // Ne pas mettre à jour si les données sont plus anciennes
          if (data.lastUpdate <= prevState.lastUpdate) {
            return prevState;
          }

          return {
            playing: isLoading ? prevState.playing : data.playing,
            currentTrack: {
              ...data.currentTrack,
              // Garder l'ancienne image si la nouvelle est manquante
              albumArt: data.currentTrack?.albumArt || prevState.currentTrack.albumArt
            },
            lastUpdate: data.lastUpdate
          };
        });
      }
    };

    return () => {
      ws.close();
    };
  }, [fetchCurrentTrack, isLoading]);

  const handlePlayPause = async () => {
    setIsLoading(true);
    const action = playerState.playing ? 'pause' : 'play';
    
    try {
      const response = await fetch(`http://localhost:3001/api/player/${action}`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error(`Failed to ${action}`);
      // Ne pas modifier l'état ici, laisser le WebSocket le faire
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = async (direction) => {
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:3001/api/player/${direction}`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error(`Failed to ${direction}`);
      setTimeout(() => fetchCurrentTrack(), 100);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // JSX reste inchangé...
  return (
    <div className="flex flex-col items-center p-8 max-w-md mx-auto bg-white rounded-lg shadow-lg">
      <div className="w-64 h-64 mb-6 rounded-lg overflow-hidden shadow-lg">
        {playerState.currentTrack.albumArt ? (
          <img 
            src={playerState.currentTrack.albumArt} 
            alt="Album artwork" 
            className="w-full h-full object-cover"
            onError={(e) => {
              console.error('Error loading album art:', e);
              e.target.src = ''; // Effacer l'image en cas d'erreur
            }}
          />
        ) : (
          <div className="w-full h-full bg-gray-200 flex items-center justify-center">
            <span className="text-gray-400">Pas de couverture</span>
          </div>
        )}
      </div>

      <div className="w-full text-center mb-8">
        <h2 className="text-xl font-bold truncate">
          {playerState.currentTrack.title}
        </h2>
        <p className="text-gray-600 truncate">
          {playerState.currentTrack.artist}
        </p>
        <p className="text-gray-500 text-sm truncate">
          {playerState.currentTrack.album}
        </p>
      </div>

      <div className="flex items-center space-x-6">
        <button 
          onClick={() => handleSkip('previous')}
          disabled={isLoading}
          className="p-2 hover:bg-gray-100 rounded-full transition-colors disabled:opacity-50"
        >
          ⏮️
        </button>

        <button 
          onClick={handlePlayPause}
          disabled={isLoading}
          className="p-4 bg-green-500 hover:bg-green-600 rounded-full text-white transition-colors disabled:opacity-50"
        >
          {playerState.playing ? '⏸️' : '▶️'}
        </button>

        <button 
          onClick={() => handleSkip('next')}
          disabled={isLoading}
          className="p-2 hover:bg-gray-100 rounded-full transition-colors disabled:opacity-50"
        >
          ⏭️
        </button>
      </div>
    </div>
  );
};

export default SpotifyController;