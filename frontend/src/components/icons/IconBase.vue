<template>
  <svg 
    :width="computedSize" 
    :height="computedSize" 
    fill="none" 
    xmlns="http://www.w3.org/2000/svg" 
    viewBox="0 0 24 24"
  >
    <slot :fill="color"></slot>
  </svg>
</template>

<script>
export default {
  name: 'IconBase',
  props: {
    color: {
      type: String,
      default: 'currentColor'
    },
    variant: {
      type: String,
      default: 'md',
      validator: (value) => ['sm', 'md', 'lg'].includes(value)
    }
  },
  computed: {
    computedSize() {
      const sizes = {
        sm: 24,  // taille de base
        md: 32,  // taille moyenne
        lg: 48   // grande taille
      }
      return sizes[this.variant]
    }
  }
}
</script>