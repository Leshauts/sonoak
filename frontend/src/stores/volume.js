// frontend/src/stores/volume.js
import { defineStore } from 'pinia'

export const useVolumeStore = defineStore('volume', {
  state: () => ({
    currentVolume: 0,
    websocket: null,
    isConnected: false,
    adjustmentQueue: Promise.resolve(),
    isAdjusting: false
  }),

  actions: {
    async initializeWebSocket() {
      if (this.websocket) {
        this.websocket.close()
      }

      this.websocket = new WebSocket(`ws://${window.location.hostname}:8000/ws/volume`)
      
      this.websocket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        if (data.type === 'volume_status') {
          // Ne mettre à jour le volume que si nous ne sommes pas en train d'ajuster
          if (!this.isAdjusting) {
            this.currentVolume = data.volume
            console.log('Volume updated from server:', data.volume, 'ALSA volume:', data.alsa_volume)
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

    async sendVolumeAdjustment(delta) {
      if (this.websocket?.readyState === WebSocket.OPEN) {
        this.websocket.send(JSON.stringify({
          type: 'adjust_volume',
          delta: delta
        }))
        
        // Attendre un court instant pour laisser le temps au serveur de traiter
        await new Promise(resolve => setTimeout(resolve, 50))
      }
    },

    async adjustVolume(delta) {
      // Si déjà en cours d'ajustement, ignorer la demande
      if (this.isAdjusting) {
        console.log('Volume adjustment already in progress, skipping')
        return
      }

      this.isAdjusting = true
      try {
        console.log(`Starting volume adjustment from ${this.currentVolume} with delta ${delta}`)
        
        // Mettre à jour le volume localement
        const newVolume = Math.max(0, Math.min(100, this.currentVolume + delta))
        this.currentVolume = newVolume
        
        // Envoyer l'ajustement au serveur
        await this.sendVolumeAdjustment(delta)
        
        // Demander le statut actuel au serveur
        await this.requestVolumeStatus()
        
        console.log(`Volume adjustment complete: ${this.currentVolume}`)
      } catch (error) {
        console.error('Error during volume adjustment:', error)
      } finally {
        this.isAdjusting = false
      }
    },

    async increaseVolume() {
      await this.adjustVolume(2)
    },

    async decreaseVolume() {
      await this.adjustVolume(-2)
    }
  }
})