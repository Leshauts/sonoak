<template>
    <IconBase :color="color" :variant="variant">
      <template v-slot="{ fill }">
        <path 
          d="M5.25 15.868V8.132c0-.504.596-.804 1.041-.525l6.16 3.868a.61.61 0 0 1 0 1.05l-6.16 3.868c-.445.28-1.041-.021-1.041-.525Z" 
          :fill="fill"
        />
        <path 
          d="M12.75 15.868V8.132c0-.504.596-.804 1.041-.525l6.16 3.868a.61.61 0 0 1 0 1.05l-6.16 3.868c-.445.28-1.041-.021-1.041-.525Z" 
          :fill="fill"
        />
      </template>
    </IconBase>
  </template>
  
  <script>
  import IconBase from './IconBase.vue'
  export default {
    name: 'NextIcon',
    components: { IconBase },
    props: { color: String, variant: String }
  }
  </script>