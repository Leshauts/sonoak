<template>
    <IconBase :color="color" :variant="variant">
      <template v-slot="{ fill }">
        <path 
          fill-rule="evenodd" 
          d="M8.47 5.47a.75.75 0 0 1 1.06 0l6 6a.75.75 0 0 1 0 1.06l-6 6a.75.75 0 0 1-1.06-1.06L13.94 12 8.47 6.53a.75.75 0 0 1 0-1.06Z" 
          :fill="fill" 
          clip-rule="evenodd"
        />
      </template>
    </IconBase>
  </template>
  
  <script>
  import IconBase from './IconBase.vue'
  export default {
    name: 'CaretRightIcon',
    components: { IconBase },
    props: { color: String, variant: String }
  }
  </script>