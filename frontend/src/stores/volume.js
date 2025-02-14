// frontend/src/stores/volume.js
import { defineStore } from 'pinia'

export const useVolumeStore = defineStore('volume', {
  state: () => ({
    currentVolume: 0,
    websocket: null,
    isConnected: false,
    isAdjusting: false,
    showVolumeBarCallback: null
  }),

  actions: {
    setShowVolumeBarCallback(callback) {
      this.showVolumeBarCallback = callback
    },

    async initializeWebSocket() {
      if (this.websocket) {
        this.websocket.close()
      }

      this.websocket = new WebSocket(`ws://${window.location.hostname}:8000/ws/volume`)
      
      this.websocket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        if (data.type === 'volume_status') {
          // Mise à jour du volume
          this.currentVolume = data.volume
          console.log(`Volume: ${data.volume}% (ALSA: ${data.alsa_volume})`)
          
          // Afficher la VolumeBar seulement si ce n'est pas un status initial
          if (this.showVolumeBarCallback && data.show_volume_bar && !data.is_initial_status) {
            this.showVolumeBarCallback()
          }
        }
      }

      this.websocket.onopen = () => {
        this.isConnected = true
        this.requestVolumeStatus()
      }

      this.websocket.onclose = () => {
        this.isConnected = false
        setTimeout(() => this.initializeWebSocket(), 5000)
      }
    },

    async requestVolumeStatus() {
      if (this.websocket?.readyState === WebSocket.OPEN) {
        this.websocket.send(JSON.stringify({
          type: 'get_volume'
        }))
      }
    },

    async adjustVolume(delta) {
      if (this.isAdjusting) {
        console.log('Volume adjustment already in progress, skipping')
        return
      }

      this.isAdjusting = true
      try {
        console.log(`Starting volume adjustment from ${this.currentVolume} with delta ${delta}`)
        
        if (this.websocket?.readyState === WebSocket.OPEN) {
          this.websocket.send(JSON.stringify({
            type: 'adjust_volume',
            delta: delta
          }))
        }
        
      } catch (error) {
        console.error('Error during volume adjustment:', error)
      } finally {
        setTimeout(() => {
          this.isAdjusting = false
        }, 100)
      }
    },

    async increaseVolume() {
      await this.adjustVolume(1)
    },

    async decreaseVolume() {
      await this.adjustVolume(-1)
    }
  }
})