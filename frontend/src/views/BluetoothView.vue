<template>
  <div class="view bluetooth-view">
    <h1>Bluetooth</h1>
    <BluetoothStatus />
  </div>
</template>

<script>
import BluetoothStatus from '@/components/BluetoothStatus.vue'

export default {
  name: 'BluetoothView',
  components: {
    BluetoothStatus
  }
}
</script>
