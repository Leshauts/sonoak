<!-- frontend/src/components/BluetoothStatus.vue -->
<template>
  <div class="bluetooth-container">
    <div class="bluetooth-wrapper">
      <div class="pop-in status">
        <div v-if="isLoading" class="pop-in-content disconnected">
          <LoaderIcon variant="md" />
          <p>Chargement de l'état Bluetooth...</p>
        </div>
        <div v-else-if="!activeDevice" class="pop-in-content disconnected">
          <LoaderIcon variant="md" />
          <p>Sonoak est visible dans vos accessoires Bluetooth</p>
        </div>
        <div v-else class="pop-in-content connected">
          <div class="main-content">
            <BluetoothIcon variant="md" />
            <p class="text">
              <span class="text-secondary">Connecté à </span>
              <span class="unbreakable-line">{{ getDeviceDisplayName(activeDevice) }}</span>
            </p>
          </div>
          <button @click="disconnectDevice(activeDevice.address)"
            class="button-secondary" :disabled="isDisconnecting">
            <p class="text-small text-light">
              {{ isDisconnecting ? "Déconnexion en cours..." : "Déconnecter" }}
            </p>
          </button>
        </div>
      </div>
    </div>
  </div>
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
      activeDevice: null,
      wsConnected: false,
      connectionError: null,
      isDisconnecting: false,
      isLoading: true,
      reconnectAttempts: 0,
      maxReconnectAttempts: 5,
      reconnectTimer: null,
      periodicCheck: null,
      isUnmounting: false
    }
  },
  methods: {
    getDeviceDisplayName(device) {
      return device.name === 'Nom inconnu' ? 'Connexion en cours...' : `${device.name}`
    },

    requestInitialStatus() {
      this.isLoading = true;
      this.checkStatus();
    },

    disconnectDevice(address) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.isDisconnecting = true;
        try {
          this.ws.send(JSON.stringify({
            type: 'disconnect_device',
            data: { address }
          }));

          setTimeout(() => {
            this.isDisconnecting = false;
          }, 3000);
        } catch (error) {
          console.error('Erreur lors de la déconnexion:', error);
          this.handleDisconnect();
        }
      }
    },

    async initWebSocket() {
      if (this.isUnmounting) return;

      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        await this.cleanupWebSocket();
      }

      const wsUrl = `ws://${window.location.hostname}:8000/ws/bluetooth`;
      console.log('Tentative de connexion WebSocket:', wsUrl);

      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          if (this.isUnmounting) {
            this.cleanupWebSocket();
            return;
          }
          console.log('WebSocket connecté');
          this.wsConnected = true;
          this.connectionError = null;
          this.reconnectAttempts = 0;
          this.requestInitialStatus();
          this.startPeriodicCheck();
        };

        this.ws.onmessage = (event) => {
          if (this.isUnmounting) return;
          try {
            const data = JSON.parse(event.data);
            console.log('Message WebSocket reçu:', data);

            if (data.type === 'devices_status') {
              const { activeDevice } = data;
              this.activeDevice = activeDevice || null;
              this.isLoading = false;
            }
          } catch (error) {
            console.error('Erreur parsing message WebSocket:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket fermé:', event);
          this.wsConnected = false;
          if (!this.isUnmounting) {
            this.handleDisconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('Erreur WebSocket:', error);
          this.connectionError = error;
          if (!this.isUnmounting) {
            this.handleDisconnect();
          }
        };
      } catch (error) {
        console.error('Erreur initialisation WebSocket:', error);
        this.connectionError = error;
        if (!this.isUnmounting) {
          this.handleDisconnect();
        }
      }
    },

    resetState() {
      this.activeDevice = null;
      this.isDisconnecting = false;
    },

    async cleanupWebSocket() {
      this.stopPeriodicCheck();
      
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }

      if (this.ws) {
        this.ws.onclose = null;
        this.ws.onerror = null;
        this.ws.onmessage = null;
        this.ws.onopen = null;

        try {
          if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.close();
          }
        } catch (error) {
          console.error('Erreur fermeture WebSocket:', error);
        }
        this.ws = null;
      }

      this.wsConnected = false;
      if (!this.isUnmounting) {
        this.activeDevice = null;
        this.isDisconnecting = false;
      }
    },

    handleDisconnect() {
      if (this.isUnmounting) return;

      this.cleanupWebSocket();

      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        console.log(`Tentative de reconnexion ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts} dans 2 secondes...`);
        this.reconnectAttempts++;

        this.reconnectTimer = setTimeout(() => {
          if (!this.wsConnected && !this.isUnmounting) {
            this.initWebSocket();
          }
        }, 2000);
      } else {
        console.error('Nombre maximum de tentatives de reconnexion atteint');
        this.connectionError = new Error('Impossible de se reconnecter au serveur');
      }
    },

    checkStatus() {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        // Ne vérifier que si on n'a pas d'appareil actif ou si on est en cours de déconnexion
        if (!this.activeDevice || this.isDisconnecting) {
          try {
            this.ws.send(JSON.stringify({
              type: 'get_status',
              data: {}
            }));
          } catch (error) {
            console.error('Erreur lors de l\'envoi du statut:', error);
            this.handleDisconnect();
          }
        }
      }
    },

    startPeriodicCheck() {
      this.periodicCheck = setInterval(() => {
        if (this.ws && this.ws.readyState === WebSocket.OPEN && !this.isUnmounting) {
          this.checkStatus();
        } else {
          this.handleDisconnect();
        }
      }, 5000);  // Passé de 2000 à 5000
    },

    stopPeriodicCheck() {
      if (this.periodicCheck) {
        clearInterval(this.periodicCheck);
        this.periodicCheck = null;
      }
    }
  },

  mounted() {
    console.log('Composant monté, initialisation du WebSocket');
    this.isUnmounting = false;
    this.initWebSocket();
  },

  beforeUnmount() {
    console.log('Nettoyage du composant');
    this.isUnmounting = true;
    this.cleanupWebSocket();
  },

  beforeRouteLeave(to, from, next) {
    console.log('Navigation sortante détectée');
    this.isUnmounting = true;
    this.cleanupWebSocket();
    next();
  }
}
</script>

<style scoped>
.bluetooth-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.bluetooth-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-03);
  align-items: center;
}

.pop-in {
  display: flex;
  width: 280px;
  padding: 32px 24px 16px 24px;
  flex-direction: column;
  align-items: center;
  border-radius: 16px;
  background: var(--background, #F7F7F7);
}

.pop-in-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  width: 100%;
  gap: var(--spacing-04);
}

.pop-in-content.disconnected {
  padding-bottom: var(--spacing-02);
}

.main-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  padding: 0 var(--spacing-02) var(--spacing-02) var(--spacing-02);
  gap: var(--spacing-04);
}

.button-secondary {
  background: var(--background-neutral);
  width: 100%;
  padding: var(--spacing-02);
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.unbreakable-line {
  white-space: nowrap;
}

@media (max-aspect-ratio: 3/2) {
  .pop-in {
    width: 256px;
  }
}
</style>