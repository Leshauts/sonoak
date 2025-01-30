<template>
  <div class="spotify-view">
    <SpotifyStatus v-if="!isConnected" />
    
    <div v-if="isConnected" class="spotify-player">
      <!-- Bloc gauche - Image -->
      <div class="cover-image" v-if="playbackStatus">
        <img :src="playbackStatus.album_cover_url" :alt="playbackStatus.album_name" 
             v-if="playbackStatus.album_cover_url"/>
        <div class="placeholder-image" v-else></div>
      </div>

      <!-- Bloc droite -->
      <div class="content">
        <!-- Bouton playlist -->
        <IconButton class="playlist-button" @click="navigateToPlaylists">
          <PlaylistIcon color="var(--text-light)" variant="md" />
        </IconButton>

        <!-- Textes -->
        <div class="track-info" v-if="playbackStatus">
          <h1>{{ playbackStatus.track_name || 'Aucun titre' }}</h1>
          <h2>{{ formatArtists(playbackStatus.artist_names) }}</h2>
        </div>

        <!-- Barre de lecture -->
        <div class="playback-bar" v-if="playbackStatus">
          <span class="time">{{ formatTime(progressTime) }}</span>
          <div class="progress-bar">
            <div class="progress" :style="{ width: progressWidth }"></div>
          </div>
          <span class="time">{{ formatTime(playbackStatus.duration) }}</span>
        </div>

        <!-- Contrôleur Spotify -->
        <SpotifyController 
          :is-playing="playbackStatus?.is_playing"
          @play-pause="handlePlayPause"
          @next="handleNext"
          @previous="handlePrevious"
        />
      </div>
    </div>
  </div>
</template>

<script>
import SpotifyStatus from '@/components/SpotifyStatus.vue'
import IconButton from '../components/IconButton.vue'
import PlaylistIcon from '../components/icons/PlaylistIcon.vue'
import SpotifyController from '../components/SpotifyController.vue'

export default {
  name: 'SpotifyView',
  components: {
    SpotifyStatus,
    IconButton,
    PlaylistIcon,
    SpotifyController
  },
  data() {
    return {
      ws: null,
      playbackStatus: null,
      progressTime: 0,
      startTime: 0,
      progressInterval: null,
      isConnected: false
    }
  },
  computed: {
    progressWidth() {
      if (!this.playbackStatus?.duration) return '0%'
      const progress = Math.min(this.progressTime / this.playbackStatus.duration, 1)
      return `${progress * 100}%`
    }
  },
  methods: {
    initWebSocket() {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) return
      
      this.ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/spotify`)
      
      this.ws.onopen = () => {
        console.log('WebSocket connecté')
        this.requestInitialStatus()
      }

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        console.log('Message reçu:', data)

        if (data.type === 'spotify_status') {
          console.log('Mise à jour du statut de connexion:', data.status)
          this.isConnected = data.status.connected
          // Si connecté, demander le statut de lecture
          if (this.isConnected) {
            this.requestPlaybackStatus()
          }
        } 
        else if (data.type === 'playback_status' && data.status) {
          console.log('Mise à jour du statut de lecture:', data.status)
          // S'assurer que nous sommes toujours connectés
          if (this.isConnected) {
            this.playbackStatus = data.status
            this.startProgressTimer()
          }
        }
      }

      this.ws.onclose = () => {
        this.clearTimers()
        setTimeout(() => this.initWebSocket(), 2000)
      }
    },

    requestInitialStatus() {
        if (this.ws?.readyState === WebSocket.OPEN) {
          // Demander les deux statuts
          console.log('Demande des statuts initiaux')
          this.ws.send(JSON.stringify({ type: 'get_status' }))
          this.ws.send(JSON.stringify({ type: 'get_playback_status' }))
        }
      },

    requestPlaybackStatus() {
      if (this.ws?.readyState === WebSocket.OPEN) {
        // Demander le statut de lecture
        this.ws.send(JSON.stringify({ type: 'get_playback_status' }))
      }
    },

    startProgressTimer() {
      this.clearTimers()
      if (this.playbackStatus?.is_playing) {
        this.startTime = Date.now() - this.progressTime
        this.progressInterval = setInterval(() => {
          this.progressTime = Date.now() - this.startTime
          if (this.progressTime >= this.playbackStatus.duration) {
            this.clearTimers()
            // Demander une mise à jour du statut
            this.requestPlaybackStatus()
          }
        }, 100)  // Mise à jour plus fréquente pour une animation plus fluide
      }
    },

    clearTimers() {
      if (this.progressInterval) {
        clearInterval(this.progressInterval)
        this.progressInterval = null
      }
    },

    formatArtists(artists) {
      return artists?.join(', ') || 'Artiste inconnu'
    },

    formatTime(ms) {
      if (!ms) return '0:00'
      const seconds = Math.floor(ms / 1000)
      const minutes = Math.floor(seconds / 60)
      const remainingSeconds = seconds % 60
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
    },

    handlePlayPause() {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'play_pause' }))
      }
    },

    handleNext() {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'next_track' }))
      }
    },

    handlePrevious() {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'previous_track' }))
      }
    },

    navigateToPlaylists() {
      this.$router.push('/playlists')
    }
  },
  mounted() {
    this.initWebSocket()
  },
  beforeUnmount() {
    this.clearTimers()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  },
  activated() {
    // Si le composant est réactivé (retour sur la page)
    this.initWebSocket()
  },
  deactivated() {
    // Si le composant est désactivé (changement de page)
    this.clearTimers()
  }
}
</script>


<style scoped>
.spotify-view {
  width: 100%;
  height: 100svh;
}

.spotify-player {
  width: 100%;
  height: 100%;
  display: flex;
  gap: var(--spacing-06);
}

.cover-image {
  height: 100%;
  aspect-ratio: 1/1;
}

.cover-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: var(--spacing-06);
}

.placeholder-image {
  width: 100%;
  height: 100%;
  background-color: var(--background-strong);
  border-radius: var(--spacing-06);
}

.content {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
}

.playlist-button {
  position: fixed;
  top: var(--spacing-06);
  right: var(--spacing-06);
  display: none;
}


.track-info {
  flex: 1;
  display: flex;
  gap: var(--spacing-02);
  flex-direction: column;
  justify-content: center;
  text-align: center;
}

.track-info h2 {
  color: var(--text-light);
}


.playback-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-04);
  margin: var(--spacing-05)0;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background-color: var(--background-strong);
  border-radius: 6px;
}

.progress {
  height: 100%;
  background-color: var(--text);
  border-radius: 6px;
}

.time {
  width: 48px;
  text-align: center;
}

@media (max-aspect-ratio: 3/2) {
  .spotify-view {
    flex-direction: column;
  }

  .cover-image {
    height: auto;
  }

  .playlist-button {
    display: none;
  }
}
</style>