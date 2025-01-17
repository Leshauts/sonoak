<!-- components/Dock.vue -->
<template>
  <div>
    <!-- Gradient blur background visible uniquement sur Spotify -->
    <div class="focus" :class="{ 'visible': isVisible && currentPath === '/spotify' }"></div>

    <!-- Black overlay visible uniquement sur Spotify -->
    <div class="black-overlay" :class="{ 'visible': isVisible && currentPath === '/spotify' }"></div>

    <!-- Dock avec les événements touch -->
    <div class="dock-container" 
         :class="{ 'dock-hidden': !isVisible }"
         @touchstart="handleTouchStart"
         @touchmove="handleTouchMove"
         @touchend="handleTouchEnd">
      <nav class="dock">
        <div v-if="showIndicator" class="dock-indicator" :style="indicatorStyle"></div>
        <router-link v-for="(item, index) in menuItems" :key="item.path" :to="item.path" class="dock-item"
          :class="{ 'active': currentPath === item.path }">
          <img :src="'/src/components/services/' + item.iconName + '.svg'" :alt="item.name" class="dock-icon">
        </router-link>
      </nav>
    </div>

    <!-- Zone de swipe uniquement visible sur Spotify -->
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
      isSwiping: false,
      menuItems: [
        {
          name: 'Spotify',
          path: '/spotify',
          iconName: 'spotify'
        },
        {
          name: 'Bluetooth',
          path: '/bluetooth',
          iconName: 'bluetooth'
        },
        {
          name: 'MacOS',
          path: '/macos',
          iconName: 'mac-os'
        }
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
    async handleNavClick(item) {
      await this.$router.push(item.path)
    },
    handleTouchStart(event) {
      if (this.currentPath === '/spotify') {
        this.touchStartY = event.touches[0].clientY
        this.isSwiping = true
      }
    },
    handleTouchMove(event) {
      if (this.currentPath === '/spotify' && this.touchStartY !== null && this.isSwiping) {
        const currentY = event.touches[0].clientY
        const swipeDistance = this.touchStartY - currentY

        if (swipeDistance > 20 && currentY < this.touchStartY) {
          this.showDock()
          this.isSwiping = false
          this.touchStartY = null
        } else if (swipeDistance < -20 && currentY > this.touchStartY) {
          this.hideDock()
          this.isSwiping = false
          this.touchStartY = null
        }
      }
    },

    showDock() {
      if (this.currentPath === '/spotify') {
        requestAnimationFrame(() => {
          this.isVisible = true
        })
      }
    },

    hideDock() {
      if (this.currentPath === '/spotify') {
        this.isVisible = false
      }
    },

    handleTouchEnd() {
      if (this.currentPath === '/spotify') {
        this.touchStartY = null
        this.isSwiping = false
      }
    },

    initializeDockVisibility() {
      this.isVisible = true
    }
  },
  created() {
    this.currentPath = this.$route.path
    this.initializeDockVisibility()
  },
  watch: {
    '$route'(to) {
      this.currentPath = to.path
      this.isVisible = true
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
  transition: transform 0.3s ease;
  z-index: 10;
  background: transparent;
  padding: var(--spacing-06);
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
}

.focus {
  position: fixed;
  bottom: 0;
  left: 0;
  height: 100%;
  width: 100%;
  pointer-events: none;
  z-index: 5;
  backdrop-filter: blur(0px);
  -webkit-backdrop-filter: blur(0px);
  -webkit-mask: linear-gradient(to top, rgba(0, 0, 0, 1), rgba(0, 0, 0, 0));
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.4s cubic-bezier(0.785, 0.135, 0.15, 0.86),
              backdrop-filter 0.4s cubic-bezier(0.785, 0.135, 0.15, 0.86),
              -webkit-backdrop-filter 0.4s cubic-bezier(0.785, 0.135, 0.15, 0.86);
}

.focus.visible {
  opacity: 1;
  transform: translateY(0);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

.black-overlay {
  position: fixed;
  height: 60%;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0) 0%, rgba(0, 0, 0, 0.7) 100%);
  opacity: 0;
  pointer-events: none;
  z-index: 4;
  transition: all 0.4s cubic-bezier(0.785, 0.135, 0.15, 0.86);
}

.black-overlay.visible {
  opacity: 1;
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