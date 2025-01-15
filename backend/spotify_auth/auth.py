import json
import os
from flask import Flask, request, redirect, session, jsonify
from flask_cors import CORS
import requests
from urllib.parse import urlencode

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = os.urandom(24)

# Spotify API credentials
CLIENT_ID = 'bbf81c2e8d794363bb13a23f10678d56'
CLIENT_SECRET = 'e7a84bd477ec47dfaf63a1bd3fbdc9ce'
REDIRECT_URI = 'http://localhost:3333/callback'

# Spotify API URLs
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
TOKENS_FILE = 'spotify_tokens.json'

def load_tokens():
    try:
        with open(TOKENS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_tokens(tokens):
    with open(TOKENS_FILE, 'w') as f:
        json.dump(tokens, f)

@app.route('/api/auth/status')
def auth_status():
    tokens = load_tokens()
    return jsonify({
        'authenticated': len(tokens) > 0,
        'users': list(tokens.keys())
    })

@app.route('/api/auth/current-user')
def get_current_user():
    tokens = load_tokens()
    if not tokens:
        return jsonify({'error': 'No authenticated users'}), 401
    
    # Pour l'instant, on retourne le premier utilisateur trouvé
    user_id = next(iter(tokens))
    access_token = get_fresh_access_token(user_id)
    
    # Get user info from Spotify
    response = requests.get(
        'https://api.spotify.com/v1/me',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    if response.status_code != 200:
        return jsonify({'error': 'Failed to get user info'}), 500
        
    return jsonify(response.json())

@app.route('/')
def index():
    return '''
        <h1>Spotify Authentication</h1>
        <a href="/login">Login with Spotify</a>
    '''

@app.route('/login')
def login():
    scope = 'user-read-playback-state user-modify-playback-state user-read-currently-playing'
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }
    return redirect(f'{AUTH_URL}?{urlencode(params)}')

@app.route('/callback')
def callback():
    error = request.args.get('error')
    code = request.args.get('code')
    
    if error:
        return f"Error: {error}"
    
    response = requests.post(
        TOKEN_URL,
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }
    )
    
    if response.status_code != 200:
        return 'Error getting token'
    
    tokens = response.json()
    
    user_response = requests.get(
        'https://api.spotify.com/v1/me',
        headers={
            'Authorization': f"Bearer {tokens['access_token']}"
        }
    )
    
    if user_response.status_code != 200:
        return 'Error getting user info'
    
    user_info = user_response.json()
    user_id = user_info['id']
    
    all_tokens = load_tokens()
    all_tokens[user_id] = {
        'refresh_token': tokens['refresh_token'],
        'access_token': tokens['access_token'],
        'expires_in': tokens['expires_in']
    }
    save_tokens(all_tokens)
    
    return f'''
        <h1>Success!</h1>
        <p>Authentication successful for user: {user_info['display_name']}</p>
        <p>You can close this window now.</p>
        <script>
            window.opener && window.opener.postMessage('spotify-auth-success', '*');
            window.close();
        </script>
    '''

def get_fresh_access_token(user_id):
    tokens = load_tokens()
    if user_id not in tokens:
        raise Exception(f"No refresh token stored for user {user_id}")
    
    refresh_token = tokens[user_id]['refresh_token']
    
    response = requests.post(
        TOKEN_URL,
        data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }
    )
    
    if response.status_code != 200:
        raise Exception("Error refreshing token")
    
    new_tokens = response.json()
    tokens[user_id]['access_token'] = new_tokens['access_token']
    tokens[user_id]['expires_in'] = new_tokens['expires_in']
    save_tokens(tokens)
    
    return new_tokens['access_token']

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3333)