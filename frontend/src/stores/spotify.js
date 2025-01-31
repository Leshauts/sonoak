import { defineStore } from 'pinia'

export const useSpotifyStore = defineStore('spotify', {
  state: () => ({
    websocket: null,
    connected: false,
    username: null,
    deviceName: null,
    playbackStatus: {
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
    isConnected: (state) => state.connected,
    currentTrack: (state) => ({
      name: state.playbackStatus.trackName,
      artists: state.playbackStatus.artistNames,
      album: state.playbackStatus.albumName,
      coverUrl: state.playbackStatus.albumCoverUrl
    }),
    playbackProgress: (state) => {
      if (!state.playbackStatus.duration) return 0
      return Math.min(state.progressTime / state.playbackStatus.duration * 100, 100)
    }
  },

  actions: {
    initWebSocket() {
      if (this.websocket) return

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/spotify`
      
      this.websocket = new WebSocket(wsUrl)
      
      this.websocket.onopen = () => {
        console.log('WebSocket Spotify connecté')
        this.requestPlaybackStatus()
      }

      this.websocket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        console.log('Message Spotify reçu:', data)

        if (data.type === 'spotify_status') {
          this.updateConnectionStatus(data.status)
        }
        else if (data.type === 'playback_status' && data.status) {
          this.updatePlaybackStatus(data.status)
        }
      }

      this.websocket.onerror = (error) => {
        console.error('Erreur WebSocket Spotify:', error)
      }

      this.websocket.onclose = () => {
        console.log('WebSocket Spotify déconnecté')
        this.connected = false
        this.websocket = null
        this.clearTimers()
        // Tentative de reconnexion après un délai
        setTimeout(() => this.initWebSocket(), 2000)
      }
    },

    updateConnectionStatus(status) {
      this.connected = status.connected
      this.username = status.username
      this.deviceName = status.device_name

      if (this.connected) {
        this.requestPlaybackStatus()
      }
    },

    updatePlaybackStatus(status) {
      this.playbackStatus = {
        trackName: status.track_name,
        artistNames: status.artist_names || [],
        albumName: status.album_name,
        albumCoverUrl: status.album_cover_url,
        duration: status.duration,
        isPlaying: status.is_playing,
        volume: status.volume
      }

      if (status.is_playing) {
        this.startProgressTimer()
      } else {
        this.clearTimers()
      }
    },

    requestPlaybackStatus() {
      if (this.websocket?.readyState === WebSocket.OPEN) {
        this.websocket.send(JSON.stringify({ type: 'get_playback_status' }))
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

    // Contrôles de lecture
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

    // Nettoyage lors de la destruction du store
    cleanup() {
      this.clearTimers()
      if (this.websocket) {
        this.websocket.close()
        this.websocket = null
      }
    }
  }
})