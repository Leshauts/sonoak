// backend/routes/audio.js
const express = require('express');
const router = express.Router();
const audioManager = require('../services/audioManager');

// Endpoints pour Spotify
router.post('/spotify/start', async (req, res) => {
  try {
    await audioManager.startSpotify();
    res.status(200).json({ message: 'Spotify service started' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/spotify/stop', async (req, res) => {
  try {
    await audioManager.stopSpotify();
    res.status(200).json({ message: 'Spotify service stopped' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Route pour l'état de Spotify
router.get('/spotify/status', async (req, res) => {
  try {
    const status = await audioManager.getSpotifyStatus();
    res.status(200).json(status);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Endpoints pour Bluetooth
router.post('/bluetooth/start', async (req, res) => {
  try {
    await audioManager.startBluetooth();
    res.status(200).json({ message: 'Bluetooth service started' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/bluetooth/stop', async (req, res) => {
  try {
    await audioManager.stopBluetooth();
    res.status(200).json({ message: 'Bluetooth service stopped' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Endpoints pour MacOS
router.post('/macos/start', async (req, res) => {
  try {
    await audioManager.startMacos();
    res.status(200).json({ message: 'MacOS service started' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/macos/stop', async (req, res) => {
  try {
    await audioManager.stopMacos();
    res.status(200).json({ message: 'MacOS service stopped' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;