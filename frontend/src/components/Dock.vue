# Dock.vue
<template>
  <div class="root"
    :style="{ position: 'fixed', width: '100%', height: '100%', pointerEvents: 'none', top: '0', left: '0' }">
    <div :style="{ position: 'absolute', bottom: 0, width: '100%', pointerEvents: 'auto' }">
      <div class="dock-wrapper" @touchstart="handleTouchStart" @touchmove="handleTouchMove" @touchend="handleTouchEnd"
        :style="{ transform: `translateX(-50%) translateY(${dockPosition}px)` }">
        <nav class="dock">
          <div v-if="showIndicator" class="dock-indicator" :style="indicatorStyle" />
          <router-link v-for="(item, index) in menuItems" :key="item.path" :to="item.path" class="dock-item"
            :class="{ 'active': currentPath === item.path }">
            <img :src="'/src/components/services/' + item.iconName + '.svg'" :alt="item.name" class="dock-icon">
          </router-link>
        </nav>
        <div class="dock-grabber" :style="{ opacity: Math.pow(blurPosition / 100, 2) * 0.12 }"></div>

      </div>
      <GradientBlur :isVisible="isVisible" position="bottom" height="50%"
        :style="{ transform: `translateY(${blurPosition}%)` }" />
    </div>
  </div>
</template>

<script>
import GradientBlur from './GradientBlur.vue';

function SpringSolver(mass, stiffness, damping, initialVelocity) {
  this.m_w0 = Math.sqrt(stiffness / mass);
  this.m_zeta = damping / (2 * Math.sqrt(stiffness * mass));

  if (this.m_zeta < 1) {
    this.m_wd = this.m_w0 * Math.sqrt(1 - this.m_zeta * this.m_zeta);
    this.m_A = 1;
    this.m_B = (this.m_zeta * this.m_w0 + -initialVelocity) / this.m_wd;
  } else {
    this.m_wd = 0;
    this.m_A = 1;
    this.m_B = -initialVelocity + this.m_w0;
  }
}

SpringSolver.prototype.solve = function (t) {
  let result;
  if (this.m_zeta < 1) {
    result = Math.exp(-t * this.m_zeta * this.m_w0) *
      (this.m_A * Math.cos(this.m_wd * t) + this.m_B * Math.sin(this.m_wd * t));
  } else {
    result = (this.m_A + this.m_B * t) * Math.exp(-t * this.m_w0);
  }
  return 1 - result;
};

export default {
  name: 'Dock',
  components: { GradientBlur },
  data() {
    return {
      currentPath: '/spotify',
      isVisible: true,
      touchStartY: 0,
      dockPosition: 0,
      blurPosition: 0,
      dockTension: 0.82,
      blurShowTension: 0.8,
      blurHideTension: 0.8,
      dockShowConfig: {
        springConfig: { mass: 2, stiffness: 160, damping: 19, velocity: 1 },
        duration: 400
      },
      dockHideConfig: {
        springConfig: { mass: 1, stiffness: 100, damping: 14, velocity: 1 },
        duration: 400
      },
      blurShowConfig: {
        springConfig: { mass: 1, stiffness: 140, damping: 30, velocity: 0 },
        duration: 400
      },
      blurHideConfig: {
        springConfig: { mass: 1, stiffness: 240, damping: 30, velocity: 0 },
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
    showIndicator() {
      return this.currentPath !== '/';
    },
    indicatorStyle() {
      const pathToIndexMap = {
        '/spotify': 0,
        '/bluetooth': 1,
        '/macos': 2
      };
      const currentIndex = pathToIndexMap[this.currentPath] || 0;
      return {
        transform: `translateX(${currentIndex * 80 + 20}px)`
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

      if (this.isVisible) {
        const dockDelta = Math.min(96, Math.pow(absDelta, this.dockTension));
        const blurDelta = Math.min(100, Math.pow(absDelta, this.blurShowTension));

        this.dockPosition = deltaY >= 0 ? dockDelta : -dockDelta;
        this.blurPosition = Math.max(0, deltaY >= 0 ? blurDelta : -blurDelta);
      } else {
        const dockDelta = -Math.pow(absDelta, this.dockTension);
        const blurDelta = -Math.pow(absDelta, this.blurHideTension);

        this.dockPosition = Math.min(128, 128 + (deltaY >= 0 ? -dockDelta : dockDelta));
        this.blurPosition = Math.max(0, Math.min(100, 100 + (deltaY >= 0 ? -blurDelta : blurDelta)));
      }
    },
    handleDragEnd() {
      const threshold = 10;
      const shouldToggle = Math.abs(this.dockPosition) > threshold;
      const endPosition = shouldToggle ? (this.isVisible ? 128 : 0) : (this.isVisible ? 0 : 128);

      this.animateElement(
        this.dockPosition,
        endPosition,
        this.isVisible ? this.dockHideConfig : this.dockShowConfig,
        (pos) => this.dockPosition = pos
      );

      this.animateElement(
        this.blurPosition,
        shouldToggle ? 100 : 0,
        this.isVisible ? this.blurHideConfig : this.blurShowConfig,
        (pos) => this.blurPosition = pos
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
      const threshold = 5;
      const currentPosition = this.isVisible ? this.dockPosition : (100 - this.dockPosition);
      const shouldToggle = currentPosition > threshold;
      const endPosition = shouldToggle ? (this.isVisible ? 128 : 0) : (this.isVisible ? 0 : 128);

      this.animateElement(
        this.dockPosition,
        endPosition,
        this.isVisible ? this.dockHideConfig : this.dockShowConfig,
        (pos) => this.dockPosition = pos
      );

      this.animateElement(
        this.blurPosition,
        endPosition,
        this.isVisible ? this.blurHideConfig : this.blurShowConfig,
        (pos) => this.blurPosition = pos
      );

      if (shouldToggle) {
        setTimeout(() => {
          this.isVisible = !this.isVisible;
        }, this.dockHideConfig.duration);
      }
    }
  }
}
</script>

<style scoped>
.dock-wrapper {
  /* background: red; */
  padding: var(--spacing-07) 8% 32px 8%;
  position: absolute;
  left: 50%;
  bottom: 0;
  width: fit-content;
  margin: 0 auto;
  z-index: 10;
}

.dock {
  display: inline-flex;
  padding: 16px 16px;
  justify-content: center;
  align-items: center;
  gap: 16px;
  border-radius: 32px;
  background: var(--background);
  position: relative;
  transition: transform 0.2s cubic-bezier(0.215, 0.61, 0.355, 1),
    opacity 0.2s cubic-bezier(0.215, 0.61, 0.355, 1);
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
  width: 64px;
  height: 64px;
  transition: transform 0.2s ease;
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
  background: var(--text-light, #A6ACA6);
  transition: opacity 0.2s ease;
}

@keyframes fadeIn {
  to {
    opacity: 1;
  }
}

.dock-item.active .dock-icon {
  animation: dimPulse 0.3s ease-in-out;
}

@keyframes dimPulse {
  0% {
    filter: contrast(1);
  }

  50% {
    filter: contrast(0.8);
  }

  100% {
    filter: contrast(1);
  }
}


@media (max-aspect-ratio: 3/2) {
  .dock-grabber {
    top: 18px;
  }
}
</style>