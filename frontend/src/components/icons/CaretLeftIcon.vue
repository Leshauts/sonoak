<template>
    <IconBase :color="color" :variant="variant">
      <template v-slot="{ fill }">
        <path 
          fill-rule="evenodd" 
          d="M15.53 18.53a.75.75 0 0 1-1.06 0l-6-6a.75.75 0 0 1 0-1.06l6-6a.75.75 0 1 1 1.06 1.06L10.06 12l5.47 5.47a.75.75 0 0 1 0 1.06Z" 
          :fill="fill" 
          clip-rule="evenodd"
        />
      </template>
    </IconBase>
  </template>
  
  <script>
  import IconBase from './IconBase.vue'
  export default {
    name: 'CaretLeftIcon',
    components: { IconBase },
    props: { color: String, variant: String }
  }
  </script>