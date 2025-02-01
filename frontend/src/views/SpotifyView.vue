<template>
  <div class="spotify-view">
    <SpotifyStatus />

    <div v-if="spotifyStore.isConnected" class="spotify-player">
      <!-- Bloc gauche - Image -->
      <div class="cover-image" v-if="spotifyStore.playbackStatus">
        <img :src="spotifyStore.playbackStatus.albumCoverUrl" :alt="spotifyStore.playbackStatus.albumName"
          v-if="spotifyStore.playbackStatus.albumCoverUrl" />
        <div class="placeholder-image" v-else></div>
      </div>

      <!-- Bloc droite -->
      <div class="content">
        <!-- Bouton playlist -->
        <IconButton class="playlist-button" @click="navigateToPlaylists">
          <PlaylistIcon color="var(--text-light)" variant="md" />
        </IconButton>

        <!-- Textes -->
        <div class="track-info" v-if="spotifyStore.playbackStatus">
          <h1>{{ spotifyStore.playbackStatus.trackName || 'Aucun titre' }}</h1>
          <h2>{{ formatArtists(spotifyStore.playbackStatus.artistNames) }}</h2>
        </div>

        <!-- Barre de lecture -->
        <div class="playback-bar" v-if="spotifyStore.playbackStatus">
          <span class="time">{{ formatTime(spotifyStore.progressTime) }}</span>
          <div class="progress-bar" @click="handleSeek" ref="progressBar">
            <div class="progress" :style="{ width: progressWidth }"></div>
          </div>
          <span class="time">{{ formatTime(spotifyStore.playbackStatus.duration) }}</span>
        </div>

        <!-- Contrôleur Spotify -->
        <SpotifyController :is-playing="spotifyStore.playbackStatus?.isPlaying" @play-pause="spotifyStore.playPause"
          @next="spotifyStore.nextTrack" @previous="spotifyStore.previousTrack" />
      </div>
    </div>

  </div>
</template>

<script>
import { ref } from 'vue'
import { useSpotifyStore } from '@/stores/spotify'
import SpotifyStatus from '@/components/SpotifyStatus.vue'
import IconButton from '@/components/IconButton.vue'
import PlaylistIcon from '@/components/icons/PlaylistIcon.vue'
import SpotifyController from '@/components/SpotifyController.vue'

export default {
  name: 'SpotifyView',
  components: {
    SpotifyStatus,
    IconButton,
    PlaylistIcon,
    SpotifyController
  },
  setup() {
    const spotifyStore = useSpotifyStore()
    const isDev = ref(import.meta.env.DEV)
    return {
      spotifyStore,
      isDev
    }
  },
  computed: {
    progressWidth() {
      if (!this.spotifyStore.playbackStatus.duration) return '0%'
      const progress = Math.min(
        this.spotifyStore.progressTime / this.spotifyStore.playbackStatus.duration,
        1
      )
      return `${progress * 100}%`
    }
  },
  methods: {
    formatArtists(artists) {
      return artists?.join(', ') || 'Artiste inconnu'
    },
    handleSeek(event) {
      const progressBar = this.$refs.progressBar
      const rect = progressBar.getBoundingClientRect()
      const clickPosition = event.clientX - rect.left
      const percentage = clickPosition / rect.width

      const newPosition = Math.floor(percentage * this.spotifyStore.playbackStatus.duration)
      this.spotifyStore.seekTo(newPosition)
    },
    formatTime(ms) {
      if (!ms) return '0:00'
      const seconds = Math.floor(ms / 1000)
      const minutes = Math.floor(seconds / 60)
      const remainingSeconds = seconds % 60
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
    },
    navigateToPlaylists() {
      this.$router.push('/playlists')
    }
  },
  activated() {
    // Lors de l'activation de la vue, on demande une mise à jour du statut
    this.spotifyStore.requestPlaybackStatus()
  },
  deactivated() {
    // Nettoyage des timers lors de la désactivation de la vue
    this.spotifyStore.clearTimers()
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
  .spotify-player {
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