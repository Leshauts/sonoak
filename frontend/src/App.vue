<script setup>
import { RouterLink, RouterView } from 'vue-router';
import Dock from '@/components/Dock.vue';
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const socket = ref(null);

onMounted(() => {
  socket.value = new WebSocket('ws://sonoak.local:24880');

  socket.value.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'updatePage') {
      const currentPath = router.currentRoute.value.path;
      if (currentPath !== data.page) {
        router.push(data.page); // Synchronize page with server
      }
    }
  };

  router.afterEach((to) => {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify({ type: 'navigate', page: to.path }));
    }
  });
});
</script>

<template>
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" class="view" />
    </transition>
  </router-view>
  <Dock />
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