import express from 'express';
import cors from 'cors';
import { WebSocketServer } from 'ws';
import fetch from 'node-fetch';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import audioManager from './services/audioManager.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const port = process.env.PORT || 3000;
const wsPort = 24880;
const LIBRESPOT_API = 'http://localhost:24879';

app.use(cors({
  origin: 'http://localhost:5173',
  methods: ['GET', 'POST', 'PUT']
}));

app.use(express.json());

// Initialize WebSocket server
const wss = new WebSocketServer({ port: wsPort });
wss.on('connection', (ws) => {
  console.log('Client connected to WebSocket.');
  ws.send(JSON.stringify({ message: 'Connection established.' }));
});

// Service management routes
app.post('/audio/:service/start', async (req, res) => {
  try {
    const service = req.params.service;
    switch (service) {
      case 'spotify':
        await audioManager.startSpotify();
        break;
      case 'bluetooth':
        await audioManager.startBluetooth();
        break;
      case 'macos':
        await audioManager.startMacos();
        break;
      default:
        return res.status(404).json({ error: 'Service not found' });
    }
    res.json({ message: `${service} service started` });
  } catch (error) {
    console.error(`Error starting ${req.params.service}:`, error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/audio/:service/stop', async (req, res) => {
  try {
    const service = req.params.service;
    switch (service) {
      case 'spotify':
        await audioManager.stopSpotify();
        break;
      case 'bluetooth':
        await audioManager.stopBluetooth();
        break;
      case 'macos':
        await audioManager.stopMacos();
        break;
      default:
        return res.status(404).json({ error: 'Service not found' });
    }
    res.json({ message: `${service} service stopped` });
  } catch (error) {
    console.error(`Error stopping ${req.params.service}:`, error);
    res.status(500).json({ error: error.message });
  }
});

// Spotify API routes
app.post('/audio/spotify/play', async (req, res) => {
  try {
    console.log('Sending play command to Spotify...');
    const response = await fetch(`${LIBRESPOT_API}/player/resume`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    res.json({ message: 'Playback started' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/audio/spotify/pause', async (req, res) => {
  try {
    const response = await fetch(`${LIBRESPOT_API}/player/pause`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    res.json({ message: 'Playback paused' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/audio/spotify/next', async (req, res) => {
  try {
    console.log('Sending next command to Spotify...');
    const response = await fetch(`${LIBRESPOT_API}/player/next`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{}'
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    res.json({ message: 'Skipped to next track' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/audio/spotify/prev', async (req, res) => {
  try {
    console.log('Sending previous command to Spotify...');
    const response = await fetch(`${LIBRESPOT_API}/player/prev`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{}'
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    res.json({ message: 'Returned to previous track' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/audio/spotify/seek', async (req, res) => {
  try {
    const { position } = req.body;
    const response = await fetch(`${LIBRESPOT_API}/player/seek`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ position: Math.floor(position) })
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    res.json({ message: 'Seeked to position' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/audio/spotify/status', async (req, res) => {
  try {
    if (!audioManager.services.spotify) {
      return res.json({
        paused: true,
        volume: 75,
        track: null
      });
    }
    
    const response = await fetch(`${LIBRESPOT_API}/player`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
  console.log(`WebSocket server running on port ${wsPort}`);
});