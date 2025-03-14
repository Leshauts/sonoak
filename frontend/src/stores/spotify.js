// frontend/src/stores/spotify.js
import { defineStore } from 'pinia'
import { webSocketService } from '../services/websocket'

export const useSpotifyStore = defineStore('spotify', {
  state: () => ({
    connected: localStorage.getItem("spotify_connected") === "true" || false,
    playbackStatus: JSON.parse(localStorage.getItem("spotify_playbackStatus")) || {
      trackName: null,
      artistNames: [],
      albumName: null,
      albumCoverUrl: null,
      duration: 0,
      isPlaying: false,
      volume: 0
    },
    progressTime: localStorage.getItem("spotify_progressTime") ? parseInt(localStorage.getItem("spotify_progressTime")) : 0,
    startTime: localStorage.getItem("spotify_startTime") ? parseInt(localStorage.getItem("spotify_startTime")) : 0,
    progressInterval: null,
    unsubscribe: null,
    librespotWsUrl: null
  }),

  getters: {
    isConnected: (state) => state.connected,
    playerActive: (state) => !!state.playbackStatus.trackName
  },

  actions: {
    initialize() {
      if (!this.unsubscribe) {
        // Configuration de la WebSocket librespot directe (non centralisée)
        const librespotProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        this.librespotWsUrl = `${librespotProtocol}//${window.location.hostname}:4789/events`
        this.connectToLibrespot()
        
        // S'abonner aux messages Spotify depuis notre service centralisé
        this.unsubscribe = webSocketService.subscribe('spotify', (data) => {
          if (data.type === 'spotify_status') {
            this.updateConnectionStatus(data.status)
            if (this.connected) {
              this.requestPlaybackStatus()
            }
          } else if (data.type === 'playback_status' && data.status) {
            this.updatePlaybackStatus(data.status)
          }
        })
        
        // Demander l'état actuel
        this.fetchStatusFromAPI()
        this.fetchPlaybackFromAPI()
        this.requestStatus()
      }
    },

    connectToLibrespot() {
      try {
        const librespotWs = new WebSocket(this.librespotWsUrl)
        
        librespotWs.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleLibrespotEvent(data)
          } catch (error) {
            console.error('Erreur WebSocket Librespot:', error)
          }
        }
        
        librespotWs.onclose = () => {
          // Reconnexion automatique après délai
          setTimeout(() => this.connectToLibrespot(), 2000)
        }
      } catch (error) {
        console.error('Erreur connexion Librespot:', error)
        setTimeout(() => this.connectToLibrespot(), 2000)
      }
    },

    handleLibrespotEvent(event) {
      console.log('Événement Librespot reçu:', event)
      // Gérer les événements de go-librespot
      switch (event.type) {
        case 'metadata':
          this.progressTime = event.data?.position || 0
          this.startTime = Date.now() - this.progressTime
          break
        case 'seek':
          if (event.data) {
            this.progressTime = event.data.position
            this.startTime = Date.now() - event.data.position
            if (this.playbackStatus.isPlaying) {
              this.startProgressTimer()
            }
          }
          break
      }
    },

    requestStatus() {
      webSocketService.sendMessage('spotify', { type: 'get_status' })
    },

    requestPlaybackStatus() {
      webSocketService.sendMessage('spotify', { type: 'get_playback_status' })
    },

    updateConnectionStatus(status) {
      this.connected = status.connected
      localStorage.setItem("spotify_connected", status.connected.toString())

      if (this.connected) {
        this.requestPlaybackStatus()
      }
    },

    updatePlaybackStatus(status) {
      console.log('Mise à jour du statut de lecture:', status)
      
      // Vérifier si la position est définie et différente de 0
      const position = status.position || 0
      
      this.playbackStatus = {
        trackName: status.track_name,
        artistNames: status.artist_names || [],
        albumName: status.album_name,
        albumCoverUrl: status.album_cover_url,
        duration: status.duration,
        isPlaying: status.is_playing,
        volume: status.volume,
        position: position
      }

      // Mettre à jour le temps de progression
      this.progressTime = position
      this.startTime = Date.now() - position

      // Sauvegarder dans localStorage
      localStorage.setItem("spotify_progressTime", this.progressTime.toString())
      localStorage.setItem("spotify_startTime", this.startTime.toString())
      localStorage.setItem("spotify_playbackStatus", JSON.stringify(this.playbackStatus))

      if (status.is_playing) {
        this.startProgressTimer()
      } else {
        this.clearTimers()
      }
    },

    startProgressTimer() {
      this.clearTimers()
      if (this.playbackStatus.isPlaying) {
        this.progressInterval = setInterval(() => {
          const currentTime = Date.now()
          this.progressTime = currentTime - this.startTime
          if (this.progressTime >= this.playbackStatus.duration) {
            this.clearTimers()
            this.requestPlaybackStatus()
          }
        }, 100)
      }
    },

    clearTimers() {
      if (this.progressInterval) {
        clearInterval(this.progressInterval)
        this.progressInterval = null
      }
    },

    playPause() {
      webSocketService.sendMessage('spotify', { type: 'play_pause' })
    },

    nextTrack() {
      webSocketService.sendMessage('spotify', { type: 'next_track' })
    },

    previousTrack() {
      webSocketService.sendMessage('spotify', { type: 'previous_track' })
    },

    async fetchStatusFromAPI() {
      try {
        const response = await fetch('/api/spotify/status')
        if (!response.ok) {
          console.warn(`Erreur API Spotify status: ${response.status}`)
          return
        }
        
        const contentType = response.headers.get('content-type')
        if (!contentType?.includes('application/json')) {
          console.warn(`Réponse non-JSON (${contentType})`)
          return
        }
        
        const data = await response.json()
        if (data && data.status) {
          this.updateConnectionStatus(data.status)
        }
      } catch (err) {
        console.error("Erreur API Spotify (status):", err)
        // Ne pas modifier l'état connecté en cas d'erreur pour éviter les déconnexions indésirables
      }
    },

    async fetchPlaybackFromAPI() {
      try {
        const response = await fetch('/api/spotify/playback')
        if (!response.ok) {
          console.warn(`Erreur API Spotify playback: ${response.status}`)
          return
        }
        
        const contentType = response.headers.get('content-type')
        if (!contentType?.includes('application/json')) {
          console.warn(`Réponse non-JSON (${contentType})`)
          return
        }
        
        const data = await response.json()
        if (data) {
          this.updatePlaybackStatus(data)
        }
      } catch (err) {
        console.error("Erreur API Spotify (playback):", err)
        // Continuer à utiliser les données existantes en cas d'erreur
      }
    },
    
    cleanup() {
      this.clearTimers()
      if (this.unsubscribe) {
        this.unsubscribe()
        this.unsubscribe = null
      }
      this.connected = false
      localStorage.setItem("spotify_connected", "false")
    }
  }
})