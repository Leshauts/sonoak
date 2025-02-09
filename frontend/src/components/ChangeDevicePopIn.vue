<!-- frontend/src/components/ChangeDevicePopIn.vue -->
<template>
    <Transition name="fade">
      <div v-if="newDevice" class="change-device-pop-in">
        <div class="pop-in-content">
          <div class="main-content">
            <BluetoothIcon variant="md" />
            <div>
              <p class="text">{{ newDevice.name }} souhaite récupérer la connexion</p>
            </div>
          </div>
          <div class="actions">
            <button 
              @click="handleAccept" 
              class="accept-button"
              :disabled="isProcessing"
            >
              Accepter
            </button>
            <button 
              @click="handleRefuse" 
              class="refuse-button"
              :disabled="isProcessing"
            >
              Refuser
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </template>
  
  <script>
  import BluetoothIcon from '@/components/icons/BluetoothIcon.vue';
  
  export default {
    name: 'ChangeDevicePopIn',
    components: {
      BluetoothIcon
    },
    props: {
      newDevice: {
        type: Object,
        default: null
      }
    },
    data() {
      return {
        isProcessing: false
      }
    },
    methods: {
      async handleAccept() {
        this.isProcessing = true;
        try {
          await this.$emit('accept', this.newDevice);
        } finally {
          this.isProcessing = false;
        }
      },
      async handleRefuse() {
        this.isProcessing = true;
        try {
          await this.$emit('refuse', this.newDevice);
        } finally {
          this.isProcessing = false;
        }
      }
    }
  }
  </script>
  
  <style scoped>
  .change-device-pop-in {
    display: flex;
    width: 280px;
    padding: 24px 16px 16px 16px;
    flex-direction: column;
    align-items: center;
    border-radius: 16px;
    background: var(--background, #F7F7F7);
    position: absolute;
    top: calc(50% + 180px);
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
  }
  
  .actions {
    display: flex;
    gap: var(--spacing-02);
    width: 100%;
    margin-top: var(--spacing-04);
  }
  
  .accept-button, .refuse-button {
    flex: 1;
    padding: var(--spacing-02);
    border: none;
    border-radius: 8px;
    cursor: pointer;
  }
  
  .accept-button {
    background: var(--primary);
    color: white;
  }
  
  .refuse-button {
    background: var(--background-neutral);
    color: var(--text);
  }
  
  /* Réutilisation des styles existants */
  .pop-in-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
    gap: var(--spacing-04);
  }
  
  .main-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
    padding: 0 var(--spacing-02);
    gap: var(--spacing-04);
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