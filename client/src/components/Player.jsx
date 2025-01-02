import { useState, useEffect } from 'react';

const Player = () => {
 const [playerState, setPlayerState] = useState({
   playing: false,
   currentTrack: {
     title: "No track playing",
     artist: "",
     album: ""
   },
   volume: 50
 });
 useEffect(() => {
    console.log('Component mounted');
    const ws = new WebSocket('ws://localhost:3001');
    
    ws.onmessage = (event) => {
      console.log('WS message received:', event.data);
      const data = JSON.parse(event.data);
      setPlayerState(prev => ({...prev, ...data}));
    };
  
    return () => ws.close();
  }, []);

 const handlePlayPause = async () => {
   try {
     const action = playerState.playing ? 'pause' : 'play';
     await fetch(`http://localhost:3001/api/player/${action}`, {
       method: 'POST'
     });
     setPlayerState(prev => ({...prev, playing: !prev.playing}));
   } catch (error) {
     console.error('Error toggling play/pause:', error);
   }
 };

 const handleSkip = async (direction) => {
   try {
     await fetch(`http://localhost:3001/api/player/${direction}`, {
       method: 'POST'
     });
   } catch (error) {
     console.error(`Error skipping ${direction}:`, error);
   }
 };

 const handleVolumeChange = async (e) => {
    const newVolume = parseInt(e.target.value);
    try {
      console.log('Sending volume change:', newVolume);
      const response = await fetch('http://localhost:3001/api/player/volume', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ volume: newVolume })
      });
      console.log('Volume response:', response);
      if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
      setPlayerState(prev => ({...prev, volume: newVolume}));
    } catch (error) {
      console.error('Volume error:', error);
    }
  };

 return (
   <div className="player">
     <div className="track-info">
       <h2>{playerState.currentTrack.title}</h2>
       <p>{playerState.currentTrack.artist}</p>
       <p>{playerState.currentTrack.album}</p>
     </div>
     <div className="controls">
       <button onClick={() => handleSkip('previous')}>Previous</button>
       <button onClick={handlePlayPause}>
         {playerState.playing ? 'Pause' : 'Play'}
       </button>
       <button onClick={() => handleSkip('next')}>Next</button>
     </div>
     <input 
       type="range" 
       min="0" 
       max="100" 
       value={playerState.volume} 
       onChange={handleVolumeChange}
     />
   </div>
 );
};

export default Player;