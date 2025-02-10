<template>
  <div class="root"
    :style="{ position: 'fixed', width: '100%', height: '100%', pointerEvents: 'none', top: '0', left: '0' }">
    <div :style="{ position: 'absolute', bottom: 0, width: '100%', pointerEvents: 'auto' }">
      <div class="dock-wrapper" @touchstart="handleTouchStart" @touchmove="handleTouchMove" @touchend="handleTouchEnd"
        @mousedown="handleMouseDown" :style="{ transform: `translateX(-50%) translateY(${dockPosition}px)` }">
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
            <button v-for="(item, index) in menuItems" :key="item.source" @click="switchSource(item.source)"
              class="dock-item" :class="{ 'active': audioStore.currentSource === item.source }" type="button">
              <img :src="'/src/components/services/' + item.iconName + '.svg'" :alt="item.name" class="dock-icon">
            </button>
          </div>
        </nav>
        <div class="dock-grabber" :style="{ opacity: grabberOpacity }"></div>
      </div>
    </div>
  </div>
</template>

<script>
import IconButton from './IconButton.vue';
import LessIcon from './icons/LessIcon.vue';
import PlusIcon from './icons/PlusIcon.vue';
import { SpringSolver } from './spring.js';
import { useAudioStore } from '../stores/audio'


export default {
  name: 'Dock',
  components: {
    IconButton,
    LessIcon,
    PlusIcon
  },
  setup() {
    const audioStore = useAudioStore()
    return { audioStore }
  },
  data() {
    return {
      showIndicator: true,
      isVisible: true,
      touchStartY: 0,
      dockPosition: 0,
      lastTouchPosition: null,
      lastTouchTime: null,
      isDragging: false,
      touchStartTime: 0,
      touchMoveCount: 0,
      menuItems: [
        { name: 'Spotify', source: 'spotify', iconName: 'spotify' },
        { name: 'Bluetooth', source: 'bluetooth', iconName: 'bluetooth' },
        { name: 'MacOS', source: 'macos', iconName: 'macos' }
      ],
      config: {
        default: {
          indicator: {
            offset: 24,
            step: 88
          },
          dock: {
            hidePosition: 128,
            snap: {
              threshold: 0.1,
              minDragDistance: 15,
              velocityThreshold: 0.5,
              dragThreshold: 10,
            },
            animation: {
              show: {
                spring: {
                  mass: 2,
                  stiffness: 160,
                  damping: 19,
                  velocity: 1
                },
                duration: 400
              },
              hide: {
                spring: {
                  mass: 1,
                  stiffness: 100,
                  damping: 14,
                  velocity: 1
                },
                duration: 400
              }
            }
          }
        },
        compact: {
          indicator: {
            offset: 20,
            step: 80
          },
          dock: {
            hidePosition: 184,
            snap: {
              threshold: 0.1,
              minDragDistance: 15,
              velocityThreshold: 0,
              dragThreshold: 15
            },
            animation: {
              show: {
                spring: {
                  mass: 2,
                  stiffness: 160,
                  damping: 19,
                  velocity: 0
                },
                duration: 400
              },
              hide: {
                spring: {
                  mass: 1,
                  stiffness: 100,
                  damping: 14,
                  velocity: 0
                },
                duration: 400
              }
            }
          }
        }
      }
    }
  },
  computed: {
    grabberOpacity() {
      return Math.min(1, Math.pow(Math.abs(this.dockPosition) / this.activeConfig.dock.hidePosition, 4));
    },
    isCompactDevice() {
      return window.matchMedia('(max-aspect-ratio: 3/2)').matches;
    },
    activeConfig() {
      return this.config[this.isCompactDevice ? 'compact' : 'default'];
    },
    indicatorStyle() {
      const currentIndex = { 'spotify': 0, 'bluetooth': 1, 'macos': 2 }[this.audioStore.currentSource] || 0;
      const { offset, step } = this.activeConfig.indicator;
      return {
        transform: `translateX(${currentIndex * step + offset}px)`
      };
    }
  },
  watch: {
    $route(to) {
      this.currentPath = to.path
      this.notifyRouteChange(to.path)
    }
  },
  methods: {
    async handleItemClick(item) {
      if (!this.isDragging) {
        // Au lieu de naviguer, on change la source audio
        const sourceMap = {
          '/spotify': 'spotify',
          '/bluetooth': 'bluetooth',
          '/macos': 'macos'
        }

        if (sourceMap[item.path]) {
          await this.audioStore.switchSource(sourceMap[item.path])
        }
      }
    },


    async switchSource(source) {
      if (!this.isDragging) {
        await this.audioStore.switchSource(source)
      }
    },


    // Mouse event handlers
    handleMouseDown(event) {
      event.preventDefault();
      this.initializeTouch(event.clientY);
      window.addEventListener('mousemove', this.handleMouseMove);
      window.addEventListener('mouseup', this.handleMouseUp);
    },

    handleMouseMove(event) {
      event.preventDefault();
      this.updateTouchPosition(event.clientY);
      this.handleDrag(event.clientY);
    },

    handleMouseUp(event) {
      event.preventDefault();
      window.removeEventListener('mousemove', this.handleMouseMove);
      window.removeEventListener('mouseup', this.handleMouseUp);
      this.handleDragEnd(event);
    },

    handleTouchStart(event) {
      this.touchStartTime = Date.now();
      this.touchMoveCount = 0;
      this.isDragging = false;
      this.initializeTouch(event.touches[0].clientY);
    },

    handleTouchMove(event) {
      this.touchMoveCount++;

      // On ne prévient le comportement par défaut que si on est en train de drag
      if (this.touchMoveCount > 3) {
        this.isDragging = true;
        event.preventDefault();
      }

      this.updateTouchPosition(event.touches[0].clientY);
      this.handleDrag(event.touches[0].clientY);
    },

    handleTouchEnd(event) {
      console.log('touchEnd triggered', { isDragging: this.isDragging });
      const touchDuration = Date.now() - this.touchStartTime;
      if (!this.isDragging && touchDuration < 200) {
        console.log('Was a tap, not a drag');
        this.touchMoveCount = 0;
      }
      this.handleDragEnd(event);
    },

    // Shared handlers
    initializeTouch(clientY) {
      this.touchStartY = clientY;
      this.lastTouchPosition = clientY;
      this.lastTouchTime = Date.now();
    },

    updateTouchPosition(clientY) {
      this.lastTouchPosition = clientY;
      this.lastTouchTime = Date.now();
    },

    handleDrag(clientY) {
      const deltaY = clientY - this.touchStartY;
      const absDelta = Math.abs(deltaY);
      const { hidePosition } = this.activeConfig.dock;

      if (this.isVisible) {
        const dockDelta = Math.min(hidePosition * 0.75, Math.pow(absDelta, 0.7));
        this.dockPosition = deltaY >= 0 ? dockDelta : -dockDelta;
      } else {
        const dockDelta = Math.pow(absDelta, 0.7);
        this.dockPosition = Math.max(0, hidePosition - dockDelta);
      }
    },

    handleDragEnd(event) {
      const { snap, hidePosition } = this.activeConfig.dock;
      const moveDistance = this.isVisible ?
        Math.abs(this.dockPosition) :
        Math.abs(this.dockPosition - hidePosition);

      const totalDistance = Math.abs(hidePosition);
      const movePercentage = moveDistance / totalDistance;
      const velocity = this.calculateVelocity(event);

      const shouldSnap =
        (moveDistance > snap.minDragDistance && movePercentage > snap.threshold) ||
        Math.abs(velocity) > snap.velocityThreshold;

      const endPosition = shouldSnap ?
        (this.isVisible ? hidePosition : 0) :
        (this.isVisible ? 0 : hidePosition);

      const animConfig = this.isVisible ?
        this.activeConfig.dock.animation.hide :
        this.activeConfig.dock.animation.show;

      this.animateElement(
        this.dockPosition,
        endPosition,
        animConfig,
        (pos) => this.dockPosition = pos
      );

      if (shouldSnap) {
        this.isVisible = !this.isVisible;
      }
    },

    calculateVelocity(event) {
      const currentTime = Date.now();
      const timeDelta = currentTime - this.lastTouchTime;

      if (!this.lastTouchPosition || timeDelta === 0) return 0;

      const clientY = event?.changedTouches ?
        event.changedTouches[0].clientY :
        event?.clientY || this.lastTouchPosition;

      return (clientY - this.lastTouchPosition) / timeDelta;
    },

    animateElement(startPosition, endPosition, config, updatePosition) {
      const spring = new SpringSolver(
        config.spring.mass,
        config.spring.stiffness,
        config.spring.damping,
        config.spring.velocity
      );

      const startTime = performance.now();

      const animate = (currentTime) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / config.duration, 1);
        const springProgress = spring.solve(progress);
        const position = startPosition + (endPosition - startPosition) * springProgress;

        updatePosition(position);

        if (progress === 1 && position !== 0 && endPosition === 0) {
          this.smoothToZero(position);
        } else if (progress < 1) {
          requestAnimationFrame(animate);
        }
      };

      requestAnimationFrame(animate);
    },

    smoothToZero(startPosition) {
      const startTime = performance.now();

      const animate = (currentTime) => {
        const progress = Math.min((currentTime - startTime) / 200, 1);
        const easedProgress = 1 - Math.pow(1 - progress, 3);
        this.dockPosition = startPosition * (1 - easedProgress);

        if (progress < 1) requestAnimationFrame(animate);
      };

      requestAnimationFrame(animate);
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
  padding: 8% 8% 24px 8%;
  position: absolute;
  left: 50%;
  bottom: 0;
  width: fit-content;
  margin: 0 auto;
  z-index: 10;
  touch-action: none;
  -webkit-user-select: none;
  user-select: none;
  -webkit-touch-callout: none;
  cursor: grab;
}

.dock-wrapper:active {
  cursor: grabbing;
}

.dock {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-04);
  padding: var(--spacing-04);
  border-radius: 32px;
  background: rgba(220, 220, 220, 0.24);
  backdrop-filter: blur(12px);
  position: relative;
  touch-action: none;
  -webkit-user-drag: none;
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
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}

.dock-icon {
  width: 72px;
  height: 72px;
  transition: transform 0.2s ease;
  border-radius: 16px;
  -webkit-touch-callout: none;
  -webkit-user-select: none;
  user-select: none;
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
  top: 60px;
  margin: 0 auto;
  background: #84848445;
}

.dock-item,
.dock-icon,
.volume-button {
  -webkit-user-select: none;
  user-select: none;
  -webkit-touch-callout: none;
}

@keyframes fadeIn {
  to {
    opacity: 1;
  }
}

@media (max-aspect-ratio: 3/2) {
  .dock-grabber {
    top: 14px;
  }

  .dock-icon {
    width: 64px;
    height: 64px;
  }
}
</style>