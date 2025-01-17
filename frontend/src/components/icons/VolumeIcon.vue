<template>
    <IconBase :color="color" :variant="variant">
      <template v-slot="{ fill }">
        <path 
          fill-rule="evenodd" 
          d="M14.604 3.839A.75.75 0 0 1 15 4.5v15a.75.75 0 0 1-1.166.624L7.273 15.75H3a.75.75 0 0 1-.75-.75V9A.75.75 0 0 1 3 8.25h4.273l6.561-4.374a.75.75 0 0 1 .77-.037ZM13.5 5.9 7.916 9.624a.75.75 0 0 1-.416.126H3.75v4.5H7.5a.75.75 0 0 1 .416.126l5.584 3.723V5.9Z" 
          :fill="fill" 
          clip-rule="evenodd"
        />
        <path 
          fill-rule="evenodd" 
          d="M7.5 8.25a.75.75 0 0 1 .75.75v5.9a.75.75 0 0 1-1.5 0V9a.75.75 0 0 1 .75-.75Zm9.29.908a.75.75 0 0 1 1.052.132c.591.76.908 1.724.908 2.71s-.317 1.95-.908 2.71a.75.75 0 0 1-1.184-.92A2.926 2.926 0 0 0 17.25 12c0-.67-.217-1.307-.592-1.79a.75.75 0 0 1 .132-1.052Z" 
          :fill="fill" 
          clip-rule="evenodd"
        />
        <path 
          fill-rule="evenodd" 
          d="M19.039 6.909a.75.75 0 0 1 1.052.13C21.166 8.416 21.75 10.183 21.75 12c0 1.817-.584 3.584-1.659 4.962a.75.75 0 0 1-1.182-.924c.857-1.097 1.341-2.534 1.341-4.038 0-1.503-.484-2.94-1.341-4.039a.75.75 0 0 1 .13-1.052Z" 
          :fill="fill" 
          clip-rule="evenodd"
        />
      </template>
    </IconBase>
  </template>
  
  <script>
  import IconBase from './IconBase.vue'
  export default {
    name: 'SoundIcon',
    components: { IconBase },
    props: { color: String, variant: String }
  }
  </script>