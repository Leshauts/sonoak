<template>
  <IconBase :color="color" :variant="variant">
    <template v-slot="{ fill }">
      <rect width="24" height="24" fill="#0046EB" rx="6" />
      <path 
        fill-rule="evenodd" 
        d="M12.337 4.8a.562.562 0 0 0-.9.45v5.625l-3.6-2.7a.562.562 0 1 0-.675.9l3.9 2.925-3.9 2.925a.563.563 0 0 0 .676.9l3.599-2.7v5.625a.563.563 0 0 0 .9.45l4.5-3.375a.563.563 0 0 0 0-.9L12.937 12l3.9-2.925a.563.563 0 0 0 0-.9l-4.5-3.375Zm.225 6.075v-4.5l3 2.25-3 2.25Zm3 4.5-3 2.25v-4.5l3 2.25Z"
        fill="#FFFFFF"
        clip-rule="evenodd"
      />
    </template>
  </IconBase>
</template>

<script>
import IconBase from './IconBase.vue'
export default {
  name: 'BluetoothIcon',
  components: { IconBase },
}
</script>




