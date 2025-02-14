<!-- frontend/src/App.vue -->
<script setup>
import { ref, computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import Dock from './components/Dock.vue'
import VolumeBar from './components/VolumeBar.vue'
import Logo from './components/logo/Sonoak.vue'

const volumeBar = ref(null)
const route = useRoute()

const logoState = computed(() => {
  switch (route.path) {
    case '/':
      return 'intro'
    case '/bluetooth':
    case '/macos':
    case '/spotify':
      return 'minified'
    default:
      return 'hidden'
  }
})
</script>

<template>
  <div class="warm-filter"></div>
  <router-view />
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

#app {
  height: 100%;
  min-height: 100svh;
  display: flex;
  flex-direction: column;
}

.view {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100svh;
  padding: var(--spacing-06);
  box-sizing: border-box;
  overflow-x: hidden;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}
</style>