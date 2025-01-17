<template>
  <div class="spotify-view">
    <div class="cover-image">
      <img :src="currentTrack.album_cover_url || 'placeholder-image.jpg'" :alt="currentTrack.name" />
    </div>

    <div class="content">
      <IconButton class="playlist-button-wrapper" @click="navigateToPlaylists">
        <PlaylistIcon color="var(--text)" variant="md" />
      </IconButton>

      <div class="track-info">
        <h1>{{ currentTrack.name || 'Aucune piste' }}</h1>
        <h2>{{ currentTrack.artist_names?.join(', ') || 'Aucun artiste' }}</h2>
      </div>

      <div class="playback-bar">
  <span class="time">{{ formatTime(trackPosition) }}</span>
  <div class="progress-bar" 
       ref="progressBar"
       @click="handleProgressBarClick">
    <div class="progress" 
         :style="{ width: `${progressPercentage}%` }">
    </div>
  </div>
  <span class="time">{{ formatTime(currentTrack.duration) }}</span>
</div>

      <SpotifyController />
    </div>
  </div>
</template>

<script>
import { useSpotifyStore } from '../stores/spotifyStore'
import { mapState } from 'pinia'
import IconButton from '../components/IconButton.vue'
import PlaylistIcon from '../components/icons/PlaylistIcon.vue'
import SpotifyController from '../components/SpotifyController.vue'

export default {
  name: 'SpotifyView',
  components: {
    IconButton,
    PlaylistIcon,
    SpotifyController
  },

  data() {
    return {
      trackPosition: 0,
      progressInterval: null,
      showPreview: false,
      previewPosition: 0,
      previewTime: 0
    }
  },

  computed: {
    ...mapState(useSpotifyStore, ['currentTrack', 'isPlaying']),
    progressPercentage() {
      if (!this.currentTrack.duration) return 0
      return (this.trackPosition / this.currentTrack.duration) * 100
    }
  },

  watch: {
    'currentTrack.position': {
      handler(newPosition) {
        this.trackPosition = newPosition
      },
      immediate: true
    },
    isPlaying: {
      handler(newValue) {
        if (newValue) {
          this.startProgressInterval()
        } else {
          this.stopProgressInterval()
        }
      },
      immediate: true
    }
  },

  methods: {
    formatTime(ms) {
      if (!ms) return '00:00'
      const totalSeconds = Math.floor(ms / 1000)
      const minutes = Math.floor(totalSeconds / 60)
      const seconds = totalSeconds % 60
      return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
    },

    startProgressInterval() {
      this.stopProgressInterval()
      this.progressInterval = setInterval(() => {
        if (this.isPlaying && this.trackPosition < this.currentTrack.duration) {
          this.trackPosition += 1000 // Incrémente d'une seconde
        }
      }, 1000)
    },

    stopProgressInterval() {
      if (this.progressInterval) {
        clearInterval(this.progressInterval)
        this.progressInterval = null
      }
    },

    navigateToPlaylists() {
      this.$router.push('/playlists')
    },


    handleProgressBarClick(event) {
      const store = useSpotifyStore()
      const progressBar = this.$refs.progressBar
      const rect = progressBar.getBoundingClientRect()
      const clickPosition = event.clientX - rect.left
      const percentage = (clickPosition / rect.width)
      const newPosition = Math.floor(this.currentTrack.duration * percentage)
      
      // Mise à jour immédiate de la position locale
      this.trackPosition = newPosition
      
      // Envoi de la commande seek
      store.seek(newPosition)
    },

    handleProgressBarHover(event) {
      if (!this.showPreview) return
      
      const progressBar = this.$refs.progressBar
      const rect = progressBar.getBoundingClientRect()
      const hoverPosition = event.clientX - rect.left
      const percentage = (hoverPosition / rect.width) * 100
      
      this.previewPosition = percentage
      this.previewTime = Math.floor(this.currentTrack.duration * (percentage / 100))
    }

  },

  async mounted() {
    const store = useSpotifyStore()
    await store.fetchInitialState()
    await store.initializeWebSocket()
    this.trackPosition = this.currentTrack.position
    if (this.isPlaying) {
      this.startProgressInterval()
    }
  },

  beforeUnmount() {
    this.stopProgressInterval()
  }
}
</script>

<style scoped>
.spotify-view {
  width: 100%;
  height: 100svh;
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
  cursor: pointer;
  position: relative;
}

.progress-bar:hover {
  height: calc(var(--spacing-01) * 1.5);
}

.progress {
  height: 100%;
  background-color: var(--text);
  border-radius: 2px;
  transition: width 0.1s linear;
}

.progress-bar:hover .progress {
  height: 100%;
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