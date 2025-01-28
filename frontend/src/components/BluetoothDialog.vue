<template>
  <div class="bluetooth-dialog">
    <div class="p-6">
      <div class="flex flex-col space-y-4">
        <div v-if="!connectedDevice" class="text-gray-600">
          Aucun appareil connecté
        </div>
        <div v-else class="flex items-center justify-between p-3 bg-white rounded-lg shadow">
          <div class="text-green-600">
            {{ getDeviceDisplayName(connectedDevice) }}
          </div>
          <button
            @click="disconnectDevice(connectedDevice.address)"
            class="px-4 py-2 bg-red-100 hover:bg-red-200 rounded text-red-700"
          >
            Déconnecter
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BluetoothDialog',
  data() {
    return {
      ws: null,
      connectedDevice: null,
      wsConnected: false,
      connectionError: null
    }
  },
  methods: {
    getDeviceDisplayName(device) {
      return device.name === 'Unknown' ? 'Connexion en cours...' : `Connecté à ${device.name}`
    },
    
    disconnectDevice(address) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        console.log('Envoi de la commande de déconnexion pour:', address)
        this.ws.send(JSON.stringify({
          type: 'disconnect_device',
          data: { address }
        }))
      }
    },

    initWebSocket() {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        return // Éviter les connexions multiples
      }

      try {
        this.ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/bluetooth`)
        
        this.ws.onopen = () => {
          console.log('WebSocket connecté')
          this.wsConnected = true
          this.connectionError = null
          this.checkStatus()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            console.log('Message reçu:', data)
            
            if (data.type === 'devices_status') {
              // Comme nous ne gérons qu'un seul appareil, nous prenons le premier de la liste
              this.connectedDevice = data.devices[0] || null
            }
          } catch (error) {
            console.error('Erreur parsing message:', error)
          }
        }

        this.ws.onclose = (event) => {
          console.log('WebSocket déconnecté', event.code, event.reason)
          this.wsConnected = false
          this.handleDisconnect()
        }

        this.ws.onerror = (error) => {
          console.error('Erreur WebSocket:', error)
          this.connectionError = error
        }
      } catch (error) {
        console.error('Erreur initialisation WebSocket:', error)
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