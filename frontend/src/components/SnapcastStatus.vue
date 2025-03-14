<template>
    <Transition name="fade">
        <div v-if="isReady" class="pop-in">
            <div v-if="!serverAvailable" class="pop-in-content">
                <LoaderIcon variant="md" />
                <p>Sonoak est prêt à recevoir l'audio d'un Mac</p>
            </div>
            <div v-else class="pop-in-content">
                <MacOSIcon variant="md" />
                <div>
                    <p class="text-secondary">Connecté à</p>
                    <p class="text">{{ getServerDisplayName }}</p>
                </div>
            </div>
        </div>
    </Transition>
</template>

<script>
import { webSocketService } from '@/services/websocket'
import MacOSIcon from '@/components/icons/MacOSIcon.vue'
import LoaderIcon from '@/components/icons/LoaderIcon.vue'

export default {
    name: 'SnapcastStatus',
    components: {
        MacOSIcon,
        LoaderIcon
    },
    data() {
        return {
            clients: [],
            serverAvailable: false,
            isReady: false,
            serverInfo: null,
            periodicCheck: null,
            unsubscribe: null
        }
    },
    computed: {
        getServerDisplayName() {
            if (!this.serverInfo) return 'Serveur inconnu';
            // Nettoyer le nom du serveur (enlever .local, etc.)
            let name = this.serverInfo.name || 'Unknown';
            name = name.replace('.local', '').replace('.home', '');
            // Mettre la première lettre en majuscule
            return name.charAt(0).toUpperCase() + name.slice(1);
        }
    },
    methods: {
        checkStatus() {
            webSocketService.sendMessage('snapcast', {
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
        console.log('Composant Snapcast monté');
        
        // S'abonner aux messages Snapcast via le service centralisé
        this.unsubscribe = webSocketService.subscribe('snapcast', (data) => {
            if (data.type === 'clients_status') {
                console.log('Mise à jour du statut Snapcast:', data);
                this.clients = data.clients;
                this.serverAvailable = data.server_available;
                this.serverInfo = data.server_info;
                if (!this.isReady) {
                    this.isReady = true;
                }
            }
        });
        
        // Demander l'état actuel
        this.checkStatus();
        this.startPeriodicCheck();
    },
    beforeUnmount() {
        this.stopPeriodicCheck();
        
        // Se désabonner du service
        if (this.unsubscribe) {
            this.unsubscribe();
        }
    }
}
</script>

<style scoped>
.pop-in {
    display: flex;
    width: 280px;
    padding: 32px 24px 24px 24px;
    flex-direction: column;
    align-items: center;
    gap: 16px;
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
    gap: var(--spacing-04);
}

.text-secondary {
    color: var(--text-secondary);
}

.text {
    color: var(--text);
    font-weight: 500;
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