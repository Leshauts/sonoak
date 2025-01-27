<template>
  <div class="view bluetooth-view">
    <h1>Bluetooth</h1>
    <BluetoothDialog />
  </div>
</template>

<script>
import BluetoothDialog from '@/components/BluetoothDialog.vue'

export default {
  name: 'BluetoothView',
  components: {
    BluetoothDialog
  }
}
</script>
