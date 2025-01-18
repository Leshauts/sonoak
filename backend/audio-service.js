const { exec } = require('child_process');
const express = require('express');
const cors = require('cors');
const WebSocket = require('ws');
const net = require('net');

const app = express();
const port = 3000;
const wsPort = 24879;

// CORS configuration
app.use(cors({
  origin: 'http://localhost:5173', // Frontend URL
  methods: ['GET', 'POST'],
}));
app.use(express.json());

// Check if port is in use
const portInUse = (port) => {
  return new Promise((resolve) => {
    const tester = net.createServer()
      .once('error', (err) => {
        if (err.code === 'EADDRINUSE') resolve(true);
        else resolve(false);
      })
      .once('listening', () => tester.once('close', () => resolve(false)).close())
      .listen(port);
  });
};

// Initialize WebSocket server
(async () => {
  if (await portInUse(wsPort)) {
    console.error(`Port ${wsPort} is already in use.`);
    process.exit(1);
  }

  const wss = new WebSocket.Server({ port: wsPort });
  wss.on('connection', (ws) => {
    console.log('Client connected to WebSocket.');

    ws.send(JSON.stringify({ message: 'Connexion établie.' }));

    ws.on('message', (message) => {
      try {
        const data = JSON.parse(message);
        console.log('Message reçu:', data);
      } catch (err) {
        console.error('Erreur de parsing du message WebSocket :', err);
      }
    });

    ws.on('close', () => {
      console.log('Client déconnecté du WebSocket.');
    });
  });

  console.log(`WebSocket server running on port ${wsPort}`);
})();

// Command definitions
const commands = {
  spotify: {
    start: './go-librespot',
    stop: 'pkill go-librespot',
  },
  bluetooth: {
    start: `
      sudo rfkill unblock bluetooth &&
      sudo systemctl start bluetooth &&
      pulseaudio --start &&
      bluetoothctl << EOF
      power on
      discoverable on
      pairable on
      agent NoInputNoOutput
      default-agent
      EOF`,
    stop: `
      sudo systemctl stop bluetooth &&
      pulseaudio --kill &&
      sudo rfkill block bluetooth`,
  },
  macos: {
    start: 'snapclient -h 192.168.1.173',
    stop: 'pkill snapclient',
  },
};

// Execute a command
function executeCommand(command, res) {
  exec(command, (error, stdout, stderr) => {
    if (error) {
      console.error(`Error: ${stderr}`);
      res.status(500).send(stderr);
      return;
    }
    res.send(stdout || 'Command executed successfully.');
  });
}

// Routes for audio services
app.post('/audio/:service/start', (req, res) => {
  const service = req.params.service;
  if (commands[service]) {
    executeCommand(commands[service].start, res);
  } else {
    res.status(404).send('Service not found.');
  }
});

app.post('/audio/:service/stop', (req, res) => {
  const service = req.params.service;
  if (commands[service]) {
    executeCommand(commands[service].stop, res);
  } else {
    res.status(404).send('Service not found.');
  }
});

app.get('/audio/spotify/status', (req, res) => {
  res.send({
    paused: false,
    volume: 75,
    track: {
      name: 'Example Track',
      artist_names: ['Artist 1', 'Artist 2'],
      album_cover_url: '/path/to/cover.jpg',
      position: 120,
      duration: 300,
    },
  });
});

// Start the Express server
app.listen(port, () => {
  console.log(`Backend server running on http://localhost:${port}`);
});