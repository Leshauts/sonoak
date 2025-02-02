<template>
  <div class="view bluetooth-view">
    <BluetoothStatus />
  </div>
</template>

<script>
import BluetoothStatus from '@/components/BluetoothStatus.vue'
import Logo from '@/components/logo/Sonoak.vue'

export default {
  name: 'BluetoothView',
  components: {
    BluetoothStatus,
    Logo
  }
}
</script>
