<template>
  <div class="view macos-view">
    <h1>MacOS</h1>
    <SnapcastStatus />
  </div>
</template>

<script>
import SnapcastStatus from '@/components/SnapcastStatus.vue'

export default {
  name: 'MacOSView',
  components: {
    SnapcastStatus
  }
}
</script>
