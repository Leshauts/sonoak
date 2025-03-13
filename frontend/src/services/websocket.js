// frontend/src/services/websocket.js
import { ref } from 'vue'

class WebSocketService {
  constructor() {
    this.socket = null
    this.isConnected = ref(false)
    this.reconnectInterval = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 10
    this.subscribers = new Map() // service -> callbacks[]
    this.pendingMessages = [] // Messages à envoyer une fois connecté
    this.messageQueue = [] // Messages reçus à traiter
    this.processingQueue = false
    this.lastProtocolError = null
  }

  /**
   * Initialise la connexion WebSocket
   */
  connect() {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      console.log('WebSocket déjà connecté')
      return
    }
    
    this.cleanup()
    
    const hostname = window.location.hostname === 'localhost' 
      ? 'localhost' 
      : window.location.hostname
      
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${hostname}:8000/ws`
    
    console.log(`Connexion WebSocket à ${wsUrl}`)
    this.socket = new WebSocket(wsUrl)
    
    this.socket.onopen = this.handleOpen.bind(this)
    this.socket.onmessage = this.handleMessage.bind(this)
    this.socket.onclose = this.handleClose.bind(this)
    this.socket.onerror = this.handleError.bind(this)
  }

  /**
   * S'abonne aux messages pour un service spécifique
   * @param {string} service - Nom du service (audio, bluetooth, volume, etc.)
   * @param {Function} callback - Callback à appeler quand un message arrive
   * @returns {Function} Fonction pour se désabonner
   */
  subscribe(service, callback) {
    if (!this.subscribers.has(service)) {
      this.subscribers.set(service, [])
    }
    
    this.subscribers.get(service).push(callback)
    
    // Si c'est la première souscription, s'assurer que la connexion est établie
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      this.connect()
    }
    
    return () => {
      if (this.subscribers.has(service)) {
        const callbacks = this.subscribers.get(service)
        const index = callbacks.indexOf(callback)
        if (index !== -1) {
          callbacks.splice(index, 1)
        }
      }
    }
  }

  /**
   * Envoie un message à un service spécifique
   * @param {string} service - Nom du service destinataire 
   * @param {object} message - Message à envoyer
   */
  sendMessage(service, message) {
    const wrappedMessage = { service, message }
    
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.log(`WebSocket non connecté. Message mis en file d'attente: ${JSON.stringify(wrappedMessage)}`)
      this.pendingMessages.push(wrappedMessage)
      this.connect()
      return
    }
    
    try {
      this.socket.send(JSON.stringify(wrappedMessage))
    } catch (error) {
      console.error(`Erreur d'envoi de message:`, error)
      this.pendingMessages.push(wrappedMessage)
      this.reconnect()
    }
  }

  /**
   * Gère l'ouverture de la connexion
   */
  handleOpen() {
    console.log('WebSocket connecté')
    this.isConnected.value = true
    this.reconnectAttempts = 0
    this.lastProtocolError = null
    
    // Envoyer les messages en attente
    if (this.pendingMessages.length > 0) {
      console.log(`Envoi de ${this.pendingMessages.length} messages en attente`)
      const messages = [...this.pendingMessages]
      this.pendingMessages = []
      
      messages.forEach(msg => {
        this.sendMessage(msg.service, msg.message)
      })
    }
  }

  /**
   * Gère les messages reçus
   * @param {MessageEvent} event - Événement de message
   */
  handleMessage(event) {
    try {
      const data = JSON.parse(event.data)
      
      // Ajouter le message à la file d'attente
      this.messageQueue.push(data)
      
      // Traiter la file d'attente si ce n'est pas déjà en cours
      if (!this.processingQueue) {
        this.processMessageQueue()
      }
    } catch (error) {
      console.error('Erreur de parsing du message:', error)
      this.lastProtocolError = error
    }
  }

  /**
   * Traite les messages en file d'attente de manière asynchrone
   */
  async processMessageQueue() {
    this.processingQueue = true
    
    while (this.messageQueue.length > 0) {
      const data = this.messageQueue.shift()
      
      // Ignorer les pings
      if (data.type === 'ping') {
        this.socket.send(JSON.stringify({ type: 'pong' }))
        continue
      }
      
      // Identifier le service associé au message
      // Si le message contient un champ 'service', l'utiliser
      // Sinon, considérer le message comme 'global'
      const service = data.service || 'global'
      
      // Récupérer le contenu réel du message (en retirant l'enveloppe 'service')
      const messageContent = { ...data }
      delete messageContent.service

      // Trouver les abonnés au service correspondant
      const callbacks = this.subscribers.get(service) || []
      
      // Appeler les callbacks avec le contenu du message (sans l'enveloppe)
      for (const callback of callbacks) {
        try {
          callback(messageContent)
        } catch (error) {
          console.error(`Erreur dans un callback pour ${service}:`, error)
        }
        
        // Petite pause pour éviter de bloquer l'UI
        await new Promise(resolve => setTimeout(resolve, 0))
      }
      
      // Si c'est un message global, vérifier s'il y a des abonnés spécifiques
      if (service !== 'global') {
        const globalCallbacks = this.subscribers.get('global') || []
        for (const callback of globalCallbacks) {
          try {
            callback(data) // Passer le message complet aux abonnés globaux
          } catch (error) {
            console.error('Erreur dans un callback global:', error)
          }
          
          await new Promise(resolve => setTimeout(resolve, 0))
        }
      }
    }
    
    this.processingQueue = false
  }

  /**
   * Gère la fermeture de la connexion
   */
  handleClose(event) {
    console.log(`WebSocket fermé: ${event.code} ${event.reason}`)
    this.isConnected.value = false
    this.reconnect()
  }

  /**
   * Gère les erreurs de connexion
   */
  handleError(error) {
    console.error('Erreur WebSocket:', error)
    // Les erreurs sont généralement suivies d'une fermeture
  }

  /**
   * Tente une reconnexion avec backoff exponentiel
   */
  reconnect() {
    if (this.reconnectInterval) {
      clearTimeout(this.reconnectInterval)
    }
    
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), 30000)
      
      console.log(`Tentative de reconnexion ${this.reconnectAttempts}/${this.maxReconnectAttempts} dans ${delay}ms`)
      
      this.reconnectInterval = setTimeout(() => {
        this.connect()
      }, delay)
    } else {
      console.error('Nombre maximum de tentatives de reconnexion atteint')
    }
  }

  /**
   * Nettoie les ressources
   */
  cleanup() {
    if (this.socket) {
      // Supprimer les handlers pour éviter les références circulaires
      this.socket.onopen = null
      this.socket.onmessage = null
      this.socket.onclose = null
      this.socket.onerror = null
      
      // Fermer la connexion si elle est ouverte
      if (this.socket.readyState === WebSocket.OPEN) {
        this.socket.close()
      }
      
      this.socket = null
    }
    
    if (this.reconnectInterval) {
      clearTimeout(this.reconnectInterval)
      this.reconnectInterval = null
    }
  }
}

// Créer une instance unique exportée
export const webSocketService = new WebSocketService()