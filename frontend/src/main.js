import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAudioStore } from './stores/audio'
import './styles/main.css'
import './styles/raspberry.css'


// Création de l'application
const app = createApp(App)

// Création et installation de Pinia AVANT le router
const pinia = createPinia()
app.use(pinia)  // Installer Pinia en premier

// Installation du router
app.use(router)

app.config.devtools = false 

// Initialisation du store audio
const audioStore = useAudioStore()
audioStore.initWebSocket()

// Montage de l'application
app.mount('#app')