<template>
    <IconBase :color="color" :variant="variant">
      <template v-slot="{ fill }">
        <path 
          d="M6.75 6.75A.75.75 0 0 1 7.5 6h2.25a.75.75 0 0 1 .75.75v10.5a.75.75 0 0 1-.75.75H7.5a.75.75 0 0 1-.75-.75V6.75Zm6.75 0a.75.75 0 0 1 .75-.75h2.25a.75.75 0 0 1 .75.75v10.5a.75.75 0 0 1-.75.75h-2.25a.75.75 0 0 1-.75-.75V6.75Z" 
          :fill="fill"
        />
      </template>
    </IconBase>
  </template>
  
  <script>
  import IconBase from './IconBase.vue'
  export default {
    name: 'PauseIcon',
    components: { IconBase },
    props: { color: String, variant: String }
  }
  </script>