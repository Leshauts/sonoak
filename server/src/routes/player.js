const express = require('express');
const { exec } = require('child_process');
const fs = require('fs');
const router = express.Router();

let playerState = {
  playing: false,
  currentTrack: {
    title: "No track playing",
    artist: "",
    album: ""
  },
  volume: 50
};

function initLibrespotHooks(wss) {
  const logFile = `${process.cwd()}/spotify-event.log`;

  // Surveiller le fichier de log
  fs.watchFile(logFile, (curr, prev) => {
    try {
      const data = fs.readFileSync(logFile, 'utf8');
      const lastLine = data.trim().split('\n').pop();
      console.log('Event log:', lastLine);
      
      const [event, trackId, name, artist, album] = lastLine.split(' | ');
      if (event === 'playing') {
        playerState.playing = true;
        playerState.currentTrack = { title: name, artist, album };
      } else if (event === 'paused') {
        playerState.playing = false;
      }

      wss.clients.forEach(client => {
        client.send(JSON.stringify(playerState));
      });
    } catch (error) {
      console.error('Error reading event log:', error);
    }
  });
}

router.get('/current-track', (req, res) => {
  res.json(playerState);
});

router.post('/play', (req, res) => {
  exec('killall -SIGUSR1 librespot', (error) => {
    if (error) {
      console.error('Error sending play signal:', error);
      res.status(500).json({ error: 'Failed to play' });
      return;
    }
    playerState.playing = true;
    res.json({ status: 'success' });
  });
});

router.post('/pause', (req, res) => {
  exec('killall -SIGUSR1 librespot', (error) => {
    if (error) {
      console.error('Error sending pause signal:', error);
      res.status(500).json({ error: 'Failed to pause' });
      return;
    }
    playerState.playing = false;
    res.json({ status: 'success' });
  });
});

router.post('/previous', (req, res) => {
  exec('killall -SIGUSR2 librespot', (error) => {
    if (error) {
      console.error('Error sending previous signal:', error);
      res.status(500).json({ error: 'Failed to go previous' });
      return;
    }
    res.json({ status: 'success' });
  });
});

router.post('/next', (req, res) => {
  exec('killall -SIGUSR2 librespot', (error) => {
    if (error) {
      console.error('Error sending next signal:', error);
      res.status(500).json({ error: 'Failed to go next' });
      return;
    }
    res.json({ status: 'success' });
  });
});

router.post('/volume', (req, res) => {
  const { volume } = req.body;
  // Implémenter le contrôle du volume via librespot
  playerState.volume = volume;
  res.json({ status: 'success', volume });
});

module.exports = { router, initLibrespotHooks };