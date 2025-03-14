<!-- frontend/src/App.vue -->
<script setup>
import { onMounted, onBeforeUnmount } from 'vue'
import { RouterView } from 'vue-router'
import { useAudioStore } from './stores/audio'
import { useSpotifyStore } from './stores/spotify'
import { useVolumeStore } from './stores/volume'
import { webSocketService } from './services/websocket'

// Récupération des stores
const audioStore = useAudioStore()
const spotifyStore = useSpotifyStore()
const volumeStore = useVolumeStore()

// Initialisation de la WebSocket et des stores au montage
onMounted(() => {
  console.log('Initialisation du WebSocket service et des stores')
  // Connexion à la WebSocket centralisée
  webSocketService.connect()
  
  // Initialisation prioritaire des stores audio et volume
  audioStore.initialize()
  volumeStore.initialize()
  
  // Initialiser Spotify uniquement quand la source audio sera Spotify
  // On laisse la souscription en place pour qu'il s'initialise au besoin
  webSocketService.subscribe('audio', (data) => {
    if (data.type === 'audio_state_change' && data.data?.current_source === 'spotify') {
      spotifyStore.initialize()
    }
  })
})

// Nettoyage des ressources au démontage
onBeforeUnmount(() => {
  console.log('Nettoyage des ressources WebSocket')
  audioStore.cleanup()
  spotifyStore.cleanup()
  volumeStore.cleanup()
})
</script>

<template>
  <router-view />
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

#app {
  height: 100%;
  min-height: 100svh;
  display: flex;
  flex-direction: column;
}

.view {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100svh;
  padding: var(--spacing-06);
  box-sizing: border-box;
  overflow-x: hidden;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}
</style>