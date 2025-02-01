<!-- ApiDebugger.vue -->
<template>
    <div class="api-debugger">
      <h3>API Debug Info</h3>
      
      <div v-if="error" class="error">
        Erreur: {{ error }}
      </div>
      
      <div class="endpoint-info">
        <h4>Status Endpoint (/api/spotify/status)</h4>
        <pre class="response">{{ status ? JSON.stringify(status, null, 2) : 'Chargement...' }}</pre>
      </div>
  
      <div class="endpoint-info">
        <h4>Playback Endpoint (/api/spotify/playback)</h4>
        <pre class="response">{{ playback ? JSON.stringify(playback, null, 2) : 'Chargement...' }}</pre>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'ApiDebugger',
    data() {
      return {
        status: null,
        playback: null,
        error: null
      }
    },
    async created() {
      await this.testEndpoints()
    },
    methods: {
      async testEndpoints() {
        try {
          // Test de l'endpoint status
          const statusRes = await fetch('/api/spotify/status')
          const statusText = await statusRes.text()
          this.status = {
            status: statusRes.status,
            headers: Object.fromEntries(statusRes.headers.entries()),
            body: this.tryParseJson(statusText)
          }
  
          // Test de l'endpoint playback
          const playbackRes = await fetch('/api/spotify/playback')
          const playbackText = await playbackRes.text()
          this.playback = {
            status: playbackRes.status,
            headers: Object.fromEntries(playbackRes.headers.entries()),
            body: this.tryParseJson(playbackText)
          }
        } catch (err) {
          this.error = err.message
        }
      },
      tryParseJson(text) {
        try {
          return JSON.parse(text)
        } catch (e) {
          return {
            error: 'Invalid JSON',
            rawText: text.substring(0, 500) + (text.length > 500 ? '...' : '')
          }
        }
      }
    }
  }
  </script>
  
  <style scoped>
  .api-debugger {
    margin: 20px;
    padding: 20px;
    border: 1px solid #ddd;
    border-radius: 8px;
    background: var(--background);
  }
  
  .error {
    margin: 10px 0;
    padding: 10px;
    background-color: rgba(255, 0, 0, 0.1);
    border: 1px solid rgba(255, 0, 0, 0.3);
    border-radius: 4px;
    color: #d00;
  }
  
  .endpoint-info {
    margin: 15px 0;
  }
  
  .endpoint-info h4 {
    margin-bottom: 8px;
    color: var(--text-light);
  }
  
  .response {
    padding: 10px;
    background-color: var(--background-strong);
    border-radius: 4px;
    overflow-x: auto;
    white-space: pre-wrap;
    font-family: monospace;
    font-size: 14px;
  }
  </style>