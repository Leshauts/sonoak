<template>
    <IconBase :color="color" :variant="variant">
      <template v-slot="{ fill }">
        <path 
          d="M18.75 8.132v7.736c0 .504-.596.804-1.041.525l-6.16-3.868a.611.611 0 0 1 0-1.05l6.16-3.868c.445-.28 1.041.021 1.041.525Z" 
          :fill="fill"
        />
        <path 
          d="M11.25 8.132v7.736c0 .504-.596.804-1.041.525l-6.16-3.868a.611.611 0 0 1 0-1.05l6.16-3.868c.445-.28 1.041.021 1.041.525Z" 
          :fill="fill"
        />
      </template>
    </IconBase>
  </template>
  
  <script>
  import IconBase from './IconBase.vue'
  export default {
    name: 'PreviousIcon',
    components: { IconBase },
    props: { color: String, variant: String }
  }
  </script>