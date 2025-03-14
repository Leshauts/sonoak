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
import { webSocketService } from '@/services/websocket';
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
      activeDevice: null,
      isDisconnecting: false,
      isLoading: true,
      unsubscribe: null
    }
  },
  methods: {
    getDeviceDisplayName(device) {
      return device.name === 'Nom inconnu' ? 'Connexion en cours...' : `${device.name}`
    },

    disconnectDevice(address) {
      if (this.isDisconnecting) return;
      
      this.isDisconnecting = true;
      console.log('Déconnexion de l\'appareil:', address);

      try {
        webSocketService.sendMessage('bluetooth', {
          type: 'disconnect_device',
          data: { address }
        });

        // Réinitialiser l'état de déconnexion après 3 secondes si nécessaire
        setTimeout(() => {
          if (this.isDisconnecting) {
            this.isDisconnecting = false;
          }
        }, 3000);
      } catch (error) {
        console.error('Erreur lors de la déconnexion:', error);
        this.isDisconnecting = false;
      }
    },

    checkStatus() {
      console.log('Vérification du statut Bluetooth');
      webSocketService.sendMessage('bluetooth', {
        type: 'get_status',
        data: {}
      });
    },

    startPeriodicCheck() {
      this.stopPeriodicCheck(); // Arrêter l'ancien check si existant
      this.periodicCheck = setInterval(() => {
        this.checkStatus();
      }, 5000);
    },

    stopPeriodicCheck() {
      if (this.periodicCheck) {
        clearInterval(this.periodicCheck);
        this.periodicCheck = null;
      }
    }
  },
  mounted() {
    console.log('BluetoothStatus monté');
    
    // S'abonner aux messages Bluetooth via le service centralisé
    this.unsubscribe = webSocketService.subscribe('bluetooth', (data) => {
      if (data.type === 'devices_status') {
        console.log('Mise à jour du statut des appareils Bluetooth:', data);
        this.activeDevice = data.activeDevice || null;
        this.isLoading = false;
        
        // Si plus d'appareil actif, réinitialiser l'état de déconnexion
        if (!data.activeDevice) {
          this.isDisconnecting = false;
        }
      }
    });
    
    // Demander l'état actuel
    this.checkStatus();
    this.startPeriodicCheck();
  },
  beforeUnmount() {
    console.log('BluetoothStatus démontage');
    this.stopPeriodicCheck();
    
    // Se désabonner du service
    if (this.unsubscribe) {
      this.unsubscribe();
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