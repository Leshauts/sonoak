<!-- frontend/src/components/VolumeBar.vue -->
<template>
  <div class="root"
    :style="{ position: 'fixed', width: '100%', height: '100%', pointerEvents: 'none', top: '0', left: '0' }">
    <div :style="{ position: 'absolute', top: 0, width: '100%', pointerEvents: 'auto' }">
      <div class="volume-bar-wrapper" :style="{ transform: `translateX(-50%) translateY(${barPosition}px)` }">
        <div class="volume-bar">
          <div class="volume-slider">
            <div class="current-bar" :style="{ width: currentVolume + '%' }"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { SpringSolver } from './spring.js'

const isVisible = ref(false)
const barPosition = ref(-128)
const blurPosition = ref(100)
const currentVolume = ref(33)
let hideTimer = null

const springConfigs = {
  volumeBar: {
    show: { mass: 1, stiffness: 140, damping: 15, duration: 600 },
    hide: { mass: 1, stiffness: 140, damping: 15, duration: 1000 }
  },
  gradientBlur: {
    show: { mass: 1, stiffness: 160, damping: 25, duration: 600 },
    hide: { mass: 1, stiffness: 160, damping: 40, duration: 1000 }
  }
}

function animate(value, target, config) {
  const spring = new SpringSolver(config.mass, config.stiffness, config.damping, 0)
  const startValue = value.value
  const startTime = performance.now()

  const update = (timestamp) => {
    const elapsed = timestamp - startTime
    const progress = Math.min(elapsed / config.duration, 1)
    value.value = startValue + (target - startValue) * spring.solve(progress)

    if (progress < 1) {
      requestAnimationFrame(update)
    }
  }

  requestAnimationFrame(update)
}

function showVolume() {
  // Annuler le timer de masquage précédent s'il existe
  if (hideTimer) {
    clearTimeout(hideTimer)
  }
  
  isVisible.value = true
  // Animation vers la position visible (0)
  animate(barPosition, 0, springConfigs.volumeBar.show)
  animate(blurPosition, 12, springConfigs.gradientBlur.show)
}

function hideVolume() {
  animate(barPosition, -128, springConfigs.volumeBar.hide)
  animate(blurPosition, 100, springConfigs.gradientBlur.hide)
  isVisible.value = false
}

function setVolume(volume) {
  currentVolume.value = Math.min(100, Math.max(0, volume))
  showVolume()
  
  // Configurer le timer pour masquer la barre après 5 secondes
  hideTimer = setTimeout(() => {
    hideVolume()
  }, 5000)
}

// Exposer les méthodes pour le composant parent
defineExpose({
  showVolume,
  hideVolume,
  setVolume,
  isVisible
})
</script>

<style scoped>
.volume-bar-wrapper {
  padding: 24px 0 var(--spacing-07) 0;
  position: absolute;
  left: 50%;
  z-index: 10;
}

.volume-bar {
  width: 280px;
  padding: 16px;
  border-radius: 12px;
  background: rgba(220, 220, 220, 0.24);
  backdrop-filter: blur(12px);
}

.volume-slider {
  position: relative;
  width: 100%;
  height: 12px;
  background: var(--background-neutral);
  border-radius: 6px;
}

.current-bar {
  position: absolute;
  height: 100%;
  background: var(--text);
  border-radius: 6px;
  left: 0;
  top: 0;
}

@media (max-aspect-ratio: 3/2) {
  .volume-bar-wrapper {
    max-width: none;
    padding: var(--spacing-08);
  }
  .volume-bar {
    width: 256px;
  }
}
</style>