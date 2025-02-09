<template>
  <div class="bluetooth-view">
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