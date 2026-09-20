<script setup lang="ts">
import type { AdminQuoteList, AdminQuoteStatus } from '~/composables/useAdminApi'

type FilterState = 'all' | AdminQuoteStatus

const { request } = useAdminApi()
const result = ref<AdminQuoteList>({ items: [], total: 0, new_count: 0 })
const activeFilter = ref<FilterState>('all')
const search = ref('')
const loading = ref(true)
const errorMessage = ref('')

const filters: { value: FilterState, label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'new', label: 'New' },
  { value: 'viewed', label: 'Viewed' },
  { value: 'accepted', label: 'Accepted' },
]

useHead({
  title: 'Request inbox · Monarch',
  meta: [{ name: 'robots', content: 'noindex, nofollow, noarchive' }],
})

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-CA', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

async function loadQuotes() {
  loading.value = true
  errorMessage.value = ''
  try {
    const params = new URLSearchParams({ state: activeFilter.value })
    if (search.value.trim()) params.set('search', search.value.trim())
    result.value = await request<AdminQuoteList>(`/api/v1/admin/quote-requests?${params}`)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not load requests.'
  } finally {
    loading.value = false
  }
}

async function setFilter(value: FilterState) {
  activeFilter.value = value
  await loadQuotes()
}

onMounted(loadQuotes)
</script>

<template>
  <AdminShell :new-count="result.new_count">
    <section class="admin-page-heading">
      <div>
        <p>Secure intake</p>
        <h1>Requests</h1>
      </div>
      <button class="admin-icon-button" type="button" :disabled="loading" @click="loadQuotes">
        Refresh
      </button>
    </section>

    <form class="admin-search" role="search" @submit.prevent="loadQuotes">
      <input v-model.trim="search" type="search" placeholder="Search name, contact, vehicle or area">
      <button type="submit">Search</button>
    </form>

    <nav class="admin-filters" aria-label="Request status">
      <button
        v-for="filter in filters"
        :key="filter.value"
        type="button"
        :class="{ 'is-active': activeFilter === filter.value }"
        @click="setFilter(filter.value)"
      >
        {{ filter.label }}
        <span v-if="filter.value === 'new' && result.new_count">{{ result.new_count }}</span>
      </button>
    </nav>

    <p v-if="errorMessage" class="admin-alert is-error" role="alert">{{ errorMessage }}</p>
    <div v-else-if="loading" class="admin-empty">Loading requests…</div>
    <div v-else-if="result.items.length === 0" class="admin-empty">
      <strong>No requests here.</strong>
      <span>New quote requests will appear automatically.</span>
    </div>

    <div v-else class="admin-request-list">
      <NuxtLink
        v-for="quote in result.items"
        :key="quote.id"
        :to="`/admin/requests/${quote.id}`"
        class="admin-request-card"
        :class="{ 'is-new': quote.status === 'new' }"
      >
        <div class="admin-request-card-top">
          <AdminStatusBadge :status="quote.status" />
          <time :datetime="quote.created_at">{{ formatDate(quote.created_at) }}</time>
        </div>
        <h2>{{ quote.name }}</h2>
        <p>{{ quote.vehicle }} · {{ quote.community }}</p>
        <div class="admin-service-tags">
          <span v-for="service in quote.requested_services" :key="service">{{ service }}</span>
          <span v-if="quote.requested_services.length === 0">Custom request</span>
        </div>
        <footer>
          <span>#{{ quote.number }}</span>
          <span>{{ quote.photo_count }} photos · {{ quote.video_count }} videos</span>
          <span v-if="!quote.notification_delivered" class="admin-delivery-warning">Telegram pending</span>
        </footer>
      </NuxtLink>
    </div>
  </AdminShell>
</template>
