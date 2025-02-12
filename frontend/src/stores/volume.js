import { defineStore } from 'pinia'

export const useVolumeStore = defineStore('volume', {
  state: () => ({
    currentVolume: 0,
    targetVolume: 0,
    websocket: null,
    isConnected: false,
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
          if (!this.isAdjusting) {
            this.currentVolume = data.volume
            this.targetVolume = data.volume
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

    async adjustVolumeGradually(delta, steps = 2, interval = 150) {
      if (this.websocket?.readyState !== WebSocket.OPEN) return;

      this.isAdjusting = true;
      const stepValue = Math.sign(delta);
      
      // Calculate and set target volume immediately
      const startVolume = this.currentVolume;
      this.targetVolume = Math.min(100, Math.max(0, startVolume + (stepValue * steps)));
      
      console.log(`Starting volume adjustment:
        Initial volume: ${startVolume}
        Target volume: ${this.targetVolume}
        Steps: ${steps}
        Interval: ${interval}ms`);
      
      for (let i = 0; i < steps; i++) {
        this.currentVolume = Math.min(100, Math.max(0, this.currentVolume + stepValue));
        
        console.log(`Step ${i + 1}/${steps}: Volume now ${this.currentVolume}`);
        
        this.websocket.send(JSON.stringify({
          type: 'adjust_volume',
          delta: stepValue
        }));

        await new Promise(resolve => setTimeout(resolve, interval));
      }

      setTimeout(() => {
        this.requestVolumeStatus();
        console.log(`Volume adjustment complete: ${this.currentVolume}`);
        this.isAdjusting = false;
      }, interval);
    },

    async increaseVolume() {
      await this.adjustVolumeGradually(1);
    },

    async decreaseVolume() {
      await this.adjustVolumeGradually(-1);
    }
  }
})