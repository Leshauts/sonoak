// frontend/src/stores/volume.js
import { defineStore } from 'pinia'
import { webSocketService } from '../services/websocket'

export const useVolumeStore = defineStore('volume', {
  state: () => ({
    currentVolume: 0,
    isAdjusting: false,
    showVolumeBarCallback: null,
    unsubscribe: null
  }),

  actions: {
    initialize() {
      if (!this.unsubscribe) {
        this.unsubscribe = webSocketService.subscribe('volume', (data) => {
          if (data.type === 'volume_status') {
            // Mise à jour du volume
            this.currentVolume = data.volume
            console.log(`Volume: ${data.volume}% (ALSA: ${data.alsa_volume})`)
            
            // Afficher la VolumeBar seulement si ce n'est pas un status initial
            if (this.showVolumeBarCallback && data.show_volume_bar && !data.is_initial_status) {
              this.showVolumeBarCallback()
            }
          }
        })
        
        // Demander l'état du volume
        this.requestVolumeStatus()
      }
    },

    setShowVolumeBarCallback(callback) {
      this.showVolumeBarCallback = callback
    },

    requestVolumeStatus() {
      webSocketService.sendMessage('volume', {
        type: 'get_volume'
      })
    },

    async adjustVolume(delta) {
      if (this.isAdjusting) {
        console.log('Volume adjustment already in progress, skipping')
        return
      }

      this.isAdjusting = true
      try {
        console.log(`Starting volume adjustment from ${this.currentVolume} with delta ${delta}`)
        
        webSocketService.sendMessage('volume', {
          type: 'adjust_volume',
          delta: delta
        })
        
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
    },
    
    cleanup() {
      if (this.unsubscribe) {
        this.unsubscribe()
        this.unsubscribe = null
      }
    }
  }
})