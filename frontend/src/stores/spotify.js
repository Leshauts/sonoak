import { defineStore } from 'pinia'

export const useSpotifyStore = defineStore('spotify', {
  state: () => ({
    websocket: null,
    librespotWs: null,  // Nouveau WebSocket pour go-librespot
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

      // Initialiser la connexion WebSocket avec go-librespot
      const librespotProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const librespotUrl = `${librespotProtocol}//${window.location.hostname}:3678/events`
      
      this.librespotWs = new WebSocket(librespotUrl)
      this.librespotWs.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handleLibrespotEvent(data)
        } catch (error) {
          console.error('Erreur WebSocket Librespot:', error)
        }
      }

      // WebSocket backend standard
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/spotify`
      
      this.websocket = new WebSocket(wsUrl)
      
      this.websocket.onopen = () => {
        console.log('WebSocket Spotify connecté')
        this.fetchStatusFromAPI()
        this.fetchPlaybackFromAPI()
        this.requestStatus()
      }

      this.websocket.onmessage = async (event) => {
        const data = JSON.parse(event.data)
        console.log('Message Spotify reçu:', data)

        if (data.type === 'spotify_status') {
          this.updateConnectionStatus(data.status)
          if (this.connected) {
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
        setTimeout(() => this.initWebSocket(), 2000)
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

      // Mettre à jour la position si elle est fournie
      if (status.position !== undefined) {
        this.progressTime = status.position
        this.startTime = Date.now() - status.position
      }

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

    async seekTo(position) {
      try {
        const response = await fetch('http://localhost:3678/player/seek', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            position: position
          })
        })

        if (response.ok) {
          this.progressTime = position
          this.startTime = Date.now() - position
          if (this.playbackStatus.isPlaying) {
            this.startProgressTimer()
          }
        }
      } catch (error) {
        console.error('Erreur lors du seek:', error)
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
      if (this.librespotWs) {
        this.librespotWs.close()
        this.librespotWs = null
      }
      this.connected = false
      localStorage.setItem("spotify_connected", "false")
    },

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
        const contentType = response.headers.get('content-type')
        if (!contentType?.includes('application/json')) {
          throw new Error(`Réponse invalide (${contentType}), JSON attendu`)
        }
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()
        this.updatePlaybackStatus(data)
      } catch (err) {
        console.error("Erreur API Spotify (playback):", err)
        this.connected = false
        localStorage.setItem("spotify_connected", "false")
      }
    }
  }
})