<script setup lang="ts">
import type { AdminQuoteStatus } from '~/composables/useAdminApi'

const props = defineProps<{
  status: AdminQuoteStatus
}>()

const label = computed(() => ({
  new: 'New',
  viewed: 'Viewed',
  accepted: 'Accepted',
})[props.status])
</script>

<template>
  <span class="admin-status" :class="`is-${status}`">
    <i aria-hidden="true" />{{ label }}
  </span>
</template>
