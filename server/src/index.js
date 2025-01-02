// server/src/index.js
const express = require('express');
const cors = require('cors');
const WebSocket = require('ws');
const app = express();

app.use(cors());
app.use(express.json());

const server = app.listen(3001, () => console.log('Server on 3001'));
const wss = new WebSocket.Server({ server });

const { router, initLibrespotHooks } = require('./routes/player');
app.use('/api/player', router);

initLibrespotHooks(wss);