<template>
    <button 
      class="icon-button" 
      :class="{ 'icon-button--active': active }"
      @click="$emit('click')"
    >
      <slot></slot>
    </button>
  </template>
  
  <script>
  export default {
    name: 'IconButton',
    props: {
      active: {
        type: Boolean,
        default: false
      }
    }
  }
  </script>
  
  <style scoped>
  .icon-button {
    background-color: var(--background);
    border: none;
    border-radius: 16px;
    padding: var(--spacing-02);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: opacity 0.2s;
    line-height: 0px;
  }
  
  .icon-button:hover {
    opacity: 0.7;
  }
  
  .icon-button--active {
    background-color: var(--background-strong);
  }
  </style>