// frontend/src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles/main.css'
import { API_BASE_URL } from './config'

const app = createApp(App)
const pinia = createPinia()

// Configure global properties
app.config.globalProperties.$apiBaseUrl = API_BASE_URL

app.use(pinia)
app.use(router)

app.mount('#app')