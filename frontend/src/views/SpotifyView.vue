<template>
  <div class="spotify-view">
    <SpotifyStatus />
    
    <Transition name="fade">
      <div v-if="isReady && shouldShowPlayer" class="player-container">
        <SpotifyPlayer
          :playback-status="spotifyStore.playbackStatus"
          :progress-time="spotifyStore.progressTime"
        />
      </div>
    </Transition>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useSpotifyStore } from '@/stores/spotify'
import SpotifyStatus from '@/components/SpotifyStatus.vue'
import SpotifyPlayer from '@/components/SpotifyPlayer.vue'

export default {
  name: 'SpotifyView',
  components: {
    SpotifyStatus,
    SpotifyPlayer
  },
  setup() {
    const spotifyStore = useSpotifyStore()
    const isReady = ref(false)

    return {
      spotifyStore,
      isReady
    }
  },
  computed: {
    shouldShowPlayer() {
      return this.spotifyStore.isConnected &&
             this.spotifyStore.playbackStatus?.trackName
    }
  },
  watch: {
    'spotifyStore.playbackStatus': {
      immediate: true,
      handler(newStatus) {
        if (!newStatus?.trackName) {
          this.isReady = false
          return
        }

        if (this.spotifyStore.websocket?.readyState === WebSocket.OPEN && !this.isReady) {
          // Ajouter un petit délai pour s'assurer que les données sont bien chargées
          setTimeout(() => {
            this.isReady = true
          }, 100)
        }
      }
    }
  },
  async mounted() {
    this.isReady = false
    if (this.spotifyStore.isConnected) {
      await this.spotifyStore.fetchPlaybackFromAPI()
      this.spotifyStore.requestPlaybackStatus()
    }
  },
  async activated() {
    this.isReady = false
    if (this.spotifyStore.isConnected) {
      try {
        await this.spotifyStore.fetchPlaybackFromAPI()
        this.spotifyStore.requestPlaybackStatus()
      } catch (error) {
        console.error('Erreur lors du chargement des données Spotify:', error)
      }
    }
  },
  deactivated() {
    this.spotifyStore.clearTimers()
    this.isReady = false
  }
}
</script>

<style scoped>
.spotify-view {
  width: 100%;
  height: 100svh;
  position: relative;
  z-index: 0;
}

.player-container {
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>