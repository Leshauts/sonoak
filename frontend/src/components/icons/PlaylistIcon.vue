<template>
  <IconBase :color="color" :variant="variant">
    <template v-slot="{ fill }">
      <path 
        fill-rule="evenodd" 
        d="M15.75 19.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Zm0 1.5a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" 
        :fill="fill" 
        clip-rule="evenodd"
      />
      <path 
        fill-rule="evenodd" 
        d="M17.538 11.409a.75.75 0 0 1 .644-.137l3 .75a.75.75 0 0 1-.364 1.456l-2.068-.517V18a.75.75 0 0 1-1.5 0v-6a.75.75 0 0 1 .288-.591ZM2.25 6A.75.75 0 0 1 3 5.25h18a.75.75 0 0 1 0 1.5H3A.75.75 0 0 1 2.25 6Zm0 6a.75.75 0 0 1 .75-.75h12a.75.75 0 0 1 0 1.5H3a.75.75 0 0 1-.75-.75Zm0 6a.75.75 0 0 1 .75-.75h7.5a.75.75 0 0 1 0 1.5H3a.75.75 0 0 1-.75-.75Z" 
        :fill="fill" 
        clip-rule="evenodd"
      />
    </template>
  </IconBase>
</template>

<script>
import IconBase from './IconBase.vue'
export default {
  name: 'PlaylistIcon',
  components: { IconBase },
  props: { color: String, variant: String }
}
</script>