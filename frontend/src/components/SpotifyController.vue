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
import { useSpotifyStore } from '../stores/spotifyStore'
import { mapState, mapActions } from 'pinia'
import PlayIcon from './icons/PlayIcon.vue'
import PauseIcon from './icons/PauseIcon.vue'
import NextIcon from './icons/NextIcon.vue'
import PreviousIcon from './icons/PreviousIcon.vue'

export default {
  name: 'SpotifyController',
  components: {
    PlayIcon,
    PauseIcon,
    NextIcon,
    PreviousIcon
  },
  computed: {
    ...mapState(useSpotifyStore, ['isPlaying'])
  },
  methods: {
    ...mapActions(useSpotifyStore, ['togglePlay', 'previous', 'next'])
  }
}
</script>

<style scoped>
.controller-wrapper {
  width: 100%;
}

.controller {
  display: inline-flex;
  padding: var(--spacing-05);
  justify-content: center;
  align-items: center;
  gap: 16%;
  border-radius: 16px;
  background: var(--background);
  margin: 0 auto;
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


@media (max-width: 768px) {
  .controller {
    gap: 8%;
  }
}
</style>
