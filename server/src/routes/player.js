const express = require('express');
const { exec } = require('child_process');
const fs = require('fs');
const router = express.Router();

let playerState = {
  playing: false,
  currentTrack: {
    title: "No track playing",
    artist: "",
    albumArt: ""
  },
  volume: 50,
  lastUpdate: Date.now()
};

let pendingUpdate = null;
let updateTimeoutId = null;
const UPDATE_DELAY = 250;

// Ajout de la nouvelle fonction getAlbumArtUrl ici
async function getAlbumArtUrl() {
  try {
    const result = await new Promise((resolve, reject) => {
      exec('osascript -e \'tell application "Spotify" to get artwork url of current track\'', 
        (error, stdout) => {
          if (error) {
            reject(error);
            return;
          }
          resolve(stdout.trim());
        });
    });
    
    console.log('Got artwork URL:', result);
    return result;
  } catch (error) {
    console.error('Error getting artwork URL:', error);
    return null;
  }
}

function isCompleteTrackData(track) {
  return track.title && track.artist && track.albumArt;
}

function broadcastStateUpdate(wss) {
  if (!wss) return;
  
  const stateToSend = {
    type: 'state_update',
    playing: playerState.playing,
    currentTrack: { ...playerState.currentTrack },
    volume: playerState.volume,
    lastUpdate: playerState.lastUpdate
  };

  console.log('Broadcasting state:', {
    title: stateToSend.currentTrack.title,
    hasArt: !!stateToSend.currentTrack.albumArt,
    artUrl: stateToSend.currentTrack.albumArt
  });

  wss.clients.forEach(client => {
    client.send(JSON.stringify(stateToSend));
  });
}

function processStateUpdate(newData, wss) {
  console.log('Processing state update:', {
    title: newData.currentTrack?.title,
    hasArt: !!newData.currentTrack?.albumArt
  });

  if (updateTimeoutId) {
    clearTimeout(updateTimeoutId);
  }

  pendingUpdate = pendingUpdate || { ...playerState };
  pendingUpdate = {
    ...pendingUpdate,
    playing: newData.playing !== undefined ? newData.playing : pendingUpdate.playing,
    currentTrack: {
      title: newData.currentTrack?.title || pendingUpdate.currentTrack.title,
      artist: newData.currentTrack?.artist || pendingUpdate.currentTrack.artist,
      albumArt: newData.currentTrack?.albumArt || pendingUpdate.currentTrack.albumArt
    },
    volume: newData.volume || pendingUpdate.volume,
    lastUpdate: Date.now()
  };

  updateTimeoutId = setTimeout(() => {
    if (pendingUpdate && isCompleteTrackData(pendingUpdate.currentTrack)) {
      playerState = { ...pendingUpdate };
      broadcastStateUpdate(wss);
      pendingUpdate = null;
    } else {
      console.log('Update skipped - incomplete data:', {
        hasTitle: !!pendingUpdate?.currentTrack.title,
        hasArtist: !!pendingUpdate?.currentTrack.artist,
        hasArt: !!pendingUpdate?.currentTrack.albumArt
      });
    }
  }, UPDATE_DELAY);
}


function initLibrespotHooks(wss) {
  console.log('Initializing librespot hooks...');
  
  const logFile = `${process.cwd()}/spotify-event.log`;
  console.log('Watching log file:', logFile);

  // Modification du setInterval pour inclure l'artwork
  setInterval(() => {
    exec('osascript -e \'tell application "Spotify" to get {player state, name of current track, artist of current track}\'', 
      async (error, stdout) => {
        if (error) {
          console.error('Error polling Spotify:', error);
          return;
        }
  
        const [state, name, artist] = stdout.trim().split(', ');
        const albumArt = await getAlbumArtUrl();
  
        processStateUpdate({
          playing: state === 'playing',
          currentTrack: {
            title: name,
            artist: artist,
            albumArt: albumArt || playerState.currentTrack.albumArt
          }
        }, wss);
      });
  }, 1000);

  fs.watchFile(logFile, { interval: 100 }, async (curr, prev) => {
    try {
      const data = fs.readFileSync(logFile, 'utf8');
      const lastLine = data.trim().split('\n').pop();
      
      const [event, trackId, name, artist, album, albumArt] = lastLine.split(' | ').map(s => s.trim());
      
      console.log('Event from log file:', {
        event,
        trackId,
        name,
        artist,
        album,
        hasArt: !!albumArt
      });

      if (!name || !artist || !album) {
        console.log('Incomplete track data from log');
        return;
      }

      processStateUpdate({
        playing: event === 'playing' ? true : (event === 'paused' ? false : playerState.playing),
        currentTrack: {
          title: name,
          artist: artist,
          album: album,
          albumArt: albumArt
        }
      }, wss);
      
    } catch (error) {
      console.error('Error processing log:', error);
    }
  });
}

// Routes
router.get('/current-track', (req, res) => {
  res.json(playerState);
});

router.post('/play', (req, res) => {
  exec('osascript -e \'tell application "Spotify" to play\'', (error) => {
    if (error) {
      console.error('Error sending play command:', error);
      res.status(500).json({ error: 'Failed to play' });
      return;
    }
    processStateUpdate({
      playing: true,
      currentTrack: playerState.currentTrack
    }, req.app.get('wss'));
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
    processStateUpdate({
      playing: false,
      currentTrack: playerState.currentTrack
    }, req.app.get('wss'));
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
    broadcastStateUpdate();
  });
});

module.exports = { 
  router: router,  // Exporter explicitement le routeur
  initLibrespotHooks 
};