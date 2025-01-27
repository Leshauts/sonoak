<template>
  <div class="bluetooth-dialog">
    <div class="p-6">
      <div class="flex items-center justify-between">
        <div :class="connectionStatusClass">
          {{ connectionStatus }}
        </div>
        <button
          v-if="connectedDevice"
          @click="disconnectDevice"
          class="px-4 py-2 bg-red-100 hover:bg-red-200 rounded text-red-700"
        >
          Déconnecter l'appareil
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BluetoothDialog',

  data() {
    return {
      dialog: true,
      ws: null,
      connectedDevice: null,
      wsConnected: false,
      connectionError: null
    }
  },

  computed: {
    connectionStatus() {
      if (this.connectionError) return 'Erreur de connexion'
      if (!this.wsConnected) return 'Connexion...'
      return this.connectedDevice ? `Connecté à ${this.connectedDevice.name}` : 'Aucun appareil connecté'
    },

    connectionStatusClass() {
      return {
        'text-red-600': this.connectionError,
        'text-yellow-600': !this.wsConnected,
        'text-green-600': this.wsConnected && this.connectedDevice,
        'text-gray-600': this.wsConnected && !this.connectedDevice
      }
    }
  },

  mounted() {
    this.dialog = true
    this.initWebSocket()
  },

  beforeDestroy() {
    this.cleanupWebSocket()
  },

  methods: {
    initWebSocket() {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        return // Éviter les connexions multiples
      }

      try {
        this.ws = new WebSocket(`ws://${window.location.hostname}:8765`)

        this.ws.onopen = () => {
          console.log('WebSocket connecté')
          this.wsConnected = true
          this.connectionError = null
          // Demander le statut initial
          this.checkStatus()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            console.log('Message reçu:', data)

            if (data.type === 'device_connected' && data.device) {
              this.connectedDevice = data.device
            } else if (data.type === 'device_disconnected') {
              this.connectedDevice = null
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
        this.ws.send(JSON.stringify({ command: 'get_status' }))
      }
    },

    startPeriodicCheck() {
      this.periodicCheck = setInterval(() => {
        this.checkStatus()
      }, 2000)
    },

    handleDisconnect() {
      clearInterval(this.periodicCheck)

      // Attendre un peu avant de tenter une reconnexion
      setTimeout(() => {
        if (!this.wsConnected) {
          this.initWebSocket()
        }
      }, 2000)
    },

    disconnectDevice() {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        console.log('Envoi de la commande de déconnexion');  // Log pour debug
        this.ws.send(JSON.stringify({
          command: 'disconnect'
        }));
      }
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

  watch: {
    wsConnected(newVal) {
      if (newVal) {
        this.startPeriodicCheck()
      }
    }
  }
}
</script>