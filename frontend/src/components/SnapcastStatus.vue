<template>
    <div class="snapcast-status">
      <div class="p-6">
        <div class="flex flex-col space-y-4">
          <div v-if="!serverAvailable" class="text-orange-600">
            Serveur Snapcast non disponible
          </div>
          <div v-else-if="clients.length === 0" class="text-gray-600">
            Aucun client Snapcast connecté
          </div>
          <div v-else>
            <div v-for="client in clients" :key="client.id" 
                 class="flex items-center justify-between p-3 mb-3 bg-white rounded-lg shadow">
              <div class="flex flex-col">
                <span class="font-medium" :class="client.connected ? 'text-green-600' : 'text-red-600'">
                  {{ client.host }}
                </span>
                <span class="text-sm text-gray-500">
                  {{ client.connected ? 'Connecté' : 'Déconnecté' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'SnapcastStatus',
    data() {
      return {
        ws: null,
        clients: [],
        wsConnected: false,
        serverAvailable: false,
        connectionError: null
      }
    },
    methods: {
      initWebSocket() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          return
        }
  
        try {
          this.ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/snapcast`)
          
          this.ws.onopen = () => {
            console.log('WebSocket Snapcast connecté')
            this.wsConnected = true
            this.connectionError = null
            this.checkStatus()
          }
  
          this.ws.onmessage = (event) => {
            try {
              const data = JSON.parse(event.data)
              console.log('Message Snapcast reçu:', data)
              
              if (data.type === 'clients_status') {
                this.clients = data.clients
                this.serverAvailable = data.server_available
              }
            } catch (error) {
              console.error('Erreur parsing message:', error)
            }
          }
  
          this.ws.onclose = (event) => {
            console.log('WebSocket Snapcast déconnecté', event.code, event.reason)
            this.wsConnected = false
            this.handleDisconnect()
          }
  
          this.ws.onerror = (error) => {
            console.error('Erreur WebSocket Snapcast:', error)
            this.connectionError = error
          }
        } catch (error) {
          console.error('Erreur initialisation WebSocket Snapcast:', error)
          this.connectionError = error
        }
      },
  
      checkStatus() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({ 
            type: 'get_status',
            data: {}
          }))
        }
      },
  
      startPeriodicCheck() {
        this.periodicCheck = setInterval(() => {
          this.checkStatus()
        }, 2000)
      },
  
      handleDisconnect() {
        clearInterval(this.periodicCheck)
        setTimeout(() => {
          if (!this.wsConnected) {
            this.initWebSocket()
          }
        }, 2000)
      },
  
      cleanupWebSocket() {
        clearInterval(this.periodicCheck)
        if (this.ws) {
          this.ws.close()
          this.ws = null
        }
        this.wsConnected = false
      }
    },
  
    mounted() {
      this.initWebSocket()
    },
  
    beforeUnmount() {
      this.cleanupWebSocket()
    },
  
    watch: {
      wsConnected(newVal) {
        if (newVal) {
          this.startPeriodicCheck()
        }
      }
    }
  }
  </script>