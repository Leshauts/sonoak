// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import SpotifyView from '../views/SpotifyView.vue'
import BluetoothView from '../views/BluetoothView.vue'
import MacOSView from '../views/MacOSView.vue'
import SettingsView from '../views/SettingsView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { transition: 'fade' }
  },
  {
    path: '/spotify',
    name: 'spotify',
    component: SpotifyView,
    meta: { transition: 'fade' }
  },
  {
    path: '/bluetooth',
    name: 'bluetooth',
    component: BluetoothView,
    meta: { transition: 'fade' }
  },
  {
    path: '/macos',
    name: 'macos',
    component: MacOSView,
    meta: { transition: 'fade' }
  },
  {
    path: '/settings',
    name: 'settings',
    component: SettingsView,
    meta: { transition: 'fade' }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router