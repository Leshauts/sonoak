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
            <div v-if="!isChangingDevice">
              <p class="text">
                <span class="text-secondary">Connecté à </span>
                <span class="unbreakable-line">{{ getDeviceDisplayName(activeDevice) }}</span>
              </p>
            </div>
            <div v-else>
              <p class="text-secondary">Changement en cours...</p>
            </div>
          </div>
          <button v-if="!pendingDevice && !isChangingDevice" @click="disconnectDevice(activeDevice.address)"
            class="button-secondary" :disabled="isDisconnecting">
            <p class="text-small text-light">
              {{ isDisconnecting ? "Déconnexion en cours..." : "Déconnecter" }}
            </p>
          </button>
        </div>
      </div>

      <div v-if="pendingDevice" class="pop-in change-device">
        <div class="pop-in-content">
          <div class="main-content">
            <p class="text">
              <span class="unbreakable-line">{{ getDeviceDisplayName(pendingDevice) }}</span>
              <span class="text-secondary"> souhaite récupérer la connexion</span>
            </p>
          </div>
          <div class="horizontal-buttons">
            <button @click="handleAcceptNewDevice(pendingDevice)" class="button-secondary" :disabled="isChangingDevice">
              <p class="text-small text-light">
                Accepter
              </p>
            </button>
            <button @click="handleRefuseNewDevice(pendingDevice)" class="button-secondary" :disabled="isChangingDevice">
              <p class="text-small text-light">
                Refuser
              </p>
            </button>
          </div>
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
      pendingDevice: null,
      wsConnected: false,
      connectionError: null,
      isDisconnecting: false,
      isChangingDevice: false,
      isLoading: true,  // Nouvel état
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

    async handleAcceptNewDevice(newDevice) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.isChangingDevice = true;
        this.pendingDevice = null;

        try {
          this.ws.send(JSON.stringify({
            type: 'switch_device',
            data: {
              oldDeviceAddress: this.activeDevice.address,
              newDeviceAddress: newDevice.address
            }
          }));
        } catch (error) {
          console.error('Erreur lors du changement de device:', error);
          this.handleDisconnect();
        }
      }
    },

    async handleRefuseNewDevice(newDevice) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        try {
          this.ws.send(JSON.stringify({
            type: 'disconnect_device',
            data: { address: newDevice.address }
          }));
        } catch (error) {
          console.error('Erreur lors du refus du device:', error);
          this.handleDisconnect();
        }
      }
      this.pendingDevice = null;
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
          this.startPeriodicCheck();  // Ajout de cette ligne
        };

        this.ws.onmessage = (event) => {
          if (this.isUnmounting) return;
          try {
            const data = JSON.parse(event.data);
            console.log('Message WebSocket reçu:', data);

            if (data.type === 'devices_status') {
              const { activeDevice, pendingDevice } = data;
              this.activeDevice = activeDevice || null;
              this.pendingDevice = pendingDevice || null;
              this.isLoading = false;  // Désactiver le chargement une fois les données reçues

              if (this.isChangingDevice && !pendingDevice) {
                this.isChangingDevice = false;
              }
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
      this.pendingDevice = null;
      this.isChangingDevice = false;
      this.isDisconnecting = false;
    },

  async cleanupWebSocket() {
    this.stopPeriodicCheck();
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

      if (this.ws) {
        // Désactiver tous les handlers avant de fermer
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
        this.pendingDevice = null;
        this.isChangingDevice = false;
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
        console.log('Envoi demande de statut');
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
    },

    startPeriodicCheck() {
      console.log('Démarrage des vérifications périodiques');
      this.stopPeriodicCheck();

      this.periodicCheck = setInterval(() => {
        if (this.ws && this.ws.readyState === WebSocket.OPEN && !this.isUnmounting) {
          this.checkStatus();
        } else {
          this.handleDisconnect();
        }
      }, 2000);
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
  padding: 24px 16px 16px 16px;
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

.horizontal-buttons {
  display: flex;
  gap: var(--spacing-02);
  width: 100%;
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