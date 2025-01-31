import { defineStore } from 'pinia'

export const useSpotifyStore = defineStore('spotify', {
  state: () => ({
    websocket: null,
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
    progressTime: 0,
    startTime: 0,
    progressInterval: null
  }),

  getters: {
    isConnected: (state) => state.connected
  },

  actions: {
    initWebSocket() {
      if (this.websocket) return

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/spotify`
      
      this.websocket = new WebSocket(wsUrl)
      
      this.websocket.onopen = () => {
        console.log('WebSocket Spotify connecté')

        // 🔹 Récupérer immédiatement les données pour éviter le délai d'affichage
        this.fetchStatusFromAPI()
        this.fetchPlaybackFromAPI()

        // 🔹 Demander les données au serveur WebSocket
        this.requestStatus()
      }

      this.websocket.onmessage = async (event) => {
        const data = JSON.parse(event.data)
        console.log('Message Spotify reçu:', data)

        if (data.type === 'spotify_status') {
          this.updateConnectionStatus(data.status)
          if (this.connected) {
            // 🔹 Lancer immédiatement une mise à jour du playback
            this.requestPlaybackStatus()
          }
        } else if (data.type === 'playback_status' && data.status) {
          this.updatePlaybackStatus(data.status)
        }
      }

      this.websocket.onclose = () => {
        console.log('WebSocket Spotify déconnecté')
        this.connected = false
        localStorage.setItem("spotify_connected", "false")
        this.websocket = null
        this.clearTimers()
        setTimeout(() => this.initWebSocket(), 2000) // 🔄 Reconnexion automatique
      }
    },

    requestStatus() {
      if (this.websocket?.readyState === WebSocket.OPEN) {
        this.websocket.send(JSON.stringify({ type: 'get_status' }))
      }
    },

    requestPlaybackStatus() {
      if (this.websocket?.readyState === WebSocket.OPEN) {
        this.websocket.send(JSON.stringify({ type: 'get_playback_status' }))
      }
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
      this.playbackStatus = {
        trackName: status.track_name,
        artistNames: status.artist_names || [],
        albumName: status.album_name,
        albumCoverUrl: status.album_cover_url,
        duration: status.duration,
        isPlaying: status.is_playing,
        volume: status.volume
      }

      // 🔹 Stocker en local pour un affichage immédiat après un refresh
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
        this.startTime = Date.now() - this.progressTime
        this.progressInterval = setInterval(() => {
          this.progressTime = Date.now() - this.startTime
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
      if (this.websocket?.readyState === WebSocket.OPEN) {
        this.websocket.send(JSON.stringify({ type: 'play_pause' }))
      }
    },

    nextTrack() {
      if (this.websocket?.readyState === WebSocket.OPEN) {
        this.websocket.send(JSON.stringify({ type: 'next_track' }))
      }
    },

    previousTrack() {
      if (this.websocket?.readyState === WebSocket.OPEN) {
        this.websocket.send(JSON.stringify({ type: 'previous_track' }))
      }
    },

    cleanup() {
      this.clearTimers()
      if (this.websocket) {
        this.websocket.close()
        this.websocket = null
      }
      this.connected = false
      localStorage.setItem("spotify_connected", "false")
    },

    // 🔹 **Nouvelle fonction** : Récupérer immédiatement les données depuis l'API HTTP
    async fetchStatusFromAPI() {
      try {
        const response = await fetch('/api/spotify/status')
        if (response.ok) {
          const data = await response.json()
          this.updateConnectionStatus(data)
        }
      } catch (err) {
        console.error("Erreur API Spotify (status):", err)
      }
    },

    async fetchPlaybackFromAPI() {
      try {
        const response = await fetch('/api/spotify/playback')
        if (response.ok) {
          const data = await response.json()
          this.updatePlaybackStatus(data)
        }
      } catch (err) {
        console.error("Erreur API Spotify (playback):", err)
      }
    }
  }
})