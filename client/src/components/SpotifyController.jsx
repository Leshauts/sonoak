import React, { useState, useEffect, useCallback } from 'react';
import './SpotifyController.css';
import { useNavigate } from 'react-router-dom';
import PlayIcon from '../icons/play.svg';
import PauseIcon from '../icons/pause.svg';
import NextIcon from '../icons/next.svg';
import PreviousIcon from '../icons/previous.svg';
import DevicesIcon from '../icons/devices.svg';
import LibraryIcon from '../icons/library.svg';

// Icons components
// const PlayIcon = () => (
//   <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" className="control-icon">
//     <rect width="256" height="256" fill="none"/>
//     <path d="M240,128a15.74,15.74,0,0,1-7.6,13.51L88.32,229.65a16,16,0,0,1-16.2.3A15.86,15.86,0,0,1,64,216.13V39.87a15.86,15.86,0,0,1,8.12-13.82,16,16,0,0,1,16.2.3L232.4,114.49A15.74,15.74,0,0,1,240,128Z" fill="currentColor"/>
//   </svg>
// );

// const PauseIcon = () => (
//   <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" className="control-icon">
//     <rect width="256" height="256" fill="none"/>
//     <path d="M216,48V208a16,16,0,0,1-16,16H160a16,16,0,0,1-16-16V48a16,16,0,0,1,16-16h40A16,16,0,0,1,216,48ZM96,32H56A16,16,0,0,0,40,48V208a16,16,0,0,0,16,16H96a16,16,0,0,0,16-16V48A16,16,0,0,0,96,32Z" fill="currentColor"/>
//   </svg>
// );

// const NextIcon = () => (
//   <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
//     <path d="M5 15.868V8.132c0-.504.596-.804 1.041-.525l6.16 3.868c.398.25.398.8 0 1.05l-6.16 3.868c-.445.28-1.041-.021-1.041-.525Z" fill="currentColor"/>
//     <path d="M12.5 15.868V8.132c0-.504.596-.804 1.041-.525l6.16 3.868c.398.25.398.8 0 1.05l-6.16 3.868c-.445.28-1.041-.021-1.041-.525Z" fill="currentColor"/>
//   </svg>
// );

// const PreviousIcon = () => (
//   <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
//     <path d="M19 8.132v7.736c0 .504-.596.804-1.041.525l-6.16-3.868a.611.611 0 0 1 0-1.05l6.16-3.868c.445-.28 1.041.021 1.041.525Z" fill="currentColor"/>
//     <path d="M11.5 8.132v7.736c0 .504-.596.804-1.041.525l-6.16-3.868a.611.611 0 0 1 0-1.05l6.16-3.868c.445-.28 1.041.021 1.041.525Z" fill="currentColor"/>
//   </svg>
// );

// const AudioSourceIcon = () => (
//   <svg width="32" height="32" fill="none" xmlns="http://www.w3.org/2000/svg" className="control-icon">
//     <path fillRule="evenodd" clipRule="evenodd" d="M13 7a3 3 0 0 1 3-3h9a3 3 0 0 1 3 3v18a3 3 0 0 1-3 3h-9a3 3 0 0 1-3-3V7Zm3-1a1 1 0 0 0-1 1v18a1 1 0 0 0 1 1h9a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1h-9Z" fill="currentColor"/>
//     <path d="M24 19.5a3.5 3.5 0 1 1-7 0 3.5 3.5 0 0 1 7 0ZM11 20c0 .552-.46 1.016-.982.836a3.001 3.001 0 0 1 0-5.672c.522-.18.982.284.982.836v4ZM22 11.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z" fill="currentColor"/>
//     <path fillRule="evenodd" clipRule="evenodd" d="M7 9a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h3a1 1 0 1 1 0 2H7a3 3 0 0 1-3-3V10a3 3 0 0 1 3-3h3a1 1 0 1 1 0 2H7Z" fill="currentColor"/>
//   </svg>
// );

// const PlaylistIcon = () => (
//   <svg width="32" height="32" fill="none" xmlns="http://www.w3.org/2000/svg" className="control-icon">
//     <path fillRule="evenodd" clipRule="evenodd" d="M21 26a2 2 0 1 0 0-4 2 2 0 0 0 0 4Zm0 2a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z" fill="currentColor"/>
//     <path fillRule="evenodd" clipRule="evenodd" d="M23.385 15.212a1 1 0 0 1 .857-.182l4 1a1 1 0 1 1-.485 1.94L25 17.28V24a1 1 0 1 1-2 0v-8a1 1 0 0 1 .385-.788ZM3 8a1 1 0 0 1 1-1h24a1 1 0 1 1 0 2H4a1 1 0 0 1-1-1Zm0 8a1 1 0 0 1 1-1h16a1 1 0 1 1 0 2H4a1 1 0 0 1-1-1Zm0 8a1 1 0 0 1 1-1h10a1 1 0 1 1 0 2H4a1 1 0 0 1-1-1Z" fill="currentColor"/>
//   </svg>
// );

const SpotifyController = () => {
  const navigate = useNavigate();
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
  const [isSourcePanelOpen, setIsSourcePanelOpen] = useState(false);
  const [isPlaylistPanelOpen, setIsPlaylistPanelOpen] = useState(false);


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
        setPlayerState(prevState => {
          if (data.lastUpdate <= prevState.lastUpdate) {
            return prevState;
          }

          return {
            playing: isLoading ? prevState.playing : data.playing,
            currentTrack: {
              ...data.currentTrack,
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


  return (
    <>
      {isSourcePanelOpen && (
        <div className="overlay" onClick={() => setIsSourcePanelOpen(false)} />
      )}
      <div className="player-container">
        <div className="album-art">
          {playerState.currentTrack.albumArt ? (
            <img 
              src={playerState.currentTrack.albumArt} 
              alt="Album artwork" 
              onError={(e) => {
                e.target.src = '';
              }}
            />
          ) : (
            <div className="no-cover">
              <span>Pas de couverture</span>
            </div>
          )}
        </div>
 
        <div className="info-controls">
     <div className="top-buttons">
       <button 
         className="icon-btn" 
         onClick={() => navigate('/playlists')}
       >
         <img src={LibraryIcon} alt="Playlists" />
       </button>
       <button 
         className="icon-btn"
         onClick={() => setIsSourcePanelOpen(true)}
       >
         <img src={DevicesIcon} alt="Sources audio" />
       </button>
     </div>

     <div className="track-info">
       <h2>{playerState.currentTrack.title}</h2>
       <p>{playerState.currentTrack.artist}</p>
     </div>

     <div className="controls">
       <button 
         onClick={() => handleSkip('previous')}
         disabled={isLoading}
         className="control-btn"
       >
         <img src={PreviousIcon} alt="Previous" />
       </button>

       <button 
         onClick={handlePlayPause}
         disabled={isLoading}
         className="play-btn"
       >
         <img src={playerState.playing ? PauseIcon : PlayIcon} alt={playerState.playing ? "Pause" : "Play"} />
       </button>

       <button 
         onClick={() => handleSkip('next')}
         disabled={isLoading}
         className="control-btn"
       >
         <img src={NextIcon} alt="Next" />
       </button>
          </div>
        </div>
      </div>
 
      <div className={`source-panel ${isSourcePanelOpen ? 'open' : ''}`}>
        <h2>Sources audio</h2>
        <div className="source-list">
          <button className="source-item">Bluetooth</button>
          <button className="source-item">Snapcast</button>
          <button className="source-item">Jack 3.5mm</button>
        </div>
      </div>

      <div className={`source-panel ${isPlaylistPanelOpen ? 'open' : ''}`}>
        <h2>Playlists</h2>
        <div className="source-list">
          {/* Liste des playlists */}
        </div>
      </div>
    </>
  );
 };

export default SpotifyController;