<template>
    <div class="pop-in">
        <AppleIcon class="icon" variant="md" />
        <div v-if="!serverAvailable" class="text">
            Sonoak est prêt à recevoir l’audio d’un ordinateur Mac
        </div>
        <div v-else-if="clients.length === 0" class="text">
            Aucun client Snapcast connecté
        </div>
        <div v-else>
            <div v-for="client in clients" :key="client.id" class="text">
                <p class="text-secondary">Connecté au </p>Mac mini de Léo
            </div>
        </div>
    </div>
</template>

<script>
import AppleIcon from '@/components/icons/AppleIcon.vue';

export default {
    name: 'SnapcastStatus',
    components: {
        AppleIcon,
    },
    props: {
        serverAvailable: Boolean,
        clients: Array,
    },
    data() {
        return {
            ws: null,
            clients: [],
            wsConnected: false,
            serverAvailable: false,
            connectionError: null
        }
    },
    methods: {
        initWebSocket() {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                return
            }

            try {
                this.ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/snapcast`)

                this.ws.onopen = () => {
                    console.log('WebSocket Snapcast connecté')
                    this.wsConnected = true
                    this.connectionError = null
                    this.checkStatus()
                }

                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data)
                        console.log('Message Snapcast reçu:', data)

                        if (data.type === 'clients_status') {
                            this.clients = data.clients
                            this.serverAvailable = data.server_available
                        }
                    } catch (error) {
                        console.error('Erreur parsing message:', error)
                    }
                }

                this.ws.onclose = (event) => {
                    console.log('WebSocket Snapcast déconnecté', event.code, event.reason)
                    this.wsConnected = false
                    this.handleDisconnect()
                }

                this.ws.onerror = (error) => {
                    console.error('Erreur WebSocket Snapcast:', error)
                    this.connectionError = error
                }
            } catch (error) {
                console.error('Erreur initialisation WebSocket Snapcast:', error)
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

<style scoped>
.pop-in {
    display: flex;
    width: 280px;
    padding: 24px 16px;
    flex-direction: column;
    align-items: center;
    gap: 16px;
    border-radius: 16px;
    background: var(--background, #F7F7F7);
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}


.text {
    font: var(--text-font);
    letter-spacing: var(--text-spacing);
    color: var(--text);
    text-align: center;
}
.text-secondary {
    color: var(--text-secondary);
}

@media (max-aspect-ratio: 3/2) {
    .pop-in {
        width: 256px;
    }
}
</style>