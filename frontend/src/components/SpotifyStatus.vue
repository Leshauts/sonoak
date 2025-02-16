<template>
  <Transition name="fade">
    <div v-if="isReady && !spotifyStore.isConnected" class="pop-in">
      <div class="pop-in-content">
        <LoaderIcon variant="md" />
        <p>Sonoak est visible dans vos appareils Spotify</p>
      </div>
    </div>
  </Transition>
</template>

<script>
import { useSpotifyStore } from '@/stores/spotify'
import LoaderIcon from '@/components/icons/LoaderIcon.vue'

export default {
  name: 'SpotifyStatus',
  components: {
    LoaderIcon
  },
  setup() {
    const spotifyStore = useSpotifyStore()

    return {
      spotifyStore
    }
  },
  data() {
    return {
      isReady: false
    }
  },
  watch: {
    'spotifyStore.websocket'(newSocket) {
      if (newSocket) {
        // Attendre que la première connexion soit établie
        newSocket.onopen = () => {
          this.isReady = true
        }
      }
    }
  },
  mounted() {
    const spotifyStore = useSpotifyStore()
    
    // Si le websocket existe déjà et est connecté
    if (spotifyStore.websocket && spotifyStore.websocket.readyState === WebSocket.OPEN) {
      this.isReady = true
    }
    // Sinon, initialiser le websocket
    else if (!spotifyStore.websocket) {
      spotifyStore.initWebSocket()
    }
  },
  beforeUnmount() {
    this.isReady = false
  }
}
</script>

<style scoped>
.pop-in {
  display: flex;
  width: 280px;
  padding: 32px 24px 24px 24px;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  border-radius: 16px;
  background: var(--background, #F7F7F7);
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.pop-in-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-04);
}

@media (max-aspect-ratio: 3/2) {
  .pop-in {
    width: 256px;
  }
}

/* Styles de transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>