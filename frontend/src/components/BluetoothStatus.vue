<!-- frontend/src/components/BluetoothStatus.vue -->
<template>
  <div class="bluetooth-container">
    <div class="bluetooth-wrapper">
      <div class="pop-in status">
        <div v-if="!activeDevice" class="pop-in-content disconnected">
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
      isChangingDevice: false
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

        this.ws.send(JSON.stringify({
          type: 'switch_device',
          data: {
            oldDeviceAddress: this.activeDevice.address,
            newDeviceAddress: newDevice.address
          }
        }));
      }
    },

    async handleRefuseNewDevice(newDevice) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'disconnect_device',
          data: { address: newDevice.address }
        }));
      }
      this.pendingDevice = null;
    },

    disconnectDevice(address) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.isDisconnecting = true;
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
        return;
      }

      const wsUrl = `ws://${window.location.hostname}:8000/ws/bluetooth`;

      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          this.wsConnected = true;
          this.connectionError = null;
          this.checkStatus();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === 'devices_status') {
              const { activeDevice, pendingDevice } = data;
              this.activeDevice = activeDevice || null;
              this.pendingDevice = pendingDevice || null;

              // Réinitialiser l'état de changement si nécessaire
              if (this.isChangingDevice && !pendingDevice) {
                this.isChangingDevice = false;
              }
            }
          } catch (error) {
            console.error('Erreur parsing message WebSocket:', error);
          }
        };

        this.ws.onclose = (event) => {
          this.wsConnected = false;
          this.handleDisconnect();
        };

        this.ws.onerror = (error) => {
          this.connectionError = error;
        };
      } catch (error) {
        this.connectionError = error;
      }
    },

    checkStatus() {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        console.log('Envoi demande de statut');
        this.ws.send(JSON.stringify({
          type: 'get_status',
          data: {}
        }));
      }
    },

    startPeriodicCheck() {
      console.log('Démarrage des vérifications périodiques');
      this.periodicCheck = setInterval(() => {
        this.checkStatus();
      }, 2000);
    },

    handleDisconnect() {
      clearInterval(this.periodicCheck);
      console.log('Tentative de reconnexion dans 2 secondes...');
      setTimeout(() => {
        if (!this.wsConnected) {
          this.initWebSocket();
        }
      }, 2000);
    },

    cleanupWebSocket() {
      clearInterval(this.periodicCheck);
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
      this.wsConnected = false;
    }
  },

  mounted() {
    console.log('Composant monté, initialisation du WebSocket');
    this.initWebSocket();
  },

  beforeUnmount() {
    console.log('Nettoyage du composant');
    this.cleanupWebSocket();
  },

  watch: {
    wsConnected(newVal) {
      console.log('État de la connexion WebSocket changé:', newVal);
      if (newVal) {
        this.startPeriodicCheck();
      }
    }
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
  padding-bottom:var(--spacing-02);
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