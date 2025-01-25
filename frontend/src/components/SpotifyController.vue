<template>
  <div class="controller-wrapper">
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
  </div>
</template>

<script>
import PlayIcon from './icons/PlayIcon.vue'
import PauseIcon from './icons/PauseIcon.vue'
import NextIcon from './icons/NextIcon.vue'
import PreviousIcon from './icons/PreviousIcon.vue'
import IconButton from './IconButton.vue'

export default {
  name: 'SpotifyController',
  components: {
    PlayIcon,
    PauseIcon,
    NextIcon,
    PreviousIcon,
    IconButton
  },
  data() {
    return {
      isPlaying: false
    }
  },
  methods: {
    togglePlay() {
      this.isPlaying = !this.isPlaying
    },
    previous() {
      // Logique pour la piste précédente
    },
    next() {
      // Logique pour la piste suivante
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

@media (max-aspect-ratio: 3/2) {
  .controller-wrapper {
    padding-bottom: 8px;
  }

  .controller {
    gap: 8%;
  }
}
</style>