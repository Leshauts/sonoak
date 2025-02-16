<!-- Sonoak.vue -->
<template>
  <div class="w-full">
    <div 
      :class="[
        'logo-container',
        `logo--${computedLogoState}`
      ]"
    >
    <svg
        :class="svgClass"
        xmlns="http://www.w3.org/2000/svg"
        :width="width"
        :height="height"
        :fill="currentColor"
        viewBox="0 0 131 32"
      >
        <path
          :fill="currentColor"
          d="M16.199 23.784c1.465-2.532 4.953-3.55 9.305-3.11l4.493 7.8h-14.27c-.427-1.745-.3-3.357.472-4.69Z"
        />
        <path
          :class="pathClass"
          d="M11.684 19.443c1.484 2.565 1.315 5.79-.165 9.03l-9.52.002 6.876-11.84c1.177.708 2.137 1.644 2.81 2.808h-.001Z"
          opacity=".7"
        />
        <path
          :class="pathClass"
          d="M18.788 18.285c1.604 0 3.127-.532 4.485-1.482L16.058 4.27l-5.12 8.812c1.923 3.192 4.727 5.202 7.847 5.202l.003.001Z"
          opacity=".34"
        />
        <path
          :class="pathClass"
          fill-rule="evenodd"
          d="M55.936 20.485c0-4.389-3.182-5.294-7.378-6.364l-.271-.068c-2.593-.645-4.31-1.073-4.31-3.141 0-1.454 1.399-2.331 3.73-2.331 2.716 0 4.142 1.206 4.444 3.483h3.264c-.274-4.032-3.401-6.281-7.708-6.281-4.278 0-6.966 1.947-6.966 5.43 0 3.731 3.318 4.91 6.39 5.678 3.868.96 5.541 1.4 5.541 3.73 0 1.51-1.125 2.798-4.032 2.798-3.51 0-5.211-1.645-5.376-4.141H40c.192 4.443 3.84 6.94 8.64 6.94 4.937 0 7.296-2.607 7.296-5.733Zm65.097-14.29h-2.88v19.61h2.88v-5.074l1.948-1.837 4.416 6.912h3.456L124.956 17l5.321-5.211h-3.539l-5.705 5.623V6.194v.001Zm-11.312 7.487c1.92 0 2.523.768 2.523 1.783 0 1.344-1.316 1.618-3.483 2.03-3.511.686-5.787 1.646-5.787 4.718 0 2.358 1.755 4.004 4.608 4.004 2.166 0 3.757-.85 4.635-2.084h.055c.274 1.371.987 1.92 2.523 1.92a4.33 4.33 0 0 0 1.673-.302v-1.372c-1.124.11-1.344-.411-1.344-1.398v-6.666c0-3.73-2.304-4.91-5.403-4.91-4.224 0-5.952 2.113-6.089 4.8h2.798c.137-1.81.987-2.523 3.291-2.523Zm2.523 6.803c0 2.276-1.645 3.456-4.032 3.456-1.563 0-2.331-.714-2.331-2.003 0-1.426 1.042-2.112 3.429-2.633 1.344-.274 2.468-.603 2.934-.932v2.112ZM94.73 26.217c-4.389 0-7.05-3.044-7.05-7.406 0-4.36 2.661-7.405 7.05-7.405 4.388 0 7.049 3.044 7.049 7.405 0 4.362-2.66 7.406-7.05 7.406h.001Zm0-2.359c2.743 0 4.169-2.167 4.169-5.047 0-2.907-1.426-5.046-4.17-5.046-2.742 0-4.168 2.139-4.168 5.046 0 2.88 1.426 5.047 4.169 5.047Zm-8.942-7.735c0-3.209-2.057-4.717-4.663-4.717-2.414 0-3.868 1.097-4.608 2.194h-.055v-1.81h-2.88v14.016h2.88v-8.53c0-2.085 1.426-3.43 3.648-3.43 1.975 0 2.77 1.208 2.77 3.1v8.86h2.908v-9.683ZM64.542 26.217c-4.388 0-7.049-3.044-7.049-7.406 0-4.36 2.66-7.405 7.05-7.405 4.388 0 7.048 3.044 7.048 7.405 0 4.362-2.66 7.406-7.049 7.406Zm0-2.359c2.743 0 4.17-2.167 4.17-5.047 0-2.907-1.427-5.046-4.17-5.046s-4.169 2.139-4.169 5.046c0 2.88 1.425 5.047 4.169 5.047Z"
          clip-rule="evenodd"
        />
      </svg>
    </div>
  </div>
</template>

<script>
import { useSpotifyStore } from '@/stores/spotify'
import { useAudioStore } from '@/stores/audio'
import { computed } from 'vue'

export default {
  name: 'Sonoak',
  props: {
    state: {
      type: String,
      default: 'intro',
      validator: (value) => ['intro', 'minified', 'hidden'].includes(value)
    },
    color: {
      type: String,
      default: 'text-light',
      validator: (value) => ['text', 'text-light'].includes(value)
    }
  },
  setup(props) {
    const spotifyStore = useSpotifyStore()
    const audioStore = useAudioStore()

    const computedLogoState = computed(() => {
      // Si la source actuelle n'est pas Spotify, utiliser l'état normal
      if (audioStore.currentSource !== 'spotify') {
        return props.state
      }

      // Pour Spotify, montrer le logo sauf si un player est actif
      return spotifyStore.playerActive ? 'hidden' : props.state
    })

    return {
      computedLogoState,
      width: computed(() => props.state === 'intro' ? 196 : 131),
      height: computed(() => props.state === 'intro' ? 48 : 32),
      svgClass: computed(() => ({
        'transition-all': true,
        'duration-500': true
      })),
      pathClass: computed(() => ({
        'transition-opacity': true,
        'duration-500': true
      })),
      currentColor: computed(() => props.color === 'text' ? 'var(--text)' : 'var(--text-light)')
    }
  }
}
</script>

<style scoped>
.logo-container {
  position: fixed;
  left: 50%;
  display: flex;
  justify-content: center;
  width: fit-content;
  transform: translateX(-50%);
  will-change: transform, opacity;
  transition: all 600ms cubic-bezier(0.85, 0, 0.15, 1);
}

.logo--intro {
  top: 50vh;
  transform: translate(-50%, -50%);
  opacity: 1;
}

.logo--minified {
  top: 32px;
  transform: translateX(-50%);
  opacity: 1;
}

.logo--hidden {
  top: -32px;
  transform: translateX(-50%);
  opacity: 0;
}
</style>