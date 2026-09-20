<script setup lang="ts">
defineProps<{
  newCount?: number
}>()
</script>

<template>
  <div class="admin-app">
    <header class="admin-header">
      <NuxtLink class="admin-brand" to="/admin" aria-label="Monarch request inbox">
        <img src="/brand/monarch-symbol-gold.svg" alt="">
        <span><strong>Monarch</strong><small>Request inbox</small></span>
      </NuxtLink>
      <NuxtLink class="admin-inbox-link" to="/admin">
        Inbox
        <span v-if="newCount">{{ newCount }}</span>
      </NuxtLink>
    </header>
    <main class="admin-main">
      <slot />
    </main>
  </div>
</template>
