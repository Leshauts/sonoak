// frontend/src/stores/audio.js
import { defineStore } from 'pinia'

export const useAudioStore = defineStore('audio', {
  state: () => ({
    currentSource: 'none',
    isSwitching: false,
    websocket: null
  }),

  actions: {
    initWebSocket() {
      if (this.websocket?.readyState === WebSocket.OPEN) {
        return
      }

      console.log('Tentative de connexion WebSocket audio...')
      this.websocket = new WebSocket(`ws://${window.location.hostname}:8000/ws/audio`)

      this.websocket.onopen = () => {
        console.log('WebSocket Audio connecté avec succès')
        // Demander l'état actuel dès la connexion
        this.requestCurrentStatus()
      }

      this.websocket.onmessage = (event) => {
        console.log('Message audio reçu:', event.data)
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'audio_state_change') {
            console.log('Changement d\'état audio:', data.data)
            this.currentSource = data.data.current_source
            this.isSwitching = data.data.is_switching
          }
        } catch (error) {
          console.error('Erreur parsing message audio:', error)
        }
      }

      this.websocket.onclose = (event) => {
        console.log('WebSocket Audio déconnecté:', event.code, event.reason)
        this.websocket = null
        setTimeout(() => this.initWebSocket(), 2000)
      }

      this.websocket.onerror = (error) => {
        console.error('WebSocket Audio error:', error)
      }
    },

    async switchSource(source) {
      console.log('Tentative de changement de source vers:', source)
      if (this.websocket?.readyState === WebSocket.OPEN) {
        this.websocket.send(JSON.stringify({
          type: 'switch_source',
          data: { source }
        }))
      } else {
        console.error('WebSocket non connecté, impossible de changer la source')
      }
    },
    requestCurrentStatus() {
      if (this.websocket?.readyState === WebSocket.OPEN) {
        this.websocket.send(JSON.stringify({
          type: 'get_status'
        }))
      }
    }
  }
})