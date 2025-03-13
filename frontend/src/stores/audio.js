// frontend/src/stores/audio.js
import { defineStore } from 'pinia'
import { webSocketService } from '../services/websocket'

export const useAudioStore = defineStore('audio', {
  state: () => ({
    currentSource: 'none',
    isSwitching: false,
    unsubscribe: null
  }),

  actions: {
    initialize() {
      // S'abonner aux messages destinés au service audio
      if (!this.unsubscribe) {
        this.unsubscribe = webSocketService.subscribe('audio', (data) => {
          if (data.type === 'audio_state_change') {
            console.log('Changement d\'état audio:', data.data)
            this.currentSource = data.data.current_source
            this.isSwitching = data.data.is_switching
          }
        })
        
        // Demander l'état actuel
        this.requestCurrentStatus()
      }
    },

    async switchSource(source) {
      console.log('Tentative de changement de source vers:', source)
      webSocketService.sendMessage('audio', {
        type: 'switch_source',
        data: { source }
      })
    },
    
    requestCurrentStatus() {
      webSocketService.sendMessage('audio', {
        type: 'get_status'
      })
    },
    
    cleanup() {
      if (this.unsubscribe) {
        this.unsubscribe()
        this.unsubscribe = null
      }
    }
  }
})