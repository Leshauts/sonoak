<template>
  <IconBase :color="color" :variant="variant" class="animated-icon">
    <template v-slot="{ fill }">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">
        <path 
          class="shape1"
          :fill="fill"
          d="M12.149 17.838c1.099-1.899 3.715-2.662 6.979-2.333l3.37 5.851H11.795c-.32-1.309-.224-2.518.354-3.518Z"
        />
        <path 
          class="shape2"
          :fill="fill"
          d="M8.763 14.582c1.113 1.924.986 4.343-.124 6.773l-7.14.001 5.157-8.88c.883.531 1.603 1.233 2.107 2.106Z"
        />
        <path 
          class="shape3"
          :fill="fill"
          d="M14.09 13.714c1.204 0 2.345-.399 3.365-1.112l-5.412-9.399-3.84 6.609c1.443 2.394 3.546 3.902 5.886 3.902h.001Z"
        />
      </svg>
    </template>
  </IconBase>
</template>

<script>
import IconBase from "./IconBase.vue";

export default {
  name: "AnimatedIcon",
  components: { IconBase },
  props: { color: String, variant: String },
};
</script>

<style scoped>
.animated-icon .shape1 {
  animation: cycle-opacity-1 3s infinite linear;
}

.animated-icon .shape2 {
  animation: cycle-opacity-2 3s infinite linear;
}

.animated-icon .shape3 {
  animation: cycle-opacity-3 3s infinite linear;
}

@keyframes cycle-opacity-1 {
  0% { opacity: 1; }
  33% { opacity: 0.48; }
  66% { opacity: 0.24; }
  100% { opacity: 1; }
}
@keyframes cycle-opacity-2 {
  0% { opacity: 0.48; }
  33% { opacity: 0.24; }
  66% { opacity: 0; }
  100% { opacity: 0.48; }
}
@keyframes cycle-opacity-3 {
  0% { opacity: 0.24; }
  33% { opacity: 0; }
  66% { opacity: 0.48; }
  100% { opacity: 0.48; }
}
</style>