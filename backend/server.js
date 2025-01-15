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

let currentUserId = null;


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

// Fonction pour lire tous les tokens Spotify
async function getAllSpotifyTokens() {
    try {
        const tokensFile = await fs.readFile(tokensPath, 'utf8');
        return JSON.parse(tokensFile);
    } catch (error) {
        console.error('Erreur lecture tous les tokens:', error);
        return {};
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
        console.log('=== Début contrôle playback ===');
        console.log('Commande:', command);

        let tokens = await getAllSpotifyTokens();
        console.log('Utilisateur actif:', currentUserId);
        console.log('Tokens disponibles pour les utilisateurs:', Object.keys(tokens));

        if (!currentUserId || !tokens[currentUserId]) {
            console.log('❌ Pas de token pour l\'utilisateur actif');
            throw new Error('Pas de token disponible pour l\'utilisateur actif');
        }

        let userTokens = tokens[currentUserId];
        console.log('Token trouvé pour l\'utilisateur actif');

        try {
            console.log('Tentative d\'envoi de la commande...');
            const result = await sendSpotifyCommand(command, userTokens.access_token);
            console.log('Commande exécutée avec succès');
            return result;
        } catch (error) {
            if (error.response?.status === 401) {
                console.log('Token expiré, tentative de rafraîchissement...');
                const newAccessToken = await refreshSpotifyToken(userTokens.refresh_token);

                console.log('Token rafraîchi avec succès');
                tokens[currentUserId].access_token = newAccessToken;
                await fs.writeFile(tokensPath, JSON.stringify(tokens));

                console.log('Nouvel essai avec le token rafraîchi');
                return await sendSpotifyCommand(command, newAccessToken);
            }
            throw error;
        }
    } catch (error) {
        console.error('❌ Erreur contrôle Spotify:', error);
        throw error;
    }
}
// Modifions aussi la fonction qui vérifie l'utilisateur actif
async function getCurrentSpotifyUser(accessToken) {
    try {
        console.log('Vérification utilisateur avec token:', accessToken.substring(0, 10) + '...');
        const response = await axios({
            method: 'get',
            url: 'https://api.spotify.com/v1/me/player',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
            }
        });

        console.log('Réponse API player:', response.status);
        if (response.status === 200 && response.data) {
            return { isActive: true, data: response.data };
        } else {
            return { isActive: false };
        }
    } catch (error) {
        console.log('Erreur vérification utilisateur:', error.response?.status);
        return { isActive: false };
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
app.post('/event', async (req, res) => {
    console.log('\n=== Nouvel événement ===');
    console.log('Type:', req.body.type);
    console.log('Données complètes:', JSON.stringify(req.body, null, 2));

    const event = req.body;

    // Vérifier l'utilisateur actif lors des événements importants
    if (['track_changed', 'playing', 'stopped', 'paused'].includes(event.type)) {
        try {
            console.log('Vérification de l\'utilisateur actif...');
            const tokens = await getAllSpotifyTokens();
            console.log('Tokens disponibles:', Object.keys(tokens));

            // Si nous n'avons pas d'utilisateur actif, utiliser le dernier utilisateur authentifié
            if (!currentUserId) {
                currentUserId = Object.keys(tokens)[Object.keys(tokens).length - 1];
                console.log('Utilisation du dernier utilisateur authentifié:', currentUserId);
            }

            // Tenter de vérifier si cet utilisateur est actif
            const currentUserTokens = tokens[currentUserId];
            if (currentUserTokens) {
                try {
                    const userPlayer = await getCurrentSpotifyUser(currentUserTokens.access_token);
                    console.log('Statut du player pour l\'utilisateur actuel:', userPlayer.isActive);

                    // Si le player n'est pas actif, essayer les autres utilisateurs
                    if (!userPlayer.isActive) {
                        for (const [userId, userTokens] of Object.entries(tokens)) {
                            if (userId !== currentUserId) {
                                const otherUserPlayer = await getCurrentSpotifyUser(userTokens.access_token);
                                if (otherUserPlayer.isActive) {
                                    currentUserId = userId;
                                    console.log('Nouvel utilisateur actif trouvé:', userId);
                                    break;
                                }
                            }
                        }
                    }
                } catch (error) {
                    console.log('Erreur vérification player:', error.message);
                }
            }

            console.log('Utilisateur actif final:', currentUserId);
        } catch (error) {
            console.error('Erreur vérification utilisateur:', error);
        }
    }

    // Traitement normal de l'événement
    switch (event.type) {
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
    broadcast({
        type: event.type,
        state: {
            ...currentState,
            activeUser: currentUserId
        }
    });
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
        // Utiliser le même système que pour les autres contrôles
        let tokens = await getAllSpotifyTokens();
        if (!currentUserId || !tokens[currentUserId]) {
            throw new Error('Pas de token disponible pour l\'utilisateur actif');
        }

        let userTokens = tokens[currentUserId];
        
        try {
            const response = await axios({
                method: 'PUT',
                url: 'https://api.spotify.com/v1/me/player/seek',
                headers: {
                    'Authorization': `Bearer ${userTokens.access_token}`,
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
                const newAccessToken = await refreshSpotifyToken(userTokens.refresh_token);
                
                // Mettre à jour le token dans le fichier
                tokens[currentUserId].access_token = newAccessToken;
                await fs.writeFile(tokensPath, JSON.stringify(tokens));
                
                // Réessayer avec le nouveau token
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
        console.error('Erreur seek:', error);
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