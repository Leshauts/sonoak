<template>
  <div class="spotify-status">
    <div v-if="spotifyStore.isConnected" class="status connected">
      Connecté à Spotify 
      <span v-if="spotifyStore.username" class="username">
        ({{ spotifyStore.username }})
      </span>
    </div>
    <div v-else class="status disconnected">
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

    // Initier la connexion WebSocket au montage
    spotifyStore.initWebSocket()

    return {
      spotifyStore
    }
  }
}
</script>