<template>
    <IconBase :color="color" :variant="variant">
      <template v-slot="{ fill }">
        <path 
          d="M7.5 17.157V6.843c0-.672.775-1.073 1.354-.7l8.008 5.157a.825.825 0 0 1 0 1.4l-8.008 5.157c-.579.373-1.354-.028-1.354-.7Z" 
          :fill="fill"
        />
      </template>
    </IconBase>
  </template>
  
  <script>
  import IconBase from './IconBase.vue'
  export default {
    name: 'PlayIcon',
    components: { IconBase },
    props: { color: String, variant: String }
  }
  </script>