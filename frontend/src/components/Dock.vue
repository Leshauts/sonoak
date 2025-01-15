<!-- components/Dock.vue -->
<template>
  <div>
    <div class="gradient-blur" :class="{ 'visible': isVisible && currentPath === '/spotify' }">
      <div></div>
      <div></div>
      <div></div>
      <div></div>
      <div></div>
      <div></div>
    </div>

    <div class="black-overlay" :class="{ 'visible': isVisible && currentPath === '/spotify' }"></div>

    <div class="dock-container" 
         :class="{ 'dock-hidden': !isVisible }"
         @touchstart="handleTouchStart"
         @touchmove="handleTouchMove"
         @touchend="handleTouchEnd">
      <nav class="dock">
        <div v-if="showIndicator" class="dock-indicator" :style="indicatorStyle"></div>
        <router-link v-for="(item, index) in menuItems" 
                     :key="item.path" 
                     :to="item.path" 
                     class="dock-item"
                     :class="{ 'active': currentPath === item.path }">
          <img :src="'/src/components/services/' + item.iconName + '.svg'" 
               :alt="item.name" 
               class="dock-icon">
        </router-link>
      </nav>
    </div>

    <div v-if="currentPath === '/spotify'" 
         class="swipe-zone" 
         :style="{ height: isVisible ? '80%' : '8%' }"
         @touchstart="handleTouchStart"
         @touchmove="handleTouchMove" 
         @touchend="handleTouchEnd">
    </div>
  </div>
</template>

<script>
export default {
  name: 'Dock',
  data() {
    return {
      currentPath: '/',
      isVisible: true,
      touchStartY: null,
      isDragging: false,
      dragProgress: 0,
      dockHeight: 0,
      menuItems: [
        { name: 'Spotify', path: '/spotify', iconName: 'spotify' },
        { name: 'Bluetooth', path: '/bluetooth', iconName: 'bluetooth' },
        { name: 'MacOS', path: '/macos', iconName: 'mac-os' }
      ]
    }
  },

  computed: {
    showIndicator() {
      return this.currentPath !== '/'
    },
    indicatorStyle() {
      const pathToIndexMap = {
        '/spotify': 0,
        '/bluetooth': 1,
        '/macos': 2
      }
      const currentIndex = pathToIndexMap[this.currentPath] || 0
      const totalWidth = 72
      return {
        transform: `translateX(${currentIndex * totalWidth + 20}px)`
      }
    }
  },

  methods: {
    handleTouchStart(event) {
      if (this.currentPath === '/spotify') {
        this.touchStartY = event.touches[0].clientY
        this.isDragging = true
        const dockElement = this.$el.querySelector('.dock-container')
        this.dockHeight = dockElement.offsetHeight
        this.dragProgress = this.isVisible ? 1 : 0
      }
    },

    handleTouchMove(event) {
      if (this.currentPath === '/spotify' && this.isDragging) {
        const currentY = event.touches[0].clientY
        const delta = this.touchStartY - currentY

        if (this.isVisible) {
          this.dragProgress = Math.max(0, Math.min(1, 1 - (-delta / this.dockHeight)))
        } else {
          this.dragProgress = Math.max(0, Math.min(1, delta / this.dockHeight))
        }

        this.updateDockPosition(this.dragProgress)
        event.preventDefault()
      }
    },

    handleTouchEnd() {
      if (this.currentPath === '/spotify') {
        this.isDragging = false

        if (this.isVisible) {
          if (this.dragProgress < 0.5) {
            this.hideDock()
          } else {
            this.showDock()
          }
        } else {
          if (this.dragProgress > 0.5) {
            this.showDock()
          } else {
            this.hideDock()
          }
        }
      }
    },

    updateDockPosition(progress) {
      const dockElement = this.$el.querySelector('.dock-container')
      const gradientBlur = this.$el.querySelector('.gradient-blur')
      const overlayElement = this.$el.querySelector('.black-overlay')

      dockElement.style.transform = `translate(-50%, ${100 * (1 - progress)}%)`

      if (gradientBlur) {
        gradientBlur.style.opacity = progress
      }

      if (overlayElement) {
        overlayElement.style.opacity = progress * 0.7
      }
    },

    animateTo(targetProgress) {
      const startProgress = this.dragProgress
      const startTime = performance.now()
      const duration = 300

      const animate = (currentTime) => {
        const elapsed = currentTime - startTime
        const progress = Math.min(elapsed / duration, 1)

        const eased = this.easeInOutCubic(progress)
        this.dragProgress = startProgress + (targetProgress - startProgress) * eased
        this.updateDockPosition(this.dragProgress)

        if (progress < 1) {
          requestAnimationFrame(animate)
        }
      }

      requestAnimationFrame(animate)
    },

    easeInOutCubic(t) {
      return t < 0.5
        ? 4 * t * t * t
        : 1 - Math.pow(-2 * t + 2, 3) / 2
    },

    showDock() {
      if (this.currentPath === '/spotify') {
        this.animateTo(1)
        this.isVisible = true
      }
    },

    hideDock() {
      if (this.currentPath === '/spotify') {
        this.animateTo(0)
        setTimeout(() => {
          this.isVisible = false
        }, 300)
      }
    }
  },

  created() {
    this.currentPath = this.$route.path
    this.isVisible = this.currentPath !== '/spotify'
    this.dragProgress = this.isVisible ? 1 : 0
  },

  watch: {
    '$route'(to) {
      this.currentPath = to.path
      if (this.currentPath !== '/spotify') {
        this.isVisible = true
      }
    }
  }
}
</script>

<style scoped>
.dock-container {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  background: transparent;
  padding: var(--spacing-06);
  will-change: transform;
}

.dock-container.dock-hidden {
  transform: translate(-50%, 100%);
}

.dock {
  display: inline-flex;
  padding: 16px 24px;
  justify-content: center;
  align-items: center;
  gap: 24px;
  border-radius: 16px;
  background: var(--background);
  position: relative;
}

.dock-indicator {
  width: 8px;
  height: 4px;
  position: absolute;
  left: 24px;
  bottom: 8px;
  border-radius: 99px;
  background: var(--text-light, #A6ACA6);
  transition: transform 0.3s ease;
  opacity: 0;
  animation: fadeIn 0.3s forwards;
}

.dock-item {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 3;
}

.dock-icon {
  width: 48px;
  height: 48px;
}

.swipe-zone {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1;
  transition: height 0.3s ease;
  min-height: 50px;
}

.black-overlay {
  position: fixed;
  height: 60%;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0) 0%, rgba(0, 0, 0, 0.7) 100%);
  opacity: 1;
  pointer-events: none;
  z-index: 4;
  will-change: opacity;
}

.gradient-blur {
  position: fixed;
  z-index: 5;
  inset: auto 0 0 0;
  height: 65%;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.gradient-blur.visible {
  opacity: 1;
}

.gradient-blur > div,
.gradient-blur::before,
.gradient-blur::after {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.01);
}

.gradient-blur::before {
  content: "";
  z-index: 1;
  backdrop-filter: blur(0.25px);
  -webkit-backdrop-filter: blur(0.25px);
  mask: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0) 0%,
    rgba(0, 0, 0, 1) 12.5%,
    rgba(0, 0, 0, 1) 25%,
    rgba(0, 0, 0, 0) 37.5%
  );
  -webkit-mask: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0) 0%,
    rgba(0, 0, 0, 1) 12.5%,
    rgba(0, 0, 0, 1) 25%,
    rgba(0, 0, 0, 0) 37.5%
  );
}

.gradient-blur > div:nth-of-type(1) {
  z-index: 2;
  backdrop-filter: blur(0.75px);
  -webkit-backdrop-filter: blur(0.75px);
  mask: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0) 12.5%,
    rgba(0, 0, 0, 1) 25%,
    rgba(0, 0, 0, 1) 37.5%,
    rgba(0, 0, 0, 0) 50%
  );
  -webkit-mask: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0) 12.5%,
    rgba(0, 0, 0, 1) 25%,
    rgba(0, 0, 0, 1) 37.5%,
    rgba(0, 0, 0, 0) 50%
  );
}

.gradient-blur > div:nth-of-type(2) {
  z-index: 3;
  backdrop-filter: blur(1px);
  -webkit-backdrop-filter: blur(1px);
  mask: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0) 25%,
    rgba(0, 0, 0, 1) 37.5%,
    rgba(0, 0, 0, 1) 50%,
    rgba(0, 0, 0, 0) 62.5%
  );
  -webkit-mask: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0) 25%,
    rgba(0, 0, 0, 1) 37.5%,
    rgba(0, 0, 0, 1) 50%,
    rgba(0, 0, 0, 0) 62.5%
  );
}

.gradient-blur > div:nth-of-type(3) {
  z-index: 4;
  backdrop-filter: blur(3px);
  -webkit-backdrop-filter: blur(3px);
  mask: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0) 37.5%,
    rgba(0, 0, 0, 1) 50%,
    rgba(0, 0, 0, 1) 62.5%,
    rgba(0, 0, 0, 0) 75%
  );
  -webkit-mask: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0) 37.5%,
    rgba(0, 0, 0, 1) 50%,
    rgba(0, 0, 0, 1) 62.5%,
    rgba(0, 0, 0, 0) 75%
  );
}

.gradient-blur > div:nth-of-type(4) {
  z-index: 5;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  mask: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0) 50%,
    rgba(0, 0, 0, 1) 62.5%,
    rgba(0, 0, 0, 1) 75%,
    rgba(0, 0, 0, 0) 87.5%
  );
  -webkit-mask: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0) 50%,
    rgba(0, 0, 0, 1) 62.5%,
    rgba(0, 0, 0, 1) 75%,
    rgba(0, 0, 0, 0) 87.5%
  );
}

.gradient-blur > div:nth-of-type(5) {
  z-index: 6;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  mask: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0) 62.5%,
    rgba(0, 0, 0, 1) 75%,
    rgba(0, 0, 0, 1) 87.5%,
    rgba(0, 0, 0, 0) 100%
  );
  -webkit-mask: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0) 62.5%,
    rgba(0, 0, 0, 1) 75%,
    rgba(0, 0, 0, 1) 87.5%,
    rgba(0, 0, 0, 0) 100%
  );
}

.gradient-blur > div:nth-of-type(6) {
  z-index: 7;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  mask: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0) 75%,
    rgba(0, 0, 0, 1) 87.5%,
    rgba(0, 0, 0, 1) 100%
  );
  -webkit-mask: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0) 75%,
    rgba(0, 0, 0, 1) 87.5%,
    rgba(0, 0, 0, 1) 100%
  );
}

.gradient-blur::after {
  content: "";
  z-index: 8;
  backdrop-filter: blur(48px);
  -webkit-backdrop-filter: blur(48px);
  mask: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0) 87.5%,
    rgba(0, 0, 0, 1) 100%
  );
  -webkit-mask: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0) 87.5%,
    rgba(0, 0, 0, 1) 100%
  );
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>