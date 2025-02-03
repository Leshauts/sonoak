<template>
  <Transition name="fade">
    <div v-if="isReady" class="pop-in">
      <div v-if="!connectedDevice" class="pop-in-content disconnected">
        <LoaderIcon variant="md" />
        <p>Sonoak est visible dans vos accessoires Bluetooth</p>
      </div>
      <div v-else class="pop-in-content connected">
        <div class="main-content">
          <BluetoothIcon variant="md" />
          <div>
            <p class="text-secondary">Connecté à</p>
            <p class="text">{{ getDeviceDisplayName(connectedDevice) }}</p>
          </div>
        </div>
        <button @click="disconnectDevice(connectedDevice.address)" class="toDisconect" :disabled="isDisconnecting">
          <p class="text-small text-light">
            {{ isDisconnecting ? "Déconnexion en cours..." : "Déconnecter" }}
          </p>
        </button>
      </div>
    </div>
  </Transition>
</template>

<script>
import LoaderIcon from '@/components/icons/LoaderIcon.vue';
import BluetoothIcon from '@/components/icons/BluetoothIcon.vue';

export default {
  name: 'BluetoothStatus',
  components: {
    LoaderIcon,
    BluetoothIcon
  },
  data() {
    return {
      ws: null,
      connectedDevice: null,
      wsConnected: false,
      connectionError: null,
      isReady: false,
      isDisconnecting: false
    }
  },
  methods: {
    getDeviceDisplayName(device) {
      return device.name === 'Unknown' ? 'Connexion en cours...' : `${device.name}`
    },

    disconnectDevice(address) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.isDisconnecting = true;
        console.log('Envoi de la commande de déconnexion pour:', address);

        this.ws.send(JSON.stringify({
          type: 'disconnect_device',
          data: { address }
        }));

        setTimeout(() => {
          this.isDisconnecting = false;
        }, 3000);
      }
    },

    initWebSocket() {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        console.log('WebSocket déjà connecté');
        return
      }

      const wsUrl = `ws://${window.location.hostname}:8000/ws/bluetooth`;
      console.log('Tentative de connexion WebSocket à:', wsUrl);

      try {
        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log('WebSocket connecté avec succès')
          this.wsConnected = true
          this.connectionError = null
          this.checkStatus()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            console.log('Message WebSocket reçu:', data)

            if (data.type === 'devices_status') {
              console.log('Mise à jour du statut des appareils:', data.devices)
              this.connectedDevice = data.devices[0] || null
              if (!this.isReady) {
                console.log('Composant maintenant prêt à être affiché')
                this.isReady = true
              }
            }
          } catch (error) {
            console.error('Erreur parsing message WebSocket:', error)
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
        console.log('Envoi demande de statut')
        this.ws.send(JSON.stringify({
          type: 'get_status',
          data: {}
        }))
      }
    },

    startPeriodicCheck() {
      console.log('Démarrage des vérifications périodiques')
      this.periodicCheck = setInterval(() => {
        this.checkStatus()
      }, 2000)
    },

    handleDisconnect() {
      clearInterval(this.periodicCheck)
      console.log('Tentative de reconnexion dans 2 secondes...')
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
      this.isReady = false
    }
  },

  mounted() {
    console.log('Composant monté, initialisation du WebSocket')
    this.initWebSocket()
  },

  beforeUnmount() {
    console.log('Nettoyage du composant')
    this.cleanupWebSocket()
  },

  watch: {
    wsConnected(newVal) {
      console.log('État de la connexion WebSocket changé:', newVal)
      if (newVal) {
        this.startPeriodicCheck()
      }
    }
  }
}
</script>

<style scoped>
.pop-in {
  display: flex;
  width: 280px;
  padding: 24px 16px 16px 16px;
  flex-direction: column;
  align-items: center;
  border-radius: 16px;
  background: var(--background, #F7F7F7);
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.pop-in-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  gap: var(--spacing-04);
}

.pop-in-content.connected {
  gap: var(--spacing-05-fixed);
}

.pop-in-content.disconnected {
  padding-bottom: 8px;
}

.main-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  padding: 0 var(--spacing-02) 0 var(--spacing-02);
  gap: var(--spacing-04);
}

button.toDisconect {
  background: var(--background-neutral);
  width: 100%;
  padding: var(--spacing-02);
  border: none;
  border-radius: 8px;
}

@media (max-aspect-ratio: 3/2) {
  .pop-in {
    width: 256px;
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>