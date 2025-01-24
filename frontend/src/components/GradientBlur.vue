<!-- components/GradientBlur.vue -->
<template>
    <div class="blur-container" :class="{
        'position-top': position === 'top',
        'position-bottom': position === 'bottom'
    }">
        <div class="gradient-container">
            <!-- Gradient blur wrapper avec gradient intégré -->
            <div class="gradient-blur-wrapper" :class="{ 'visible': isVisible }" :style="{ height: height }">
                <div v-for="n in 6" :key="n" class="gradient-blur"></div>
                <!-- Overlay gradient intégré au wrapper -->
                <div class="gradient-overlay"></div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'GradientBlur',
    props: {
        isVisible: {
            type: Boolean,
            default: false
        },
        position: {
            type: String,
            default: 'bottom',
            validator: function (value) {
                return ['top', 'bottom'].includes(value)
            }
        },
        height: {
            type: String,
            default: '60%',
            validator: function (value) {
                return /^\d+(%|px)$/.test(value)
            }
        }
    }
}
</script>

<style scoped>
.blur-container {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 4;
}

.gradient-container {
    position: absolute;
    left: 0;
    bottom: 0;
    width: 100%;
    height: 100%;
    transform-origin: center center;
    transition: transform 0.4s cubic-bezier(0.785, 0.135, 0.15, 0.86);
}

.position-top .gradient-container {
    transform: rotate(180deg);
}

.gradient-blur-wrapper {
    position: absolute;
    left: 0;
    bottom: 0;
    width: 100%;
    pointer-events: none;
    z-index: 5;
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0) 0%, rgba(0, 0, 0, 0.16) 100%);
}

.gradient-blur {
    position: absolute;
    inset: 0;
}

/* Gradient overlay en haut du wrapper */
.gradient-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0) 0%, rgba(0, 0, 0, 0.16) 100%);
    pointer-events: none;
    z-index: 8;
    /* Au-dessus des blurs */
}

/* Base blur gradients */
.gradient-blur-wrapper::before {
    position: absolute;
    inset: 0;
    content: "";
    z-index: 1;
    backdrop-filter: blur(0.25px);
    -webkit-backdrop-filter: blur(0.25px);
    mask: linear-gradient(to bottom, rgba(0, 0, 0, 0) 0%, rgb(0, 0, 0) 12.5%, rgb(0, 0, 0) 25%, rgba(0, 0, 0, 0) 37.5%);
}

.gradient-blur:nth-of-type(1) {
    z-index: 2;
    backdrop-filter: blur(0.5px);
    -webkit-backdrop-filter: blur(0.5px);
    mask: linear-gradient(to bottom, rgba(0, 0, 0, 0) 12.5%, rgb(0, 0, 0) 25%, rgb(0, 0, 0) 37.5%, rgba(0, 0, 0, 0) 50%);
}

.gradient-blur:nth-of-type(2) {
    z-index: 3;
    backdrop-filter: blur(1px);
    -webkit-backdrop-filter: blur(1px);
    mask: linear-gradient(to bottom, rgba(0, 0, 0, 0) 25%, rgb(0, 0, 0) 37.5%, rgb(0, 0, 0) 50%, rgba(0, 0, 0, 0) 62.5%);
}

.gradient-blur:nth-of-type(3) {
    z-index: 4;
    backdrop-filter: blur(2px);
    -webkit-backdrop-filter: blur(2px);
    mask: linear-gradient(to bottom, rgba(0, 0, 0, 0) 37.5%, rgb(0, 0, 0) 50%, rgb(0, 0, 0) 62.5%, rgba(0, 0, 0, 0) 75%);
}

.gradient-blur:nth-of-type(4) {
    z-index: 5;
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
    mask: linear-gradient(to bottom, rgba(0, 0, 0, 0) 50%, rgb(0, 0, 0) 62.5%, rgb(0, 0, 0) 75%, rgba(0, 0, 0, 0) 87.5%);
}

.gradient-blur:nth-of-type(5) {
    z-index: 6;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    mask: linear-gradient(to bottom, rgba(0, 0, 0, 0) 62.5%, rgb(0, 0, 0) 75%, rgb(0, 0, 0) 87.5%, rgba(0, 0, 0, 0) 100%);
}

.gradient-blur:nth-of-type(6) {
    z-index: 7;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    mask: linear-gradient(to bottom, rgba(0, 0, 0, 0) 75%, rgb(0, 0, 0) 87.5%, rgb(0, 0, 0) 100%);
}

.gradient-blur-wrapper::after {
    position: absolute;
    inset: 0;
    content: "";
    z-index: 8;
    backdrop-filter: blur(32px);
    -webkit-backdrop-filter: blur(32px);
    mask: linear-gradient(to bottom, rgba(0, 0, 0, 0) 87.5%, rgb(0, 0, 0) 100%);
}
</style>