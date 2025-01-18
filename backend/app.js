// backend/app.js
const express = require('express');
const cors = require('cors');
const audioManager = require('./services/audioManager');

const app = express();

// Configurer CORS pour autoriser les requêtes depuis votre frontend Vue.js
app.use(cors({
  origin: 'http://localhost:5173' // L'URL de votre frontend Vue
}));

app.use(express.json());

// Routes pour Spotify
app.post('/audio/spotify/start', async (req, res) => {
  try {
    await audioManager.startSpotify();
    res.json({ message: 'Spotify service started' });
  } catch (error) {
    console.error('Error starting Spotify:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/audio/spotify/stop', async (req, res) => {
  try {
    await audioManager.stopSpotify();
    res.json({ message: 'Spotify service stopped' });
  } catch (error) {
    console.error('Error stopping Spotify:', error);
    res.status(500).json({ error: error.message });
  }
});

// Routes pour Bluetooth
app.post('/audio/bluetooth/start', async (req, res) => {
  try {
    await audioManager.startBluetooth();
    res.json({ message: 'Bluetooth service started' });
  } catch (error) {
    console.error('Error starting Bluetooth:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/audio/bluetooth/stop', async (req, res) => {
  try {
    await audioManager.stopBluetooth();
    res.json({ message: 'Bluetooth service stopped' });
  } catch (error) {
    console.error('Error stopping Bluetooth:', error);
    res.status(500).json({ error: error.message });
  }
});

// Routes pour MacOS
app.post('/audio/macos/start', async (req, res) => {
  try {
    await audioManager.startMacos();
    res.json({ message: 'MacOS service started' });
  } catch (error) {
    console.error('Error starting MacOS:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/audio/macos/stop', async (req, res) => {
  try {
    await audioManager.stopMacos();
    res.json({ message: 'MacOS service stopped' });
  } catch (error) {
    console.error('Error stopping MacOS:', error);
    res.status(500).json({ error: error.message });
  }
});

// Route pour vérifier l'état de Spotify (utilisée par le store Spotify)
app.get('/audio/spotify/status', async (req, res) => {
  try {
    const status = await audioManager.getSpotifyStatus();
    res.json(status);
  } catch (error) {
    console.error('Error getting Spotify status:', error);
    res.status(500).json({ error: error.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});