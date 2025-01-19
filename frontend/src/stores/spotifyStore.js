import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSpotifyStore = defineStore('spotify', () => {
  // État
  const currentTrack = ref({
    name: '',
    artist_names: [],
    album_cover_url: '',
    position: 0,
    duration: 0,
  })
  const isPlaying = ref(false)
  const volume = ref(100)
  const wsConnection = ref(null)
  const wsRetryCount = ref(0)
  const isActive = ref(false)  // Pour suivre si Spotify est actif
  const MAX_RETRY_COUNT = 10
  let wsReconnectTimeout = null

  // Fonctions
  function clearReconnectTimeout() {
    if (wsReconnectTimeout) {
      clearTimeout(wsReconnectTimeout)
      wsReconnectTimeout = null
    }
  }

  function setSpotifyRoute(isSpotifyPage) {
    isActive.value = isSpotifyPage
    if (isSpotifyPage) {
      initializeWebSocket()
    } else {
      cleanupConnections()
    }
  }

  function cleanupConnections() {
    clearReconnectTimeout()
    if (wsConnection.value) {
      console.log('Closing WebSocket connection')
      wsConnection.value.close()
      wsConnection.value = null
    }
    wsRetryCount.value = 0
    // Réinitialiser l'état
    currentTrack.value = {
      name: '',
      artist_names: [],
      album_cover_url: '',
      position: 0,
      duration: 0,
    }
    isPlaying.value = false
    volume.value = 100
  }

  async function initializeWebSocket() {
    if (!isActive.value) {
      console.log('Spotify not active, skipping WebSocket connection')
      return
    }

    try {
      clearReconnectTimeout()

      if (wsConnection.value) {
        wsConnection.value.close()
        wsConnection.value = null
      }

      if (wsRetryCount.value >= MAX_RETRY_COUNT) {
        console.log('Max WebSocket retry count reached')
        return
      }

      console.log('Attempting WebSocket connection...')
      const ws = new WebSocket('ws://localhost:24879/events')
      wsConnection.value = ws

      ws.onopen = () => {
        console.log('WebSocket connected successfully')
        wsRetryCount.value = 0
        fetchInitialState()
      }

      ws.onmessage = (event) => {
        try {
          const wsData = JSON.parse(event.data)
          console.log('WebSocket event received:', wsData)

          switch (wsData.type) {
            case 'metadata':
              if (wsData.data) {
                currentTrack.value = {
                  name: wsData.data.name || '',
                  artist_names: wsData.data.artist_names || [],
                  album_cover_url: wsData.data.album_cover_url || '',
                  position: wsData.data.position || 0,
                  duration: wsData.data.duration || 0,
                }
              }
              break
            case 'playing':
              isPlaying.value = true
              break
            case 'paused':
              isPlaying.value = false
              break
            case 'not_playing':
              isPlaying.value = false
              break
            case 'seek':
              if (wsData.data) {
                currentTrack.value.position = wsData.data.position
              }
              break
            case 'volume':
              if (wsData.data) {
                volume.value = (wsData.data.value / wsData.data.max) * 100
              }
              break
          }
        } catch (error) {
          console.error('Error processing WebSocket message:', error)
        }
      }

      ws.onclose = (event) => {
        console.log('WebSocket connection closed:', event.code)
        wsConnection.value = null
        
        if (wsRetryCount.value < MAX_RETRY_COUNT && isActive.value) {
          wsRetryCount.value++
          wsReconnectTimeout = setTimeout(() => {
            initializeWebSocket()
          }, 5000)
        }
      }

      ws.onerror = (event) => {
        console.error('WebSocket error:', event)
      }
    } catch (error) {
      console.error('Error in initializeWebSocket:', error)
      if (wsRetryCount.value < MAX_RETRY_COUNT && isActive.value) {
        wsRetryCount.value++
        wsReconnectTimeout = setTimeout(() => {
          initializeWebSocket()
        }, 5000)
      }
    }
  }

  async function fetchInitialState() {
    if (!isActive.value) return

    try {
      const response = await fetch('http://localhost:24879/player')
      const data = await response.json()
      console.log('Initial state:', data)

      if (data && data.track) {
        currentTrack.value = {
          name: data.track.name || '',
          artist_names: data.track.artist_names || [],
          album_cover_url: data.track.album_cover_url || '',
          position: data.track.position || 0,
          duration: data.track.duration || 0,
        }
        isPlaying.value = !data.paused
      }

      volume.value = data?.volume ?? 100
    } catch (error) {
      console.error('Error fetching initial state:', error)
    }
  }

  async function togglePlay() {
    try {
      const endpoint = isPlaying.value ? '/player/pause' : '/player/resume'
      const response = await fetch(`http://localhost:24879${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
    } catch (error) {
      console.error('Error toggling playback:', error)
    }
  }

  async function next() {
    try {
      const response = await fetch('http://localhost:24879/player/next', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}'
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
    } catch (error) {
      console.error('Error skipping track:', error)
    }
  }

  async function previous() {
    try {
      const response = await fetch('http://localhost:24879/player/prev', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}'
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
    } catch (error) {
      console.error('Error going to previous track:', error)
    }
  }

  async function seek(position) {
    try {
      const response = await fetch('http://localhost:24879/player/seek', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position: Math.floor(position) })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
    } catch (error) {
      console.error('Error seeking position:', error)
    }
  }

  return {
    currentTrack,
    isPlaying,
    volume,
    isActive,
    initializeWebSocket,
    fetchInitialState,
    togglePlay,
    next,
    previous,
    seek,
    setSpotifyRoute,
    cleanupConnections
  }
})