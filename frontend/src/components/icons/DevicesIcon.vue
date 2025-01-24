<template>
    <IconBase :color="color" :variant="variant">
      <template v-slot="{ fill }">
        <path 
          fill-rule="evenodd" 
          d="M9.75 5.25A2.25 2.25 0 0 1 12 3h6.75A2.25 2.25 0 0 1 21 5.25v13.5A2.25 2.25 0 0 1 18.75 21H12a2.25 2.25 0 0 1-2.25-2.25V5.25ZM12 4.5a.75.75 0 0 0-.75.75v13.5c0 .414.336.75.75.75h6.75a.75.75 0 0 0 .75-.75V5.25a.75.75 0 0 0-.75-.75H12Z" 
          :fill="fill" 
          clip-rule="evenodd"
        />
        <path 
          d="M18 14.625a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0ZM8.25 15c0 .414-.345.762-.736.627a2.25 2.25 0 0 1 0-4.254c.391-.135.736.213.736.627v3Zm8.25-6.375a1.125 1.125 0 1 1-2.25 0 1.125 1.125 0 0 1 2.25 0Z" 
          :fill="fill"
        />
        <path 
          fill-rule="evenodd" 
          d="M5.25 6.75a.75.75 0 0 0-.75.75v9c0 .414.336.75.75.75H7.5a.75.75 0 0 1 0 1.5H5.25A2.25 2.25 0 0 1 3 16.5v-9a2.25 2.25 0 0 1 2.25-2.25H7.5a.75.75 0 0 1 0 1.5H5.25Z" 
          :fill="fill" 
          clip-rule="evenodd"
        />
      </template>
    </IconBase>
  </template>
  
  <script>
  import IconBase from './IconBase.vue'
  export default {
    name: 'DevicesIcon',
    components: { IconBase },
    props: { color: String, variant: String }
  }
  </script>