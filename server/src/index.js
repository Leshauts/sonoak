const express = require('express');
const cors = require('cors');
const WebSocket = require('ws');
const { router, initLibrespotHooks } = require('./routes/player');

const app = express();
app.use(cors());
app.use(express.json());

app.use('/api/player', router);

const server = app.listen(3001, () => {
  console.log('Server running on port 3001');
});

const wss = new WebSocket.Server({ server });

wss.on('connection', (ws) => {
  console.log('Client connected to WebSocket');
  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });
});

initLibrespotHooks(wss);