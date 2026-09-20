<script setup lang="ts">
import type { AdminQuoteDetail } from '~/composables/useAdminApi'

const route = useRoute()
const router = useRouter()
const { request } = useAdminApi()
const quote = ref<AdminQuoteDetail | null>(null)
const loading = ref(true)
const working = ref(false)
const errorMessage = ref('')
const copied = ref(false)

useHead({
  title: 'Request · Monarch',
  meta: [{ name: 'robots', content: 'noindex, nofollow, noarchive' }],
})

function formatDate(value: string | null) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('en-CA', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const contactHref = computed(() => {
  const current = quote.value
  if (!current) return ''
  const value = current.contact.trim()
  const digits = value.replace(/\D/g, '')
  switch (current.contact_method) {
    case 'email': return `mailto:${encodeURIComponent(value)}`
    case 'sms': return digits ? `sms:+${digits}` : ''
    case 'whatsapp': return digits ? `https://wa.me/${digits}` : ''
    case 'telegram': {
      const username = value.replace(/^@/, '')
      return /^[A-Za-z0-9_]{5,32}$/.test(username) ? `https://t.me/${username}` : ''
    }
    case 'messenger': {
      if (/^https:\/\//i.test(value)) return value
      const username = value.replace(/^@/, '')
      return username ? `https://m.me/${encodeURIComponent(username)}` : ''
    }
    case 'viber': return digits ? `viber://chat?number=%2B${digits}` : ''
    default: return ''
  }
})

async function loadQuote() {
  loading.value = true
  errorMessage.value = ''
  try {
    const id = String(route.params.id)
    const loaded = await request<AdminQuoteDetail>(`/api/v1/admin/quote-requests/${id}`)
    quote.value = loaded
    if (loaded.status === 'new') {
      await request(`/api/v1/admin/quote-requests/${id}/view`, { method: 'POST' })
      quote.value.status = 'viewed'
      quote.value.viewed_at = new Date().toISOString()
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not load the request.'
  } finally {
    loading.value = false
  }
}

async function acceptQuote() {
  if (!quote.value || working.value) return
  working.value = true
  errorMessage.value = ''
  try {
    await request(`/api/v1/admin/quote-requests/${quote.value.id}/accept`, { method: 'POST' })
    quote.value.status = 'accepted'
    quote.value.accepted_at = new Date().toISOString()
    const purgeDate = new Date()
    purgeDate.setDate(purgeDate.getDate() + 30)
    quote.value.purge_after = purgeDate.toISOString()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not accept the request.'
  } finally {
    working.value = false
  }
}

async function markUnread() {
  if (!quote.value || working.value) return
  working.value = true
  try {
    await request(`/api/v1/admin/quote-requests/${quote.value.id}/unread`, { method: 'POST' })
    quote.value.status = 'new'
    quote.value.viewed_at = null
    await router.push('/admin')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not mark the request unread.'
  } finally {
    working.value = false
  }
}

async function deleteQuote() {
  if (!quote.value || working.value) return
  const confirmed = window.confirm(
    `Delete request #${quote.value.number}? Contact details and all media will be removed immediately.`,
  )
  if (!confirmed) return
  working.value = true
  try {
    await request(`/api/v1/admin/quote-requests/${quote.value.id}`, { method: 'DELETE' })
    await router.push('/admin')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not delete the request.'
  } finally {
    working.value = false
  }
}

async function copyContact() {
  if (!quote.value) return
  await navigator.clipboard.writeText(quote.value.contact)
  copied.value = true
  window.setTimeout(() => { copied.value = false }, 1600)
}

onMounted(loadQuote)
</script>

<template>
  <AdminShell>
    <NuxtLink class="admin-back" to="/admin">← Back to inbox</NuxtLink>

    <p v-if="errorMessage" class="admin-alert is-error" role="alert">{{ errorMessage }}</p>
    <div v-if="loading" class="admin-empty">Loading request…</div>

    <article v-else-if="quote" class="admin-request-detail">
      <header class="admin-detail-heading">
        <div>
          <AdminStatusBadge :status="quote.status" />
          <p>#{{ quote.number }} · {{ formatDate(quote.created_at) }}</p>
          <h1>{{ quote.name }}</h1>
        </div>
        <button
          v-if="quote.status !== 'accepted'"
          class="admin-primary-action"
          type="button"
          :disabled="working"
          @click="acceptQuote"
        >
          Accept request
        </button>
      </header>

      <section class="admin-detail-grid">
        <div class="admin-detail-card admin-contact-card">
          <span class="admin-card-label">Preferred contact · {{ quote.contact_method }}</span>
          <strong>{{ quote.contact }}</strong>
          <div class="admin-inline-actions">
            <a v-if="contactHref" :href="contactHref" target="_blank" rel="noopener noreferrer">Open contact</a>
            <button type="button" @click="copyContact">{{ copied ? 'Copied' : 'Copy' }}</button>
          </div>
        </div>
        <div class="admin-detail-card">
          <span class="admin-card-label">Vehicle</span>
          <strong>{{ quote.vehicle }}</strong>
          <small>{{ quote.community }}</small>
        </div>
        <div class="admin-detail-card">
          <span class="admin-card-label">Requested services</span>
          <div class="admin-service-tags">
            <span v-for="service in quote.requested_services" :key="service">{{ service }}</span>
            <span v-if="quote.requested_services.length === 0">Custom request</span>
          </div>
        </div>
        <div class="admin-detail-card">
          <span class="admin-card-label">Telegram notification</span>
          <strong>{{ quote.delivery.delivered ? 'Delivered' : 'Pending' }}</strong>
          <small>{{ quote.delivery.attempts }} attempt{{ quote.delivery.attempts === 1 ? '' : 's' }}</small>
          <p v-if="quote.delivery.last_error" class="admin-technical-error">{{ quote.delivery.last_error }}</p>
        </div>
      </section>

      <section v-if="quote.concern" class="admin-detail-section">
        <span class="admin-card-label">Customer details</span>
        <p class="admin-customer-message">{{ quote.concern }}</p>
      </section>

      <section class="admin-detail-section">
        <div class="admin-section-heading">
          <div>
            <span class="admin-card-label">Private media</span>
            <h2>{{ quote.uploads.length }} attachment{{ quote.uploads.length === 1 ? '' : 's' }}</h2>
          </div>
          <span>{{ formatBytes(quote.upload_bytes) }}</span>
        </div>
        <div v-if="quote.uploads.length" class="admin-media-grid">
          <figure v-for="upload in quote.uploads" :key="upload.id" class="admin-media-item">
            <img v-if="upload.kind === 'photo'" :src="upload.url" :alt="upload.original_name" loading="lazy">
            <video v-else :src="upload.url" controls preload="metadata" />
            <figcaption>
              <span>{{ upload.original_name }}</span>
              <small>{{ formatBytes(upload.size_bytes) }}</small>
            </figcaption>
          </figure>
        </div>
        <p v-else class="admin-muted">No media was attached.</p>
      </section>

      <section v-if="quote.status === 'accepted'" class="admin-retention-note">
        Accepted {{ formatDate(quote.accepted_at) }}. Personal data and media will be removed after
        {{ formatDate(quote.purge_after) }}.
      </section>

      <footer class="admin-detail-actions">
        <button
          v-if="quote.status !== 'accepted'"
          type="button"
          :disabled="working"
          @click="markUnread"
        >
          Mark unread
        </button>
        <button class="is-danger" type="button" :disabled="working" @click="deleteQuote">
          Delete request
        </button>
      </footer>
    </article>
  </AdminShell>
</template>
