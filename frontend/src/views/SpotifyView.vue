<template>
  <div class="spotify-view">
    <!-- Bloc gauche - Image -->
    <div class="cover-image">
      <img src="https://cdn-images.dzcdn.net/images/cover/594754de90ec0b807229f9c985289530/0x1900-000000-80-0-0.jpg"
        alt="Album cover" />
    </div>

    <!-- Bloc droite -->
    <div class="content">
      <!-- Bouton playlist -->
      <IconButton class="playlist-button" @click="navigateToPlaylists">
        <PlaylistIcon color="var(--text-light)" variant="md" />
      </IconButton>


      <!-- Textes -->
      <div class="track-info">
        <h1>Mental</h1>
        <h2>Jazzy Bazz</h2>
      </div>

      <!-- Barre de lecture -->
      <div class="playback-bar">
        <span class="time">0:00</span>
        <div class="progress-bar">
          <div class="progress" :style="{ width: '34%' }"></div>
        </div>
        <span class="time">3:41</span>
      </div>

      <!-- Contrôleur Spotify -->
      <SpotifyController />
    </div>
  </div>
</template>

<script>
import IconButton from '../components/IconButton.vue'
import PlaylistIcon from '../components/icons/PlaylistIcon.vue'
import SpotifyController from '../components/SpotifyController.vue'
import Dock from '../components/Dock.vue'


export default {
  name: 'SpotifyView',
  components: {
    IconButton,
    PlaylistIcon,
    SpotifyController,
    Dock

  },
  methods: {
    navigateToPlaylists() {
      this.$router.push('/playlists')
    }
  }
}
</script>

<style scoped>
.spotify-view {
  width: 100%;
  height: 100svh;
  display: flex;
  gap: var(--spacing-06);
}

.cover-image {
  height: 100%;
  aspect-ratio: 1/1;
}

.cover-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: var(--spacing-05);
}

.content {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
}

.playlist-button {
  position: fixed;
  top: var(--spacing-06);
  right: var(--spacing-06);
  display:none;
}


.track-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: center;
}

.track-info h1 {
  margin-bottom: var(--spacing-04);
}

.track-info h2 {
  color: var(--text-light);
}


.playback-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-04);
  margin: var(--spacing-05)0;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background-color: var(--background-strong);
  border-radius: 6px;
}

.progress {
  height: 100%;
  background-color: var(--text);
  border-radius: 6px;
}
.time {
  width:48px;
  text-align:center;
}

@media (max-aspect-ratio: 3/2) {
  .spotify-view {
    flex-direction: column;
  }

  .cover-image {
    height: auto;
  }

  .playlist-button {
    display: none;
  }
}
</style>