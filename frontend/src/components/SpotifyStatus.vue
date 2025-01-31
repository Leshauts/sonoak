<template>
  <div class="spotify-status">
    <div v-if="!spotifyStore.isConnected" class="status disconnected">
      Déconnecté de Spotify
    </div>
  </div>
</template>

<script>
import { useSpotifyStore } from '@/stores/spotify'

export default {
  name: 'SpotifyStatus',
  setup() {
    const spotifyStore = useSpotifyStore()

    // Forcer l'initialisation WebSocket immédiatement
    if (!spotifyStore.websocket) {
      spotifyStore.initWebSocket()
    }

    return {
      spotifyStore
    }
  }
}
</script>