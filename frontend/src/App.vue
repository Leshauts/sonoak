<script setup>
import { ref } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import Dock from './components/Dock.vue'
import VolumeBar from './components/VolumeBar.vue'

const volumeBar = ref(null)
</script>

<template>
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" class="view" />
    </transition>
  </router-view>
  <VolumeBar ref="volumeBar" />
  <Dock />
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>