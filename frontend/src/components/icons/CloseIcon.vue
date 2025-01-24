<template>
    <IconBase :color="color" :variant="variant">
      <template v-slot="{ fill }">
        <path 
          fill-rule="evenodd" 
          d="M5.47 5.47a.75.75 0 0 1 1.06 0l12 12a.75.75 0 1 1-1.06 1.06l-12-12a.75.75 0 0 1 0-1.06Z" 
          :fill="fill" 
          clip-rule="evenodd"
        />
        <path 
          fill-rule="evenodd" 
          d="M18.53 5.47a.75.75 0 0 1 0 1.06l-12 12a.75.75 0 0 1-1.06-1.06l12-12a.75.75 0 0 1 1.06 0Z" 
          :fill="fill" 
          clip-rule="evenodd"
        />
      </template>
    </IconBase>
  </template>
  
  <script>
  import IconBase from './IconBase.vue'
  export default {
    name: 'CloseIcon',
    components: { IconBase },
    props: { color: String, variant: String }
  }
  </script>