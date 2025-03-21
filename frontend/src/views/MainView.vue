<template>
  <div class="main-view">
    <Logo :state="logoState" />
    
    <div class="content">
      <transition name="fade" mode="out-in">
        <div v-if="audioStore.currentSource !== 'none'">
          <!-- Spotify Components -->
          <template v-if="audioStore.currentSource === 'spotify'">
            <SpotifyStatus />
            <SpotifyPlayer
              v-if="spotifyStore.isConnected && spotifyStore.playbackStatus?.trackName"
              :playback-status="spotifyStore.playbackStatus"
              :progress-time="spotifyStore.progressTime"
            />
          </template>

          <!-- Bluetooth Component -->
          <BluetoothStatus v-if="audioStore.currentSource === 'bluetooth'" />

          <!-- Snapcast Component -->
          <SnapcastStatus v-if="audioStore.currentSource === 'macos'" />
        </div>
      </transition>
    </div>
    
    <VolumeBar ref="volumeBar" />
    <Dock />
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useAudioStore } from '../stores/audio'
import { useSpotifyStore } from '../stores/spotify'
import { useVolumeStore } from '../stores/volume'
import Logo from '../components/logo/Sonoak.vue'
import VolumeBar from '../components/VolumeBar.vue'
import Dock from '../components/Dock.vue'
import SpotifyStatus from '../components/SpotifyStatus.vue'
import SpotifyPlayer from '../components/SpotifyPlayer.vue'
import BluetoothStatus from '../components/BluetoothStatus.vue'
import SnapcastStatus from '../components/SnapcastStatus.vue'

export default {
  name: 'MainView',
  components: {
    Logo,
    VolumeBar,
    Dock,
    SpotifyStatus,
    SpotifyPlayer,
    BluetoothStatus,
    SnapcastStatus
  },
  
  setup() {
    const audioStore = useAudioStore()
    const spotifyStore = useSpotifyStore()
    const volumeStore = useVolumeStore()
    const volumeBar = ref(null)

    const logoState = computed(() => {
      switch (audioStore.currentSource) {
        case 'none':
          return 'intro'
        case 'spotify':
          return 'hidden'
        default:
          return 'minified'
      }
    })

    onMounted(() => {
      console.log('MainView mounted - Initializing')
      audioStore.requestCurrentStatus()
      spotifyStore.requestPlaybackStatus()

      // Configurer le callback pour afficher la VolumeBar
      volumeStore.setShowVolumeBarCallback(() => {
        if (volumeBar.value) {
          volumeBar.value.showVolume()
        }
      })

      // Définir la fonction de test sur window
      window.testVolume = () => {
        if (volumeBar.value) {
          console.log('Testing volume bar')
          volumeBar.value.setVolume(50)
        } else {
          console.warn('Volume bar reference not found')
        }
      }
    })

    return {
      audioStore,
      spotifyStore,
      logoState,
      volumeBar
    }
  }
}
</script>

<style scoped>
.main-view {
  height: 100%;
  min-height: 100svh;
  display: flex;
  flex-direction: column;
}

.content {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100svh;
  padding: var(--spacing-06);
  box-sizing: border-box;
  overflow-x: hidden;
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