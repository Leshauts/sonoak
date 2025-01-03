const express = require('express');
const cors = require('cors');
const { WebSocketServer } = require('ws');
const { router, initLibrespotHooks } = require('./routes/player');

const app = express();

app.use(cors());
app.use(express.json());

// Server setup
const server = app.listen(3001, () => {
  console.log('Server running on port 3001');
});

// WebSocket setup
const wss = new WebSocketServer({ server });

// Rendre le WebSocket accessible aux routes
app.set('wss', wss);

// Routes
app.use('/api/player', router);

wss.on('connection', (ws) => {
  console.log('Client connected to WebSocket');

  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });

  ws.on('close', () => {
    console.log('Client disconnected');
  });
});

// Initialize librespot hooks
initLibrespotHooks(wss);