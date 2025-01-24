<!-- frontend/src/components/VolumeBar.vue -->
<template>
  <div class="root"
    :style="{ position: 'fixed', width: '100%', height: '100%', pointerEvents: 'none', top: '0', left: '0' }">
    <div :style="{ position: 'absolute', top: 0, width: '100%', pointerEvents: 'auto' }">
      <div class="volume-bar-wrapper" :style="{ transform: `translateX(-50%) translateY(${barPosition}px)` }">
        <div class="volume-bar">
          <div class="volume-slider">
            <div class="current-bar" :style="{ width: '33' + '%' }"></div>
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

  requestAnimationFrame(function update(timestamp) {
    const elapsed = timestamp - startTime
    const progress = Math.min(elapsed / config.duration, 1)
    value.value = startValue + (target - startValue) * spring.solve(progress)

    if (progress < 1) requestAnimationFrame(update)
  })
}

function showVolume() {
  isVisible.value = true
  animate(barPosition, 0, springConfigs.volumeBar.show)
  animate(blurPosition, 12, springConfigs.gradientBlur.show)
}

function hideVolume() {
  isVisible.value = false
  animate(barPosition, -128, springConfigs.volumeBar.hide)
  animate(blurPosition, 100, springConfigs.gradientBlur.hide)
}

window.testVolume = () => {
  showVolume()
  // setTimeout(() => hideVolume(), 2000)
}
</script>

<style scoped>
.volume-bar-wrapper {
  width: 100%;
  max-width: 280px;
  padding: 24px 0 var(--spacing-07)  0 ;
  position: absolute;
  left: 50%;
  z-index: 10;
}

.volume-bar {
  width: 100%;
  padding: 16px;
  border-radius: 12px;
  background: rgba(191, 191, 191, 0.32);
  backdrop-filter: blur(12px);
}

.volume-slider {
  position: relative;
  width: 100%;
  height: 6px;
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
    padding: 32px;
  }

  
}
</style>
