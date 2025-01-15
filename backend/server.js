// backend/server.js
const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const cors = require('cors');
const fs = require('fs').promises;
const axios = require('axios');
const path = require('path');

const app = express();
const server = http.createServer(app);

// Spotify API credentials
const CLIENT_ID = 'bbf81c2e8d794363bb13a23f10678d56';
const CLIENT_SECRET = 'e7a84bd477ec47dfaf63a1bd3fbdc9ce';

// Autoriser les requêtes de n'importe quelle origine
app.use(cors());
app.use(express.json());

// État global
let currentState = {
    isPlaying: false,
    currentTrack: null,
    position: 0,
    volume: 100
};

// Créer le serveur WebSocket
const wss = new WebSocket.Server({ server });

// Chemin vers le fichier des tokens
const tokensPath = path.join(__dirname, 'spotify_tokens.json');

// Fonction pour rafraîchir le token
async function refreshSpotifyToken(refreshToken) {
    try {
        const response = await axios({
            method: 'post',
            url: 'https://accounts.spotify.com/api/token',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': `Basic ${Buffer.from(CLIENT_ID + ':' + CLIENT_SECRET).toString('base64')}`
            },
            data: new URLSearchParams({
                grant_type: 'refresh_token',
                refresh_token: refreshToken
            })
        });

        return response.data.access_token;
    } catch (error) {
        console.error('Erreur refresh token:', error);
        throw error;
    }
}

// Fonction pour lire les tokens Spotify
async function getSpotifyTokens() {
    try {
        const tokensFile = await fs.readFile(tokensPath, 'utf8');
        const tokens = JSON.parse(tokensFile);
        const firstUser = Object.keys(tokens)[0];
        return tokens[firstUser];
    } catch (error) {
        console.error('Erreur lecture tokens:', error);
        return null;
    }
}

// Fonction pour envoyer les commandes à Spotify
async function sendSpotifyCommand(command, accessToken) {
    const baseUrl = 'https://api.spotify.com/v1/me/player';
    const headers = {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
    };

    let endpoint;
    let method = 'PUT';
    
    switch (command) {
        case 'play':
            endpoint = '/play';
            break;
        case 'pause':
            endpoint = '/pause';
            break;
        case 'next':
            endpoint = '/next';
            method = 'POST';
            break;
        case 'previous':
            endpoint = '/previous';
            method = 'POST';
            break;
        default:
            throw new Error('Commande invalide');
    }

    const response = await axios({
        method: method,
        url: baseUrl + endpoint,
        headers: headers
    });

    return response.status === 204;
}

// Fonction pour contrôler la lecture via l'API Spotify
async function controlSpotifyPlayback(command) {
    try {
        let tokens = await getSpotifyTokens();
        if (!tokens) throw new Error('Pas de tokens disponibles');

        try {
            // Première tentative avec le token actuel
            return await sendSpotifyCommand(command, tokens.access_token);
        } catch (error) {
            if (error.response?.status === 401) {
                // Token expiré, on rafraîchit
                console.log('Token expiré, rafraîchissement...');
                const newAccessToken = await refreshSpotifyToken(tokens.refresh_token);
                
                // Mettre à jour le token dans le fichier
                tokens.access_token = newAccessToken;
                const allTokens = JSON.parse(await fs.readFile(tokensPath, 'utf8'));
                const userId = Object.keys(allTokens)[0];
                await fs.writeFile(tokensPath, JSON.stringify({
                    [userId]: {
                        ...allTokens[userId],
                        access_token: newAccessToken
                    }
                }));
                
                // Réessayer avec le nouveau token
                return await sendSpotifyCommand(command, newAccessToken);
            }
            throw error;
        }
    } catch (error) {
        console.error('Erreur contrôle Spotify:', error);
        throw error;
    }
}

// Gérer les connexions WebSocket
wss.on('connection', (ws) => {
    console.log('Client WebSocket connecté');
    
    ws.send(JSON.stringify({
        type: 'initial_state',
        state: currentState
    }));
    
    ws.on('close', () => console.log('Client WebSocket déconnecté'));
});

// Fonction de broadcast
const broadcast = (data) => {
    wss.clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify(data));
        }
    });
};

// Route pour les événements
app.post('/event', (req, res) => {
    console.log('\n=== Nouvel événement ===');
    console.log('Type:', req.body.type);
    console.log('Données complètes:', JSON.stringify(req.body, null, 2));
    
    const event = req.body;
    
    switch(event.type) {
        case 'track_changed':
            console.log('Mise à jour des infos de la piste');
            currentState.currentTrack = {
                id: event.trackId,
                name: event.name,
                artists: event.artists?.split(',').filter(Boolean),
                album: event.album,
                duration: parseInt(event.duration_ms),
                coverUrl: event.coverUrl
            };
            console.log('Nouvel état:', JSON.stringify(currentState.currentTrack, null, 2));
            break;
            
        case 'playing':
            console.log('Mise à jour du statut de lecture');
            currentState.isPlaying = true;
            currentState.position = parseInt(event.position_ms);
            break;
            
        case 'paused':
        case 'stopped':
            console.log('Mise à jour du statut de pause/arrêt');
            currentState.isPlaying = false;
            currentState.position = parseInt(event.position_ms);
            break;
            
        case 'position_changed':
            currentState.position = parseInt(event.position_ms);
            break;
    }
    
    console.log('Broadcast de l\'état mis à jour');
    broadcast({ type: event.type, state: currentState });
    res.sendStatus(200);
});

// Routes pour le contrôle du lecteur
app.post('/player/control/:command', async (req, res) => {
    const { command } = req.params;
    console.log(`Commande reçue: ${command}`);
    
    try {
        await controlSpotifyPlayback(command);
        res.status(200).json({ success: true });
    } catch (error) {
        console.error('Erreur détaillée:', error.response?.data || error.message);
        res.status(500).json({ 
            error: 'Erreur serveur',
            details: error.response?.data || error.message 
        });
    }
});

// Route pour le seek
app.post('/player/seek', async (req, res) => {
    const { position_ms } = req.body;
    console.log(`Seek demandé à: ${position_ms}ms`);
    
    try {
        let tokens = await getSpotifyTokens();
        if (!tokens) throw new Error('Pas de tokens disponibles');

        try {
            const response = await axios({
                method: 'PUT',
                url: 'https://api.spotify.com/v1/me/player/seek',
                headers: {
                    'Authorization': `Bearer ${tokens.access_token}`,
                    'Content-Type': 'application/json'
                },
                params: {
                    position_ms: position_ms
                }
            });

            if (response.status === 204) {
                currentState.position = position_ms;
                broadcast({ 
                    type: 'position_changed', 
                    state: currentState 
                });
                res.status(200).json({ success: true });
            }
        } catch (error) {
            if (error.response?.status === 401) {
                // Token expiré, on rafraîchit
                console.log('Token expiré, rafraîchissement...');
                const newAccessToken = await refreshSpotifyToken(tokens.refresh_token);
                
                // Mettre à jour le token et réessayer
                const response = await axios({
                    method: 'PUT',
                    url: 'https://api.spotify.com/v1/me/player/seek',
                    headers: {
                        'Authorization': `Bearer ${newAccessToken}`,
                        'Content-Type': 'application/json'
                    },
                    params: {
                        position_ms: position_ms
                    }
                });

                if (response.status === 204) {
                    currentState.position = position_ms;
                    broadcast({ 
                        type: 'position_changed', 
                        state: currentState 
                    });
                    res.status(200).json({ success: true });
                }
            } else {
                throw error;
            }
        }
    } catch (error) {
        console.error('Erreur:', error);
        res.status(500).json({ error: 'Erreur serveur' });
    }
});

// Route de test
app.get('/status', (req, res) => {
    res.json({
        status: 'running',
        clients: wss.clients.size,
        currentState
    });
});

// Démarrer le serveur
const PORT = 8888;
server.listen(PORT, '0.0.0.0', () => {
    console.log(`Serveur démarré sur http://0.0.0.0:${PORT}`);
    console.log(`WebSocket disponible sur ws://0.0.0.0:${PORT}`);
});