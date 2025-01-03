const express = require('express');
const { exec } = require('child_process');
const fs = require('fs');
const router = express.Router();

let playerState = {
  playing: false,
  currentTrack: {
    title: "No track playing",
    artist: "",
    album: "",
    albumArt: ""  // Ajout de albumArt ici
  },
  volume: 50
};

function initLibrespotHooks(wss) {
  console.log('Initializing librespot hooks...');
  
  const logFile = `${process.cwd()}/spotify-event.log`;
  console.log('Watching log file:', logFile);

  let currentTrackData = null;

  fs.watchFile(logFile, (curr, prev) => {
    try {
      const data = fs.readFileSync(logFile, 'utf8');
      const lastLine = data.trim().split('\n').pop();
      console.log('New event detected:', lastLine);
  
      const [event, trackId, name, artist, album, albumArt] = lastLine.split(' | ').map(s => s.trim());
      console.log('Parsed event data:', { event, trackId, name, artist, album, albumArt });
  
      if (event === 'track_changed') {
        playerState.currentTrack = {
          title: name || "Unknown",
          artist: artist || "Unknown",
          album: album || "Unknown",
          albumArt: albumArt || ""
        };
        playerState.playing = true;
      } else if (event === 'playing') {
        playerState.playing = true;
        if (name && artist) {
          playerState.currentTrack = {
            title: name,
            artist: artist,
            album: album,
            albumArt: albumArt || playerState.currentTrack.albumArt
          };
        }
      } else if (event === 'paused') {
        playerState.playing = false;
      }
  
      console.log('Updated player state:', playerState);
  
      wss.clients.forEach(client => {
        client.send(JSON.stringify({
          type: event,
          ...playerState
        }));
      });
    } catch (error) {
      console.error('Error processing log:', error);
    }
  });
}

router.get('/current-track', (req, res) => {
  res.json(playerState);
});

// Au lieu d'utiliser les signaux, utilisez les commandes Spotify Connect
router.post('/play', (req, res) => {
  // Simule un clic "play" sur Spotify Connect
  exec('osascript -e \'tell application "Spotify" to play\'', (error) => {
    if (error) {
      console.error('Error sending play command:', error);
      res.status(500).json({ error: 'Failed to play' });
      return;
    }
    playerState.playing = true;
    res.json({ status: 'success' });
  });
});

router.post('/pause', (req, res) => {
  exec('osascript -e \'tell application "Spotify" to pause\'', (error) => {
    if (error) {
      console.error('Error sending pause command:', error);
      res.status(500).json({ error: 'Failed to pause' });
      return;
    }
    playerState.playing = false;
    res.json({ status: 'success' });
  });
});

router.post('/next', (req, res) => {
  exec('osascript -e \'tell application "Spotify" to next track\'', (error) => {
    if (error) {
      console.error('Error sending next command:', error);
      res.status(500).json({ error: 'Failed to skip' });
      return;
    }
    res.json({ status: 'success' });
  });
});

router.post('/previous', (req, res) => {
  exec('osascript -e \'tell application "Spotify" to previous track\'', (error) => {
    if (error) {
      console.error('Error sending previous command:', error);
      res.status(500).json({ error: 'Failed to go previous' });
      return;
    }
    res.json({ status: 'success' });
  });
});

router.post('/volume', (req, res) => {
  const { volume } = req.body;
  exec(`osascript -e 'tell application "Spotify" to set sound volume to ${volume}'`, (error) => {
    if (error) {
      console.error('Error setting volume:', error);
      res.status(500).json({ error: 'Failed to set volume' });
      return;
    }
    playerState.volume = volume;
    res.json({ status: 'success', volume });
  });
});

module.exports = { router, initLibrespotHooks };