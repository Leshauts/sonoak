// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import { API_BASE_URL } from '../config';
import HomeView from '../views/HomeView.vue';
import SpotifyView from '../views/SpotifyView.vue';
import BluetoothView from '../views/BluetoothView.vue';
import MacOSView from '../views/MacOSView.vue';
import SettingsView from '../views/SettingsView.vue';

// Services configuration
const API_ENDPOINTS = {
  spotify: `${API_BASE_URL}/audio/spotify`,
  bluetooth: `${API_BASE_URL}/audio/bluetooth`,
  macos: `${API_BASE_URL}/audio/macos`,
};

// Path to service mapping
const PATH_TO_SERVICE = {
  '/spotify': 'spotify',
  '/bluetooth': 'bluetooth',
  '/macos': 'macos',
};

// Toggle services function
async function toggleServices(activeService) {
  try {
    // Démarrer le service actif
    if (activeService) {
      console.log(`Starting ${activeService} service...`);
      await fetch(`${API_ENDPOINTS[activeService]}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Arrêter les autres services
    for (const service of Object.keys(API_ENDPOINTS)) {
      if (service !== activeService) {
        console.log(`Stopping ${service} service...`);
        await fetch(`${API_ENDPOINTS[service]}/stop`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        });
      }
    }
  } catch (error) {
    console.error('Error toggling services:', error);
  }
}

// Routes configuration
const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { transition: 'fade' },
  },
  {
    path: '/spotify',
    name: 'spotify',
    component: SpotifyView,
    meta: { transition: 'fade' },
  },
  {
    path: '/bluetooth',
    name: 'bluetooth',
    component: BluetoothView,
    meta: { transition: 'fade' },
  },
  {
    path: '/macos',
    name: 'macos',
    component: MacOSView,
    meta: { transition: 'fade' },
  },
  {
    path: '/settings',
    name: 'settings',
    component: SettingsView,
    meta: { transition: 'fade' },
  },
];

// Create and configure router
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

// Navigation hook for service management
router.afterEach(async (to) => {
  const activeService = PATH_TO_SERVICE[to.path];
  if (activeService) {
    await toggleServices(activeService);
  }
});

export default router;