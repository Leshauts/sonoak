const express = require('express');
const axios = require('axios');
const querystring = require('querystring');
const crypto = require('crypto');
const cors = require('cors');
const http = require('http');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Constantes
const CLIENT_ID = "65b708073fc0480ea92a077233ca87bd";
const REDIRECT_PORT = 8888;
const REDIRECT_URI = `http://127.0.0.1:${REDIRECT_PORT}/login`;
const SCOPES = "streaming,user-read-email,user-read-private,playlist-read-private,playlist-read-collaborative,playlist-modify-public,playlist-modify-private,user-follow-modify,user-follow-read,user-library-read,user-library-modify,user-top-read,user-read-recently-played";

// Middleware pour vérifier le token
app.use((req, res, next) => {
    if (['/login'].includes(req.path)) {
        return next();
    }
    if (!accessToken) {
        return res.status(401).send('Access Token is missing. Please authenticate.');
    }
    next();
});

let accessToken = '';
let refreshToken = '';
let codeVerifier = '';

function generateCodeVerifier(length) {
    return crypto.randomBytes(length)
        .toString('base64')
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '')
        .slice(0, length);
}

function generateCodeChallenge(verifier) {
    const base64hash = crypto
        .createHash('sha256')
        .update(verifier)
        .digest('base64')
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');
    return base64hash;
}

app.get('/login', async (req, res) => {
    if (req.query.code) {
        try {
            const response = await axios.post('https://accounts.spotify.com/api/token', 
                querystring.stringify({
                    grant_type: 'authorization_code',
                    code: req.query.code,
                    redirect_uri: REDIRECT_URI,
                    client_id: CLIENT_ID,
                    code_verifier: codeVerifier,
                }), {
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                }
            );

            accessToken = response.data.access_token;
            refreshToken = response.data.refresh_token;

            console.log('Access Token:', accessToken);
            res.send('Authentication successful! You can close this window.');
        } catch (err) {
            console.error('Error during authentication:', err.response?.data || err.message);
            res.status(500).send('Error during authentication');
        }
    } else {
        codeVerifier = generateCodeVerifier(64);
        const codeChallenge = generateCodeChallenge(codeVerifier);

        const authURL = `https://accounts.spotify.com/authorize?${querystring.stringify({
            response_type: 'code',
            client_id: CLIENT_ID,
            scope: SCOPES,
            redirect_uri: REDIRECT_URI,
            code_challenge_method: 'S256',
            code_challenge: codeChallenge,
        })}`;

        res.redirect(authURL);
    }
});

async function refreshAccessToken() {
    if (refreshToken) {
        try {
            const response = await axios.post('https://accounts.spotify.com/api/token',
                querystring.stringify({
                    grant_type: 'refresh_token',
                    refresh_token: refreshToken,
                    client_id: CLIENT_ID,
                }), {
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                }
            );

            accessToken = response.data.access_token;
            if (response.data.refresh_token) {
                refreshToken = response.data.refresh_token;
            }
            console.log('Access Token refreshed');
        } catch (err) {
            console.error('Error refreshing token:', err.response?.data || err.message);
        }
    }
}

setInterval(refreshAccessToken, 50 * 60 * 1000);


// Helper function to make requests to Spotify's partner API
async function makePartnerApiRequest(sectionUri) {
    // Ajout des paramètres requis pour l'API GraphQL de Spotify
    const variables = {
        uri: sectionUri,
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone, // Timezone locale
        locale: "",
        platform: "web",
        sp_t: accessToken,  // Important! C'était l'élément manquant
        sectionItemsOffset: 0,
        sectionItemsLimit: 20
    };

    const extensions = {
        persistedQuery: {
            version: 1,
            sha256Hash: "eb3fba2d388cf4fc4d696b1757a58584e9538a3b515ea742e9cc9465807340be"
        }
    };

    try {
        const response = await axios.get('https://api-partner.spotify.com/pathfinder/v1/query', {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'app-platform': 'WebPlayer',
                'spotify-app-version': '1.2.0',
                'Origin': 'https://open.spotify.com',
                'Referer': 'https://open.spotify.com/',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            params: {
                operationName: 'homeSection',
                variables: JSON.stringify(variables),
                extensions: JSON.stringify(extensions)
            }
        });

        if (response.data.errors) {
            console.error('GraphQL Errors:', response.data.errors);
            throw new Error('GraphQL response contained errors');
        }

        return response.data;
    } catch (err) {
        console.error('Error making partner API request:', err.response?.data || err.message);
        if (err.response?.data?.errors) {
            console.error('GraphQL Errors:', err.response.data.errors);
        }
        throw err;
    }
}

// Ajoutez aussi cette fonction utilitaire pour traiter la réponse
async function makePartnerApiRequest(sectionUri) {
    const variables = {
        uri: sectionUri,
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        locale: "",
        platform: "web",
        sp_t: accessToken,
        sectionItemsOffset: 0,
        sectionItemsLimit: 20
    };

    const extensions = {
        persistedQuery: {
            version: 1,
            sha256Hash: "eb3fba2d388cf4fc4d696b1757a58584e9538a3b515ea742e9cc9465807340be"
        }
    };

    try {
        console.log('Making request with:', {
            uri: sectionUri,
            token: accessToken.substring(0, 10) + '...',
            variables: variables
        });

        const response = await axios.get('https://api-partner.spotify.com/pathfinder/v1/query', {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'app-platform': 'WebPlayer',
                'spotify-app-version': '1.2.0',
                'Origin': 'https://open.spotify.com',
                'Referer': 'https://open.spotify.com/',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            params: {
                operationName: 'homeSection',
                variables: JSON.stringify(variables),
                extensions: JSON.stringify(extensions)
            }
        });

        console.log('Raw Response:', JSON.stringify(response.data, null, 2));

        if (response.data.errors) {
            console.error('GraphQL Errors:', JSON.stringify(response.data.errors, null, 2));
            throw new Error(`GraphQL errors: ${JSON.stringify(response.data.errors)}`);
        }

        return response.data;
    } catch (err) {
        console.error('Full error:', err);
        console.error('Error response:', err.response?.data);
        console.error('Error config:', {
            url: err.config?.url,
            method: err.config?.method,
            headers: err.config?.headers,
            params: err.config?.params
        });
        throw err;
    }
}

// Function to process the response and extract relevant information
function processPartnerApiResponse(data) {
    try {
        const section = data.data.home.sections[0];
        const sectionItems = section.sectionItems.items;

        return {
            title: section.data.title.text,
            items: sectionItems.map(item => {
                const content = item.content.data;
                return {
                    id: content.uri.split(':').pop(),
                    name: content.name,
                    type: content.__typename.toLowerCase(),
                    images: content.images?.items.map(img => ({
                        url: img.sources[0].url
                    })) || [],
                    description: content.description,
                    owner: content.ownerV2?.data?.name
                };
            })
        };
    } catch (err) {
        console.error('Error processing partner API response:', err);
        throw err;
    }
}



// API Endpoints

app.get('/daily-mixes', async (req, res) => {
    try {
        console.log('Attempting to fetch daily mixes...');
        console.log('Current access token:', accessToken.substring(0, 10) + '...');
        
        const data = await makePartnerApiRequest('spotify:section:0JQ5DAUnp4wcj0bCb3wh3S');
        const processed = processPartnerApiResponse(data);
        
        console.log('Successfully processed response');
        res.json(processed);
    } catch (err) {
        console.error('Detailed error in /daily-mixes:', err);
        res.status(500).json({
            error: 'Error fetching daily mixes',
            details: err.message,
            stack: err.stack
        });
    }
});

app.get('/top-mixes', async (req, res) => {
    try {
        const data = await makePartnerApiRequest('spotify:section:0JQ5DAnM3wGh0gz1MXnu89');
        res.json(data);
    } catch (err) {
        res.status(500).send('Error fetching top mixes');
    }
});

app.get('/recommended-stations', async (req, res) => {
    try {
        const data = await makePartnerApiRequest('spotify:section:0JQ5DAnM3wGh0gz1MXnu3R');
        res.json(data);
    } catch (err) {
        res.status(500).send('Error fetching recommended stations');
    }
});

app.get('/uniquely-yours', async (req, res) => {
    try {
        const data = await makePartnerApiRequest('spotify:section:0JQ5DAqAJXkJGsa2DyEjKi');
        res.json(data);
    } catch (err) {
        res.status(500).send('Error fetching uniquely yours');
    }
});

app.get('/best-of-artists', async (req, res) => {
    try {
        const data = await makePartnerApiRequest('spotify:section:0JQ5DAnM3wGh0gz1MXnu3n');
        res.json(data);
    } catch (err) {
        res.status(500).send('Error fetching best of artists');
    }
});

app.get('/shows-for-you', async (req, res) => {
    try {
        const data = await makePartnerApiRequest('spotify:section:0JQ5DAnM3wGh0gz1MXnu3N');
        res.json(data);
    } catch (err) {
        res.status(500).send('Error fetching shows for you');
    }
});

app.get('/shows-you-might-like', async (req, res) => {
    try {
        const data = await makePartnerApiRequest('spotify:section:0JQ5DAnM3wGh0gz1MXnu3P');
        res.json(data);
    } catch (err) {
        res.status(500).send('Error fetching shows you might like');
    }
});

/// API SPOTFIY : 

app.get('/user-profile', async (req, res) => {
    try {
        const response = await axios.get('https://api.spotify.com/v1/me', {
            headers: { Authorization: `Bearer ${accessToken}` },
        });
        res.json(response.data);
    } catch (err) {
        console.error('Error fetching user profile:', err.response?.data || err.message);
        res.status(500).send('Error fetching user profile');
    }
});

app.get('/user-playlists', async (req, res) => {
    try {
        const response = await axios.get('https://api.spotify.com/v1/me/playlists', {
            headers: { Authorization: `Bearer ${accessToken}` },
        });
        res.json(response.data);
    } catch (err) {
        console.error('Error fetching user playlists:', err.response?.data || err.message);
        res.status(500).send('Error fetching user playlists');
    }
});

app.get('/user-saved-tracks', async (req, res) => {
    try {
        const response = await axios.get('https://api.spotify.com/v1/me/tracks', {
            headers: { Authorization: `Bearer ${accessToken}` },
        });
        res.json(response.data);
    } catch (err) {
        console.error('Error fetching saved tracks:', err.response?.data || err.message);
        res.status(500).send('Error fetching saved tracks');
    }
});

app.get('/user-saved-episodes', async (req, res) => {
    try {
        const response = await axios.get('https://api.spotify.com/v1/me/episodes', {
            headers: { Authorization: `Bearer ${accessToken}` },
        });
        res.json(response.data);
    } catch (err) {
        console.error('Error fetching saved episodes:', err.response?.data || err.message);
        res.status(500).send('Error fetching saved episodes');
    }
});

app.get('/user-top-tracks', async (req, res) => {
    try {
        const response = await axios.get('https://api.spotify.com/v1/me/top/tracks', {
            headers: { Authorization: `Bearer ${accessToken}` },
        });
        res.json(response.data);
    } catch (err) {
        console.error('Error fetching top tracks:', err.response?.data || err.message);
        res.status(500).send('Error fetching top tracks');
    }
});

app.get('/user-top-artists', async (req, res) => {
    try {
        const response = await axios.get('https://api.spotify.com/v1/me/top/artists', {
            headers: { Authorization: `Bearer ${accessToken}` },
        });
        res.json(response.data);
    } catch (err) {
        console.error('Error fetching top artists:', err.response?.data || err.message);
        res.status(500).send('Error fetching top artists');
    }
});



app.get('/recommendations', async (req, res) => {
    const { seed_artists, seed_tracks, seed_genres, limit, market } = req.query;

    if (!seed_artists && !seed_tracks && !seed_genres) {
        return res.status(400).send('You must provide at least one of seed_artists, seed_tracks, or seed_genres.');
    }

    try {
        const response = await axios.get('https://api.spotify.com/v1/recommendations', {
            headers: { Authorization: `Bearer ${accessToken}` },
            params: {
                seed_artists,
                seed_tracks,
                seed_genres,
                limit: limit || 20,
                market,
            },
        });

        res.json(response.data);
    } catch (err) {
        console.error('Error fetching recommendations:', err.response?.data || err.message);
        res.status(500).send('Error fetching recommendations');
    }
});


app.get('/search', async (req, res) => {
    const query = req.query.q; // Ex: "Daft Punk"
    const type = req.query.type; // Ex: "track,artist,album"

    try {
        const response = await axios.get('https://api.spotify.com/v1/search', {
            headers: { Authorization: `Bearer ${accessToken}` },
            params: { q: query, type },
        });
        res.json(response.data);
    } catch (err) {
        console.error('Error searching:', err.response?.data || err.message);
        res.status(500).send('Error searching');
    }
});

// Start server
console.log('Starting server...');
app.listen(REDIRECT_PORT, '127.0.0.1', () => {
    console.log(`Server running on http://127.0.0.1:${REDIRECT_PORT}`);
}).on('error', (err) => {
    console.error('Error starting server:', err);
});