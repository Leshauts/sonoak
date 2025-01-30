<template>
    <div class="spotify-status">
      <div class="p-6">
        <div class="flex flex-col space-y-4">
          <div v-if="!status.connected" class="text-orange-600">
            Spotify non connecté
          </div>
          <div v-else class="flex items-center justify-between p-3 mb-3 bg-white rounded-lg shadow">
            <div class="flex flex-col">
              <span class="font-medium text-green-600">
                {{ status.device_name || 'Spotify' }}
              </span>
              <span class="text-sm text-gray-500">
                Connecté ({{ status.username }})
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'SpotifyStatus',
    data() {
      return {
        ws: null,
        status: {
          connected: false,
          username: null,
          device_name: null
        }
      }
    },
    methods: {
      initWebSocket() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          return
        }
  
        this.ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/spotify`)
        
        this.ws.onopen = () => {
          console.log('WebSocket Spotify connecté')
          this.checkStatus()
        }
  
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            if (data.type === 'spotify_status') {
              this.status = data.status
            }
          } catch (error) {
            console.error('Erreur parsing message:', error)
          }
        }
  
        this.ws.onclose = () => {
          console.log('WebSocket Spotify déconnecté')
          setTimeout(() => this.initWebSocket(), 2000)
        }
      },
  
      checkStatus() {
        if (this.ws?.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({ 
            type: 'get_status',
            data: {}
          }))
        }
      }
    },
  
    mounted() {
      this.initWebSocket()
    },
  
    beforeUnmount() {
      if (this.ws) {
        this.ws.close()
        this.ws = null
      }
    }
  }
  </script>