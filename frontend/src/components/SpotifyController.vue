<!-- frontend/src/components/SpotiftController.vue -->
<template>
  <div class="controller-wrapper">
    <div class="controller">
      <button 
        class="control-button" 
        @click="$emit('previous')"
        :disabled="!isEnabled"
      >
        <PreviousIcon :color="isEnabled ? 'var(--text)' : 'var(--text-light)'" variant="lg" />
      </button>
      
      <button 
        class="control-button play-button" 
        @click="$emit('toggle-play')"
        :disabled="!isEnabled"
      >
        <component 
          :is="isPlaying ? 'PauseIcon' : 'PlayIcon'" 
          :color="isEnabled ? 'var(--text)' : 'var(--text-light)'" 
          variant="lg" 
        />
      </button>
      
      <button 
        class="control-button" 
        @click="$emit('next')"
        :disabled="!isEnabled"
      >
        <NextIcon :color="isEnabled ? 'var(--text)' : 'var(--text-light)'" variant="lg" />
      </button>
    </div>
  </div>
</template>

<script>
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
  
  props: {
    isPlaying: {
      type: Boolean,
      default: false
    },
    isEnabled: {
      type: Boolean,
      default: true
    }
  },
  
  emits: ['previous', 'next', 'toggle-play']
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
  transition: all 0.2s ease-in-out;
}

.control-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.control-button:not(:disabled):hover {
  transform: scale(1.1);
}

.play-button {
  transform: scale(1.2);
}

.play-button:not(:disabled):hover {
  transform: scale(1.3);
}

@media (max-width: 768px) {
  .controller {
    gap: 8%;
  }
}
</style>