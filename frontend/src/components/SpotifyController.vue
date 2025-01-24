<template>
  <div class="controller-wrapper">
    <IconButton class="playlist-button" @click="navigateToPlaylists">
      <PlaylistIcon color="var(--text-light)" variant="md" />
    </IconButton>
    <div class="controller">
      <button class="control-button" @click="previous">
        <PreviousIcon color="var(--text-light)" variant="lg" />
      </button>
      <button class="control-button" @click="togglePlay">
        <component :is="isPlaying ? 'PauseIcon' : 'PlayIcon'" color="var(--text)" variant="lg" />
      </button>
      <button class="control-button" @click="next">
        <NextIcon color="var(--text-light)" variant="lg" />
      </button>
    </div>
    <IconButton class="volume-button" @click="toggleVolume">
      <VolumeIcon color="var(--text-light)" variant="md" />
    </IconButton>
  </div>
</template>

<script>
import PlayIcon from './icons/PlayIcon.vue'
import PauseIcon from './icons/PauseIcon.vue'
import NextIcon from './icons/NextIcon.vue'
import PreviousIcon from './icons/PreviousIcon.vue'
import VolumeIcon from './icons/VolumeIcon.vue'
import PlaylistIcon from './icons/PlaylistIcon.vue'
import IconButton from './IconButton.vue'

export default {
  name: 'SpotifyController',
  components: {
    PlayIcon,
    PauseIcon,
    NextIcon,
    PreviousIcon,
    VolumeIcon,
    PlaylistIcon,
    IconButton
  },
  data() {
    return {
      isPlaying: false,
      isMuted: false
    }
  },
  methods: {

    navigateToPlaylists() {
      this.$router.push('/playlists')
    },
    togglePlay() {
      this.isPlaying = !this.isPlaying
    },
    previous() {
      // Logique pour la piste précédente
    },
    next() {
      // Logique pour la piste suivante
    },
    toggleMute() {
      this.isMuted = !this.isMuted
    }

  }
}
</script>

<style scoped>
.controller-wrapper {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--spacing-05);
  z-index: 5;
}

.controller {
  display: inline-flex;
  padding: var(--spacing-03);
  justify-content: center;
  align-items: center;
  gap: 16%;
  border-radius: 24px;
  background: var(--background);
  width: 100%;
  box-sizing: border-box;
}

.control-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--spacing-02);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s;
}

.volume-button {
  display: none;
}

.playlist-button {
  display: none;
}

@media (max-aspect-ratio: 3/2) {
  .controller {
    gap: 0px;
  }

  .volume-button {
    display: block;
  }
  .playlist-button {
    display: block;
  }
}
</style>
