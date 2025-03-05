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
import MacOSIcon from '@/components/icons/MacOSIcon.vue';
import LoaderIcon from '@/components/icons/LoaderIcon.vue';

export default {
    name: 'SnapcastStatus',
    components: {
        MacOSIcon,
        LoaderIcon
    },
    data() {
        return {
            ws: null,
            clients: [],
            wsConnected: false,
            serverAvailable: false,
            connectionError: null,
            isReady: false,
            serverInfo: null
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
        initWebSocket() {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                return
            }

            try {
                this.ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/snapcast`);
                console.log('Tentative de connexion WebSocket Snapcast');

                this.ws.onopen = () => {
                    console.log('WebSocket Snapcast connecté');
                    this.wsConnected = true;
                    this.connectionError = null;
                    this.checkStatus();
                }

                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        console.log('Message Snapcast reçu:', data);

                        if (data.type === 'clients_status') {
                            this.clients = data.clients;
                            this.serverAvailable = data.server_available;
                            this.serverInfo = data.server_info;
                            if (!this.isReady) {
                                this.isReady = true;
                            }
                        }
                    } catch (error) {
                        console.error('Erreur parsing message:', error);
                    }
                }

                this.ws.onclose = (event) => {
                    console.log('WebSocket Snapcast déconnecté', event.code, event.reason);
                    this.wsConnected = false;
                    this.handleDisconnect();
                }

                this.ws.onerror = (error) => {
                    console.error('Erreur WebSocket Snapcast:', error);
                    this.connectionError = error;
                }
            } catch (error) {
                console.error('Erreur initialisation WebSocket Snapcast:', error);
                this.connectionError = error;
            }
        },

        checkStatus() {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'get_status',
                    data: {}
                }));
            }
        },

        startPeriodicCheck() {
            this.periodicCheck = setInterval(() => {
                this.checkStatus();
            }, 2000);
        },

        handleDisconnect() {
            clearInterval(this.periodicCheck);
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
            this.isReady = false;
        }
    },

    mounted() {
        console.log('Composant Snapcast monté');
        this.initWebSocket();
    },

    beforeUnmount() {
        this.cleanupWebSocket();
    },

    watch: {
        wsConnected(newVal) {
            if (newVal) {
                this.startPeriodicCheck();
            }
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