<!-- SpotifyPlayer.vue -->
<template>
  <div class="spotify-player">
    <!-- Bloc gauche - Image -->
    <div class="cover-image" v-if="playbackStatus">
      <img :src="playbackStatus.albumCoverUrl" :alt="playbackStatus.albumName"
        v-if="playbackStatus.albumCoverUrl" />
      <div class="placeholder-image" v-else></div>
    </div>

    <!-- Bloc droite -->
    <div class="content">
      <!-- Textes -->
      <div class="track-info" v-if="playbackStatus">
        <h1>{{ playbackStatus.trackName }}</h1>
        <h2>{{ formatArtists(playbackStatus.artistNames) }}</h2>
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
        :is-playing="playbackStatus?.isPlaying" 
        @play-pause="store.playPause"
        @next="store.nextTrack" 
        @previous="store.previousTrack" 
      />
    </div>
  </div>
</template>
  
  <script>
  import { useSpotifyStore } from '@/stores/spotify'
  import IconButton from '@/components/IconButton.vue'
  import PlaylistIcon from '@/components/icons/PlaylistIcon.vue'
  import SpotifyController from '@/components/SpotifyController.vue'
  
  export default {
    name: 'SpotifyPlayer',
    components: {
      IconButton,
      PlaylistIcon,
      SpotifyController
    },
    props: {
      playbackStatus: {
        type: Object,
        required: true
      },
      progressTime: {
        type: Number,
        required: true
      }
    },
    setup() {
      const store = useSpotifyStore()
      return { store }
    },
    computed: {
      progressWidth() {
        if (!this.playbackStatus.duration) return '0%'
        const progress = Math.min(
          this.progressTime / this.playbackStatus.duration,
          1
        )
        return `${progress * 100}%`
      }
    },
    methods: {
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
      navigateToPlaylists() {
        this.$router.push('/playlists')
      }
    }
  }
  </script>
  
  <style scoped>
.spotify-player {
  width: 100%;
  height: 100%;
  display: flex;
  gap: var(--spacing-06);
  padding: var(--spacing-06);
  position: absolute;
  inset: 0;
}

.cover-image {
  height: 100%;
  aspect-ratio: 1/1;
  max-height: 100vh;
}

.cover-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: var(--spacing-06);
  /* box-shadow: 0px 0px 0px 24px rgba(255, 0, 0, 0.63) ; */

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

.track-info {
  flex: 1;
  display: flex;
  gap: var(--spacing-02);
  flex-direction: column;
  justify-content: center;
  text-align: center;
  overflow: hidden;
}
  
  .track-info h2 {
    color: var(--text-light);
  }
  
  .playback-bar {
    display: flex;
    align-items: center;
    gap: var(--spacing-04);
    margin-bottom: var(--spacing-05);
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
      gap: 0;
    }
    .cover-image {
      height: auto;
    }
  
    .playlist-button {
      display: none;
    }
  }
  </style>