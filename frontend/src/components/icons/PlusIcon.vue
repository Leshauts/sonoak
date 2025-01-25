<template>
    <IconBase :color="color" :variant="variant">
        <template v-slot="{ fill }">
            <path fill-rule="evenodd"
                d="M12.75 3.515a.75.75 0 1 0-1.5 0v7.735H3.515a.75.75 0 1 0 0 1.5h7.735v7.735a.75.75 0 0 0 1.5 0V12.75h7.735a.75.75 0 1 0 0-1.5H12.75V3.515Z"
                :fill="fill" clip-rule="evenodd" />
        </template>
    </IconBase>
</template>

<script>
import IconBase from './IconBase.vue'
export default {
    name: 'PlusIcon',
    components: { IconBase },
    props: { color: String, variant: String }
}
</script>
