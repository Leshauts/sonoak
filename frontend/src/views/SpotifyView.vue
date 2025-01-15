# SpotifyView.vue
<template>
  <div class="spotify-view">
    <!-- Bouton de connexion si non authentifié -->
    <div v-if="!isAuthenticated" class="auth-container">
      <button @click="startAuth" class="auth-button">
        Se connecter avec Spotify
      </button>
    </div>

    <!-- Contenu existant si authentifié -->
    <template v-else>
      <!-- Status de connexion -->
      <div v-if="connectionStatus !== 'Connecté'" class="status-message">
        {{ connectionStatus }}
      </div>

      <!-- Bloc gauche - Image -->
      <div class="cover-image">
        <img v-if="currentTrack?.coverUrl" :src="currentTrack.coverUrl" :alt="currentTrack?.name" />
        <div v-else class="placeholder-cover"></div>
      </div>

      <!-- Bloc droite -->
      <div class="content">
        <!-- Bouton playlist -->
        <IconButton class="playlist-button-wrapper" @click="navigateToPlaylists">
          <PlaylistIcon color="var(--text)" variant="md" />
        </IconButton>

        <!-- Textes -->
        <div class="track-info">
          <h1>{{ currentTrack?.name || 'Aucune musique' }}</h1>
          <h2>{{ currentTrack?.artists?.join(', ') || 'Lancez la lecture sur Spotify' }}</h2>
        </div>

        <!-- Barre de lecture -->
        <div class="playback-bar">
          <span class="time">{{ formatTime(position) }}</span>
          <div class="progress-bar" @click="seekToPosition" ref="progressBar">
            <div class="progress" :style="{ width: `${(position / (currentTrack?.duration || 1)) * 100}%` }"></div>
          </div>
          <span class="time">{{ formatTime(currentTrack?.duration) }}</span>
        </div>

        <!-- Contrôleur Spotify -->
        <SpotifyController :isPlaying="isPlaying" @previous="onPrevious" @next="onNext" @toggle-play="onTogglePlay" />
      </div>
    </template>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import IconButton from '../components/IconButton.vue'
import PlaylistIcon from '../components/icons/PlaylistIcon.vue'
import SpotifyController from '../components/SpotifyController.vue'

const WS_URL = `ws://${window.location.hostname}:8888`
const AUTH_URL = 'http://localhost:3333'

export default {
  name: 'SpotifyView',

  components: {
    IconButton,
    PlaylistIcon,
    SpotifyController
  },

  setup() {
    const ws = ref(null)
    const connectionStatus = ref('Connexion...')
    const currentTrack = ref(null)
    const isPlaying = ref(false)
    const position = ref(0)
    const positionTimer = ref(null)
    const isAuthenticated = ref(false)

    const checkAuthStatus = async () => {
      try {
        console.log('Vérification du statut d\'authentification...')
        const response = await fetch(`${AUTH_URL}/api/auth/status`)
        const data = await response.json()
        console.log('Statut d\'authentification:', data)
        isAuthenticated.value = data.authenticated
      } catch (error) {
        console.error('Erreur vérification auth:', error)
        isAuthenticated.value = false  // Assurons-nous que c'est false en cas d'erreur
      }
    }

    const startAuth = () => {
      const width = 450
      const height = 730
      const left = (window.screen.width / 2) - (width / 2)
      const top = (window.screen.height / 2) - (height / 2)

      const authWindow = window.open(
        `${AUTH_URL}/login`,
        'Spotify Login',
        `width=${width},height=${height},left=${left},top=${top}`
      )

      window.addEventListener('message', async (event) => {
        if (event.data === 'spotify-auth-success') {
          await checkAuthStatus()
          if (authWindow) authWindow.close()
        }
      })
    }

    const connectWebSocket = () => {
      console.log('Tentative de connexion à', WS_URL)

      ws.value = new WebSocket(WS_URL)

      ws.value.onopen = () => {
        console.log('WebSocket connecté')
        connectionStatus.value = 'Connecté'
      }

      ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('WebSocket message reçu:', data);

    if (data.state) {
        console.log('Mise à jour du state:');
        if (data.state.currentTrack) {
            console.log('- Nouvelle piste:', data.state.currentTrack.name);
            currentTrack.value = data.state.currentTrack;
        }
        console.log('- Statut lecture:', data.state.isPlaying);
        isPlaying.value = data.state.isPlaying;
        
        // Mettre à jour la position uniquement si elle change significativement
        if (Math.abs(position.value - data.state.position) > 2000) {
            console.log('- Nouvelle position:', data.state.position);
            position.value = data.state.position;
        }
        startPositionTimer();
    }
};

      ws.value.onclose = () => {
        console.log('WebSocket déconnecté')
        connectionStatus.value = 'Déconnecté - Reconnexion...'
        stopPositionTimer()
        setTimeout(connectWebSocket, 2000)
      }

      ws.value.onerror = (error) => {
        console.error('WebSocket erreur:', error)
        connectionStatus.value = 'Erreur de connexion'
      }
    }

    const startPositionTimer = () => {
      if (positionTimer.value) {
        clearInterval(positionTimer.value)
      }

      if (isPlaying.value) {
        positionTimer.value = setInterval(() => {
          position.value += 1000
          if (currentTrack.value && position.value >= currentTrack.value.duration) {
            position.value = 0
            stopPositionTimer()
          }
        }, 1000)
      }
    }

    const stopPositionTimer = () => {
      if (positionTimer.value) {
        clearInterval(positionTimer.value)
        positionTimer.value = null
      }
    }

    const formatTime = (ms) => {
      if (!ms) return '0:00'
      const seconds = Math.floor((ms / 1000) % 60)
      const minutes = Math.floor((ms / 1000) / 60)
      return `${minutes}:${seconds.toString().padStart(2, '0')}`
    }

    const seekToPosition = async (event) => {
      if (!currentTrack.value) return;

      // Calculer la position en pourcentage où l'utilisateur a cliqué
      const rect = event.currentTarget.getBoundingClientRect();
      const clickPosition = event.clientX - rect.left;
      const percentage = clickPosition / rect.width;

      // Calculer la position en millisecondes
      const newPosition = Math.floor(currentTrack.value.duration * percentage);

      try {
        const response = await fetch(`http://${window.location.hostname}:8888/player/seek`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ position_ms: newPosition })
        });

        if (!response.ok) {
          throw new Error('Erreur lors du seek');
        }
      } catch (error) {
        console.error('Erreur seek:', error);
        connectionStatus.value = `Erreur: ${error.message}`;
      }
    };


    const sendPlayerCommand = async (command) => {
      try {
        const response = await fetch(`http://${window.location.hostname}:8888/player/control/${command}`, {
          method: 'POST'
        })

        if (!response.ok) {
          throw new Error(`Erreur commande ${command}`)
        }
      } catch (error) {
        console.error('Erreur commande:', error)
        connectionStatus.value = `Erreur: ${error.message}`
      }
    }

    const navigateToPlaylists = () => {
      // Implémentation de la navigation à venir
    }

    onMounted(async () => {
      console.log('Composant monté, vérification auth...')
      try {
        await checkAuthStatus()
        console.log('Statut auth:', isAuthenticated.value)
        if (isAuthenticated.value) {
          connectWebSocket()
        }
      } catch (error) {
        console.error('Erreur lors du montage:', error)
      }
    })

    onBeforeUnmount(() => {
      stopPositionTimer()
      if (ws.value) ws.value.close()
    })

    return {
      connectionStatus,
      currentTrack,
      isPlaying,
      position,
      isAuthenticated,
      formatTime,
      navigateToPlaylists,
      startAuth,
      seekToPosition,
      onTogglePlay: () => sendPlayerCommand(isPlaying.value ? 'pause' : 'play'),
      onPrevious: () => sendPlayerCommand('previous'),
      onNext: () => sendPlayerCommand('next')
    }
  }
}
</script>

<style scoped>
.spotify-view {
  width: 100%;
  height: 100svh;
  display: flex;
  gap: var(--spacing-06);
  padding: var(--spacing-04);
}

.status-message {
  position: fixed;
  top: var(--spacing-04);
  left: 50%;
  transform: translateX(-50%);
  padding: var(--spacing-02) var(--spacing-04);
  background: var(--background-strong);
  border-radius: var(--spacing-02);
  z-index: 1000;
}

.cover-image {
  height: 100%;
  aspect-ratio: 1/1;
}

.cover-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: var(--spacing-05);
}

.placeholder-cover {
  width: 100%;
  height: 100%;
  background: var(--background-strong);
  border-radius: var(--spacing-05);
}

.content {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
}

.playlist-button-wrapper {
  position: fixed;
  top: var(--spacing-06);
  right: var(--spacing-06);
}


.track-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: center;
}

.track-info h1 {
  margin-bottom: var(--spacing-04);
}

.track-info h2 {
  color: var(--text-light);
}


.playback-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-03);
  margin: var(--spacing-05)0;
}

.progress-bar {
  flex: 1;
  height: var(--spacing-01);
  background-color: var(--background-strong);
  border-radius: 2px;
}

.progress {
  height: 100%;
  background-color: var(--text);
  border-radius: 2px;
}

.auth-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.auth-button {
  padding: var(--spacing-03) var(--spacing-05);
  background-color: #1DB954;
  color: white;
  border: none;
  border-radius: var(--spacing-02);
  font-size: 1.2rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.auth-button:hover {
  background-color: #1ed760;
}



@media (max-width: 768px) {
  .spotify-view {
    flex-direction: column;
  }

  .cover-image {
    height: auto;
  }
}
</style>