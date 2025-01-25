<template>
    <IconBase :color="color" :variant="variant">
        <template v-slot="{ fill }">
            <path fill-rule="evenodd"
                d="M21.235 12a.75.75 0 0 1-.75.75H3.515a.75.75 0 1 1 0-1.5h16.97a.75.75 0 0 1 .75.75Z" :fill="fill"
                clip-rule="evenodd" />
        </template>
    </IconBase>
</template>

<script>
import IconBase from './IconBase.vue'
export default {
    name: 'LessIcon',
    components: { IconBase },
    props: { color: String, variant: String }
}
</script>
