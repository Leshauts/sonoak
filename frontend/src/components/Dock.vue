<template>
  <div class="root"
    :style="{ position: 'fixed', width: '100%', height: '100%', pointerEvents: 'none', top: '0', left: '0' }">
    <div :style="{ position: 'absolute', bottom: 0, width: '100%', pointerEvents: 'auto' }">
      <div class="dock-wrapper" @touchstart="handleTouchStart" @touchmove="handleTouchMove" @touchend="handleTouchEnd"
        :style="{ transform: `translateX(-50%) translateY(${dockPosition}px)` }">
        <nav class="dock">
          <div v-if="isCompactDevice" class="dock-volume-controls">

            <IconButton class="volume-button" @click="LessVolume">
              <LessIcon color="var(--text-light)" variant="md" />
            </IconButton>

            <IconButton class="volume-button" @click="MoreVolume">
              <PlusIcon color="var(--text-light)" variant="md" />
            </IconButton>

          </div>
          <div v-if="showIndicator" class="dock-indicator" :style="indicatorStyle" />
          <div class="dock-items-container">
            <router-link v-for="(item, index) in menuItems" :key="item.path" :to="item.path" class="dock-item"
              :class="{ 'active': currentPath === item.path }">
              <img :src="'/src/components/services/' + item.iconName + '.svg'" :alt="item.name" class="dock-icon">
            </router-link>
          </div>
        </nav>
        <div class="dock-grabber"></div>
      </div>
    </div>
  </div>
</template>

<script>
import IconButton from './IconButton.vue';
import LessIcon from './icons/LessIcon.vue';
import PlusIcon from './icons/PlusIcon.vue';
import { SpringSolver } from './spring.js';

export default {
  name: 'Dock',
  components: {
    IconButton,
    LessIcon,
    PlusIcon
  },
  data() {
    return {
      showIndicator: true,
      currentPath: '/spotify',
      isVisible: true,
      touchStartY: 0,
      dockPosition: 0,
      positionConfig: {
        default: {
          indicatorOffset: 24,
          indicatorStep: 88,
          dockHidePosition: 128,
          dragThreshold: 10
        },
        compact: {
          indicatorOffset: 20,
          indicatorStep: 80,
          dockHidePosition: 184,
          dragThreshold: 1
        }
      },
      dockShowConfig: {
        springConfig: { mass: 2, stiffness: 160, damping: 19, velocity: 1 },
        duration: 400
      },
      dockHideConfig: {
        springConfig: { mass: 1, stiffness: 100, damping: 14, velocity: 1 },
        duration: 400
      },
      menuItems: [
        { name: 'Spotify', path: '/spotify', iconName: 'spotify' },
        { name: 'Bluetooth', path: '/bluetooth', iconName: 'bluetooth' },
        { name: 'MacOS', path: '/macos', iconName: 'macos' }
      ]
    }
  },
  computed: {
    isCompactDevice() {
      return window.matchMedia('(max-aspect-ratio: 3/2)').matches;
    },
    activeConfig() {
      return this.isCompactDevice ? this.positionConfig.compact : this.positionConfig.default;
    },
    indicatorStyle() {
      const currentIndex = { '/spotify': 0, '/bluetooth': 1, '/macos': 2 }[this.currentPath] || 0;
      const { indicatorOffset, indicatorStep } = this.activeConfig;
      return {
        transform: `translateX(${currentIndex * indicatorStep + indicatorOffset}px)`
      };
    }
  },
  watch: {
    $route(to) {
      this.currentPath = to.path;
    }
  },
  methods: {
    handleTouchStart(event) {
      this.touchStartY = event.touches[0].clientY;
    },
    handleMouseDown(event) {
      this.touchStartY = event.clientY;
      window.addEventListener('mousemove', this.handleMouseMove);
      window.addEventListener('mouseup', this.handleMouseUp);
    },
    handleMouseMove(event) {
      this.handleDrag(event.clientY);
    },
    handleMouseUp() {
      window.removeEventListener('mousemove', this.handleMouseMove);
      window.removeEventListener('mouseup', this.handleMouseUp);
      this.handleDragEnd();
    },
    handleTouchMove(event) {
      this.handleDrag(event.touches[0].clientY);
    },
    handleDrag(clientY) {
      const deltaY = clientY - this.touchStartY;
      const absDelta = Math.abs(deltaY);
      const { dockHidePosition } = this.activeConfig;

      if (this.isVisible) {
        const dockDelta = Math.min(dockHidePosition * 0.75, Math.pow(absDelta, 0.82));
        this.dockPosition = deltaY >= 0 ? dockDelta : -dockDelta;
      } else {
        const dockDelta = Math.pow(absDelta, 0.82);
        this.dockPosition = Math.max(0, dockHidePosition - dockDelta);
      }
    },
    handleDragEnd() {
      const { dragThreshold, dockHidePosition } = this.activeConfig;

      let shouldToggle;
      if (this.isVisible) {
        shouldToggle = Math.abs(this.dockPosition) > dragThreshold;
      } else {
        shouldToggle = Math.abs(this.dockPosition - dockHidePosition) > dragThreshold;
      }

      const endPosition = shouldToggle ? (this.isVisible ? dockHidePosition : 0) : (this.isVisible ? 0 : dockHidePosition);

      this.animateElement(
        this.dockPosition,
        endPosition,
        this.isVisible ? this.dockHideConfig : this.dockShowConfig,
        (pos) => this.dockPosition = pos
      );

      if (shouldToggle) {
        this.isVisible = !this.isVisible;
      }
    },
    animateElement(startPosition, endPosition, config, updatePosition) {
      const spring = new SpringSolver(
        config.springConfig.mass,
        config.springConfig.stiffness,
        config.springConfig.damping,
        config.springConfig.velocity
      );

      const startTime = performance.now();

      const animate = (currentTime) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / config.duration, 1);
        const springProgress = spring.solve(progress);

        updatePosition(startPosition + (endPosition - startPosition) * springProgress);

        if (progress < 1) {
          requestAnimationFrame(animate);
        }
      };

      requestAnimationFrame(animate);
    },
    handleTouchEnd() {
      const { dragThreshold, dockHidePosition } = this.activeConfig;

      let shouldToggle;
      if (this.isVisible) {
        shouldToggle = Math.abs(this.dockPosition) > dragThreshold;
      } else {
        shouldToggle = Math.abs(this.dockPosition - dockHidePosition) > dragThreshold;
      }

      const endPosition = shouldToggle ? (this.isVisible ? dockHidePosition : 0) : (this.isVisible ? 0 : dockHidePosition);

      this.animateElement(
        this.dockPosition,
        endPosition,
        this.isVisible ? this.dockHideConfig : this.dockShowConfig,
        (pos) => this.dockPosition = pos
      );

      if (shouldToggle) {
        this.isVisible = !this.isVisible;
      }
    },
    LessVolume() {
      // Logique pour diminuer le volume
    },
    MoreVolume() {
      // Logique pour augmenter le volume
    }
  }
}
</script>

<style scoped>
.dock-wrapper {
  /* background: red; */
  padding: var(--spacing-07) 8% 24px 8%;
  position: absolute;
  left: 50%;
  bottom: 0;
  width: fit-content;
  margin: 0 auto;
  z-index: 10;
}



.dock {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-04);
  padding: var(--spacing-04);
  border-radius: 32px;
  background: rgba(191, 191, 191, 0.32);
  backdrop-filter: blur(12px);
  position: relative;
}

.dock-volume-controls {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  gap: var(--spacing-02);
}

.volume-button {
  background: var(--background-neutral);
  border: none;
  width: 100%;
  padding: 8px;
  border-radius: 16px;

}

.dock-items-container {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  gap: var(--spacing-04);
}

.dock-item {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 3;
  text-decoration: none;
}

.dock-icon {
  width: 72px;
  height: 72px;
  transition: transform 0.2s ease;
  border-radius: 16px;
}

.dock-indicator {
  width: 8px;
  height: 4px;
  position: absolute;
  left: 24px;
  bottom: 8px;
  border-radius: 99px;
  background: var(--text-light, #A6ACA6);
  transition: transform 0.2s ease;
  opacity: 0;
  animation: fadeIn 0.2s forwards;
}

.dock-grabber {
  width: 64px;
  height: 4px;
  flex-shrink: 0;
  border-radius: 2px;
  position: fixed;
  transform: translateX(-50%);
  left: 50%;
  top: 29px;
  margin: 0 auto;
  background: #787978;
  transition: opacity 0.2s ease;
}

@keyframes fadeIn {
  to {
    opacity: 1;
  }
}



@media (max-aspect-ratio: 3/2) {
  .dock-grabber {
    top: 18px;
  }

  .dock-icon {
    width: 64px;
    height: 64px;
  }
}
</style>