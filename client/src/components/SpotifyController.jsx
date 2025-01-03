import React, { useState, useEffect } from 'react';

const SpotifyController = () => {
  const [playerState, setPlayerState] = useState({
    playing: false,
    currentTrack: {
      title: "Aucune piste en lecture",
      artist: "",
      album: "",
      albumArt: ""
    }
  });
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:3001');
    
    ws.onopen = () => {
      console.log('WebSocket Connected');
      fetch('http://localhost:3001/api/player/current-track')
        .then(res => res.json())
        .then(data => {
          console.log('Initial state:', data);
          setPlayerState(data);
        });
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setPlayerState(prevState => ({
        ...prevState,
        playing: data.playing,
        currentTrack: {
          ...data.currentTrack,
          albumArt: data.currentTrack.albumArt
        }
      }));
    };

    return () => ws.close();
  }, []);

  const handlePlayPause = async () => {
    setIsLoading(true);
    const action = playerState.playing ? 'pause' : 'play';
    try {
      await fetch(`http://localhost:3001/api/player/${action}`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('Error:', error);
    }
    setTimeout(() => setIsLoading(false), 500);
  };

  const handleSkip = async (direction) => {
    setIsLoading(true);
    try {
      await fetch(`http://localhost:3001/api/player/${direction}`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('Error:', error);
    }
    setTimeout(() => setIsLoading(false), 500);
  };

  return (
    <div className="flex flex-col items-center p-8 max-w-md mx-auto bg-white rounded-lg shadow-lg">
      {/* Album Art */}
      <div className="w-64 h-64 mb-6 rounded-lg overflow-hidden shadow-lg">
        {playerState.currentTrack.albumArt ? (
          <img 
            src={playerState.currentTrack.albumArt} 
            alt="Album artwork" 
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full bg-gray-200 flex items-center justify-center">
            <span className="text-gray-400">Pas de couverture</span>
          </div>
        )}
      </div>

      {/* Track Info */}
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

      {/* Controls */}
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