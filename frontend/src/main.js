import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles/main.css'

// Création de l'application
const app = createApp(App)

// Création et installation de Pinia AVANT le router
const pinia = createPinia()
app.use(pinia)  // Installer Pinia en premier

// Installation du router
app.use(router)

app.config.devtools = false 

// Montage de l'application
app.mount('#app')