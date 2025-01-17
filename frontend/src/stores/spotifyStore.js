import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSpotifyStore = defineStore('spotify', () => {
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

  function updateTrack(trackData) {
    currentTrack.value = {
      name: trackData.name,
      artist_names: trackData.artist_names,
      album_cover_url: trackData.album_cover_url,
      position: trackData.position || 0,
      duration: trackData.duration
    }
  }

  async function initializeWebSocket() {
    try {
      if (wsConnection.value) {
        wsConnection.value.close()
      }

      wsConnection.value = new WebSocket(`ws://localhost:24879/events`)
      
      wsConnection.value.onopen = () => {
        console.log('WebSocket connected')
      }

      wsConnection.value.onmessage = (event) => {
        const wsData = JSON.parse(event.data)
        console.log('WebSocket event received:', wsData)
        
        const data = wsData.data
        
        switch (wsData.type) {
          case 'metadata':
            updateTrack(data)
            break
          case 'playing':
            isPlaying.value = true
            break
          case 'paused':
            isPlaying.value = false
            break
          case 'seek':
            currentTrack.value.position = data.position
            break
          case 'not_playing':
            isPlaying.value = false
            break
        }
      }

      wsConnection.value.onclose = () => {
        console.log('WebSocket connection closed, attempting to reconnect...')
        setTimeout(() => initializeWebSocket(), 1000)
      }

      wsConnection.value.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    } catch (error) {
      console.error('Error initializing WebSocket:', error)
      setTimeout(() => initializeWebSocket(), 1000)
    }
  }

  async function fetchInitialState() {
    try {
      const response = await fetch('http://localhost:24879/status')
      const data = await response.json()
      console.log('Initial state:', data)

      isPlaying.value = !data.paused
      volume.value = data.volume

      if (data.track) {
        updateTrack(data.track)
      }
    } catch (error) {
      console.error('Error fetching initial state:', error)
    }
  }

  async function togglePlay() {
    try {
      const endpoint = isPlaying.value ? '/player/pause' : '/player/resume'
      await fetch(`http://localhost:24879${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      })
    } catch (error) {
      console.error('Error toggling playback:', error)
    }
  }

  async function next() {
    try {
      await fetch('http://localhost:24879/player/next', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      })
    } catch (error) {
      console.error('Error skipping track:', error)
    }
  }

  async function previous() {
    try {
      await fetch('http://localhost:24879/player/prev', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      })
    } catch (error) {
      console.error('Error going to previous track:', error)
    }
  }

  async function seek(position) {
    try {
      await fetch('http://localhost:24879/player/seek', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          position: position
        })
      })
    } catch (error) {
      console.error('Error seeking position:', error)
    }
  }

  return {
    currentTrack,
    isPlaying,
    volume,
    initializeWebSocket,
    fetchInitialState,
    togglePlay,
    next,
    previous,
    seek
  }
})