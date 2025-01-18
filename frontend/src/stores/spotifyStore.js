import { defineStore } from 'pinia'
import { ref } from 'vue'
import { API_BASE_URL } from '../config'

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
  const wsRetryCount = ref(0)
  const MAX_RETRY_COUNT = 10
  // Utilisation du bon chemin WebSocket avec le endpoint /events
  const WEBSOCKET_URL = 'ws://localhost:24879/events'

  let wsReconnectTimeout = null

  function clearReconnectTimeout() {
    if (wsReconnectTimeout) {
      clearTimeout(wsReconnectTimeout)
      wsReconnectTimeout = null
    }
  }

  async function initializeWebSocket() {
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

      console.log(`Attempting WebSocket connection (attempt ${wsRetryCount.value + 1}/${MAX_RETRY_COUNT})...`)
      const ws = new WebSocket(WEBSOCKET_URL)
      wsConnection.value = ws

      ws.onopen = () => {
        console.log('WebSocket connected successfully')
        wsRetryCount.value = 0
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
        console.log(`WebSocket connection closed (${event.code}): ${event.reason}`)
        wsConnection.value = null
        
        if (wsRetryCount.value < MAX_RETRY_COUNT) {
          wsRetryCount.value++
          console.log(`Scheduling reconnection attempt ${wsRetryCount.value}/${MAX_RETRY_COUNT}...`)
          wsReconnectTimeout = setTimeout(() => {
            initializeWebSocket()
          }, 2000)
        }
      }

      ws.onerror = (event) => {
        console.error('WebSocket error:', event)
      }
    } catch (error) {
      console.error('Error in initializeWebSocket:', error)
      if (wsRetryCount.value < MAX_RETRY_COUNT) {
        wsRetryCount.value++
        wsReconnectTimeout = setTimeout(() => {
          initializeWebSocket()
        }, 2000)
      }
    }
  }


  function updateTrack(trackData) {
    if (!trackData) return;
    
    currentTrack.value = {
      name: trackData.name || '',
      artist_names: trackData.artist_names || [],
      album_cover_url: trackData.album_cover_url || '',
      position: trackData.position || 0,
      duration: trackData.duration || 0,
    }
  }

  async function fetchInitialState() {
    try {
      const response = await fetch(`${API_BASE_URL}/audio/spotify/status`);
      const data = await response.json();
      console.log('Initial state:', data);

      isPlaying.value = !data.paused;
      volume.value = data.volume || 75;

      if (data.track) {
        updateTrack(data.track);
      }
    } catch (error) {
      console.error('Error fetching initial state:', error);
    }
  }

  async function togglePlay() {
    try {
      const endpoint = isPlaying.value ? '/audio/spotify/pause' : '/audio/spotify/play';
      await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
    } catch (error) {
      console.error('Error toggling playback:', error);
    }
  }

  async function next() {
    try {
      await fetch(`${API_BASE_URL}/audio/spotify/next`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
    } catch (error) {
      console.error('Error skipping track:', error);
    }
  }

  async function previous() {
    try {
      await fetch(`${API_BASE_URL}/audio/spotify/prev`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
    } catch (error) {
      console.error('Error going to previous track:', error);
    }
  }

  async function seek(position) {
    try {
      await fetch(`${API_BASE_URL}/audio/spotify/seek`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          position: position,
        }),
      });
    } catch (error) {
      console.error('Error seeking position:', error);
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
    seek,
  }
})