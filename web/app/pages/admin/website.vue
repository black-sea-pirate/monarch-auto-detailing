<script setup lang="ts">
import type {
  AdminPortfolioImage,
  AdminSiteSettings,
} from '~/composables/useAdminApi'
import { cloneDefaultSiteContent, priceKeys, type PriceKey } from '~/data/siteContent'

type PriceDraft = {
  base: string | number
  discount: string | number
  discountEnabled: boolean
}

const { request } = useAdminApi()
const defaults = cloneDefaultSiteContent()
const settings = ref<AdminSiteSettings>({
  pricing: defaults.pricing,
  sections: defaults.sections,
  version: defaults.version,
  updated_at: null,
  updated_by: null,
})
const priceDrafts = reactive<Record<PriceKey, PriceDraft>>(
  Object.fromEntries(priceKeys.map(key => [key, {
    base: (defaults.pricing[key].base_price_cents / 100).toString(),
    discount: '',
    discountEnabled: false,
  }])) as Record<PriceKey, PriceDraft>,
)
const portfolio = ref<AdminPortfolioImage[]>([])
const loading = ref(true)
const saving = ref(false)
const uploading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const savedSnapshot = ref('')
const uploadCaption = ref('')
const uploadVisible = ref(true)
const uploadInput = ref<HTMLInputElement | null>(null)
const uploadAfterInput = ref<HTMLInputElement | null>(null)
const previewUrls = reactive<Record<string, string>>({})
const afterPreviewUrls = reactive<Record<string, string>>({})
const uploadingAfter = reactive<Record<string, boolean>>({})

const priceRows: { key: PriceKey, label: string, note: string }[] = [
  { key: 'maintenance', label: 'Maintenance Interior Clean', note: 'Main package' },
  { key: 'deep', label: 'Deep Interior Detail', note: 'Main package' },
  { key: 'complete', label: 'Complete Interior Reset', note: 'Main package' },
  { key: 'pet_hair', label: 'Pet Hair Removal', note: 'Add-on' },
  { key: 'extraction', label: 'Upholstery Extraction', note: 'Per seat' },
  { key: 'leather', label: 'Leather Cleaning & Care', note: 'Add-on' },
  { key: 'salt_stain', label: 'Salt & Stain Treatment', note: 'Add-on' },
  { key: 'suv_surcharge', label: 'SUV / pickup surcharge', note: 'Vehicle size' },
  { key: 'large_vehicle_surcharge', label: '3-row SUV / minivan surcharge', note: 'Vehicle size' },
]

useHead({
  title: 'Website settings · Monarch',
  meta: [{ name: 'robots', content: 'noindex, nofollow, noarchive' }],
})

function dollars(cents: number | null) {
  return cents === null ? '' : (cents / 100).toString()
}

function cents(value: string | number) {
  const amount = Number(value)
  return Number.isFinite(amount) ? Math.round(amount * 100) : 0
}

function settingsSnapshot() {
  return JSON.stringify({ sections: settings.value.sections, priceDrafts })
}

const hasUnsavedSettings = computed(() => (
  !loading.value && savedSnapshot.value !== settingsSnapshot()
))

function hydratePriceDrafts(payload: AdminSiteSettings) {
  for (const key of priceKeys) {
    const value = payload.pricing[key]!
    priceDrafts[key].base = dollars(value.base_price_cents)
    priceDrafts[key].discount = dollars(value.discount_price_cents)
    priceDrafts[key].discountEnabled = value.discount_enabled
  }
}

async function loadPreview(image: AdminPortfolioImage) {
  const loadOne = async (path: string, target: Record<string, string>) => {
    try {
      const blob = await request<Blob>(path, { responseType: 'blob' })
      const oldPreview = target[image.id]
      if (oldPreview) URL.revokeObjectURL(oldPreview)
      target[image.id] = URL.createObjectURL(blob)
    } catch {
      target[image.id] = ''
    }
  }
  await loadOne(image.url, previewUrls)
  if (image.after_url) {
    await loadOne(image.after_url, afterPreviewUrls)
  } else {
    const oldAfterPreview = afterPreviewUrls[image.id]
    if (oldAfterPreview) URL.revokeObjectURL(oldAfterPreview)
    delete afterPreviewUrls[image.id]
  }
}

async function loadPage() {
  loading.value = true
  errorMessage.value = ''
  try {
    const [loadedSettings, loadedPortfolio] = await Promise.all([
      request<AdminSiteSettings>('/api/v1/admin/site-settings'),
      request<AdminPortfolioImage[]>('/api/v1/admin/portfolio-images'),
    ])
    settings.value = loadedSettings
    portfolio.value = loadedPortfolio
    await Promise.allSettled(loadedPortfolio.map(loadPreview))
    hydratePriceDrafts(loadedSettings)
    await nextTick()
    savedSnapshot.value = settingsSnapshot()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not load website settings.'
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const pricing = Object.fromEntries(priceKeys.map((key) => {
      const discount = String(priceDrafts[key].discount ?? '').trim()
      return [key, {
        base_price_cents: cents(priceDrafts[key].base),
        discount_price_cents: discount ? cents(discount) : null,
        discount_enabled: priceDrafts[key].discountEnabled,
      }]
    }))
    const updated = await request<AdminSiteSettings>('/api/v1/admin/site-settings', {
      method: 'PUT',
      body: {
        pricing,
        sections: settings.value.sections,
        version: settings.value.version,
      },
    })
    settings.value = updated
    hydratePriceDrafts(updated)
    await nextTick()
    savedSnapshot.value = settingsSnapshot()
    successMessage.value = 'Website settings are published.'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not save website settings.'
  } finally {
    saving.value = false
  }
}

async function uploadPhoto() {
  const file = uploadInput.value?.files?.[0]
  if (!file) {
    errorMessage.value = 'Choose a photo first.'
    return
  }
  uploading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  const body = new FormData()
  body.append('image', file)
  const afterFile = uploadAfterInput.value?.files?.[0]
  if (afterFile) body.append('after_image', afterFile)
  body.append('caption', uploadCaption.value)
  body.append('is_enabled', String(uploadVisible.value))
  try {
    const created = await request<AdminPortfolioImage>('/api/v1/admin/portfolio-images', {
      method: 'POST',
      body,
    })
    portfolio.value.push(created)
    await loadPreview(created)
    uploadCaption.value = ''
    uploadVisible.value = true
    if (uploadInput.value) uploadInput.value.value = ''
    if (uploadAfterInput.value) uploadAfterInput.value.value = ''
    successMessage.value = created.after_url ? 'Before-and-after work uploaded.' : 'Photo uploaded.'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not upload the photo.'
  } finally {
    uploading.value = false
  }
}

async function uploadAfterPhoto(image: AdminPortfolioImage, event: Event) {
  const input = event.currentTarget as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  uploadingAfter[image.id] = true
  errorMessage.value = ''
  successMessage.value = ''
  const body = new FormData()
  body.append('image', file)
  try {
    const updated = await request<AdminPortfolioImage>(
      `/api/v1/admin/portfolio-images/${image.id}/after`,
      { method: 'POST', body },
    )
    const index = portfolio.value.findIndex(item => item.id === image.id)
    if (index !== -1) portfolio.value[index] = updated
    await loadPreview(updated)
    successMessage.value = image.after_url ? 'After photo replaced.' : 'After photo added.'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not upload the after photo.'
  } finally {
    input.value = ''
    uploadingAfter[image.id] = false
  }
}

async function deleteAfterPhoto(image: AdminPortfolioImage) {
  if (!window.confirm(`Remove the after photo from ${image.original_name}?`)) return
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await request<void>(`/api/v1/admin/portfolio-images/${image.id}/after`, { method: 'DELETE' })
    const oldPreview = afterPreviewUrls[image.id]
    if (oldPreview) URL.revokeObjectURL(oldPreview)
    delete afterPreviewUrls[image.id]
    image.after_original_name = null
    image.after_size_bytes = null
    image.after_url = null
    successMessage.value = 'After photo removed. The work is now shown as a regular photo.'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not remove the after photo.'
  }
}

async function savePhoto(image: AdminPortfolioImage) {
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const updated = await request<AdminPortfolioImage>(`/api/v1/admin/portfolio-images/${image.id}`, {
      method: 'PATCH',
      body: { caption: image.caption, is_enabled: image.is_enabled },
    })
    const index = portfolio.value.findIndex(item => item.id === image.id)
    if (index !== -1) portfolio.value[index] = updated
    successMessage.value = 'Photo updated.'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not update the photo.'
  }
}

async function movePhoto(image: AdminPortfolioImage, direction: 'up' | 'down') {
  errorMessage.value = ''
  try {
    portfolio.value = await request<AdminPortfolioImage[]>(
      `/api/v1/admin/portfolio-images/${image.id}/move?direction=${direction}`,
      { method: 'POST' },
    )
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not reorder the photos.'
  }
}

async function deletePhoto(image: AdminPortfolioImage) {
  if (!window.confirm(`Delete ${image.original_name}? This cannot be undone.`)) return
  errorMessage.value = ''
  try {
    await request<void>(`/api/v1/admin/portfolio-images/${image.id}`, { method: 'DELETE' })
    const oldPreview = previewUrls[image.id]
    if (oldPreview) URL.revokeObjectURL(oldPreview)
    delete previewUrls[image.id]
    const oldAfterPreview = afterPreviewUrls[image.id]
    if (oldAfterPreview) URL.revokeObjectURL(oldAfterPreview)
    delete afterPreviewUrls[image.id]
    portfolio.value = portfolio.value.filter(item => item.id !== image.id)
    successMessage.value = 'Photo deleted.'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not delete the photo.'
  }
}

onMounted(loadPage)
onBeforeUnmount(() => {
  Object.values(previewUrls).forEach((url) => {
    if (url) URL.revokeObjectURL(url)
  })
  Object.values(afterPreviewUrls).forEach((url) => {
    if (url) URL.revokeObjectURL(url)
  })
})
</script>

<template>
  <AdminShell>
    <section class="admin-page-heading admin-website-heading">
      <div>
        <p>Main website</p>
        <h1>Website settings</h1>
      </div>
      <button
        class="admin-primary-action"
        type="button"
        :disabled="loading || saving || !hasUnsavedSettings"
        @click="saveSettings"
      >
        {{ saving ? 'Publishing…' : hasUnsavedSettings ? 'Save & publish' : 'Saved' }}
      </button>
    </section>

    <p v-if="errorMessage" class="admin-alert is-error" role="alert">{{ errorMessage }}</p>
    <p v-if="successMessage" class="admin-alert is-success" role="status">{{ successMessage }}</p>
    <div v-if="loading" class="admin-empty">Loading website settings…</div>

    <template v-else>
      <section class="admin-settings-section">
        <div class="admin-settings-intro">
          <div>
            <p class="admin-card-label">Visibility</p>
            <h2>Homepage sections</h2>
          </div>
          <p>Turn a section off to hide it from the public website. Your content stays saved.</p>
        </div>
        <div class="admin-toggle-list">
          <label>
            <span><strong>Pricing</strong><small>Packages, add-ons and vehicle surcharges</small></span>
            <input v-model="settings.sections.pricing_enabled" type="checkbox">
          </label>
          <label>
            <span><strong>Portfolio</strong><small>Only visible photos will appear</small></span>
            <input v-model="settings.sections.portfolio_enabled" type="checkbox">
          </label>
          <label>
            <span><strong>Founding offer</strong><small>The 10% first-appointment banner</small></span>
            <input v-model="settings.sections.founding_offer_enabled" type="checkbox">
          </label>
        </div>
        <p
          v-if="settings.sections.portfolio_enabled && !portfolio.some(image => image.is_enabled)"
          class="admin-settings-note"
        >
          Portfolio is turned on, but it will stay hidden until at least one photo is visible.
        </p>
      </section>

      <section class="admin-settings-section">
        <div class="admin-settings-intro">
          <div>
            <p class="admin-card-label">CAD</p>
            <h2>Prices & discounts</h2>
          </div>
          <p>Enter dollar amounts. A discount only appears after its switch is turned on and the page is published.</p>
        </div>
        <div class="admin-price-table">
          <article v-for="row in priceRows" :key="row.key" class="admin-price-row">
            <div class="admin-price-name">
              <strong>{{ row.label }}</strong>
              <small>{{ row.note }}</small>
            </div>
            <label>
              <span>Regular price</span>
              <i>$</i>
              <input v-model="priceDrafts[row.key].base" type="number" min="1" step="0.01" inputmode="decimal">
            </label>
            <label>
              <span>Discount price</span>
              <i>$</i>
              <input
                v-model="priceDrafts[row.key].discount"
                type="number"
                min="1"
                step="0.01"
                inputmode="decimal"
                :disabled="!priceDrafts[row.key].discountEnabled"
              >
            </label>
            <label class="admin-discount-switch">
              <span>Discount</span>
              <input v-model="priceDrafts[row.key].discountEnabled" type="checkbox">
            </label>
          </article>
        </div>
      </section>

      <section class="admin-settings-section">
        <div class="admin-settings-intro">
          <div>
            <p class="admin-card-label">Your work</p>
            <h2>Portfolio photos</h2>
          </div>
          <p>Use a before photo on its own, or add an optional after photo to create an interactive comparison.</p>
        </div>

        <form class="admin-upload-form" @submit.prevent="uploadPhoto">
          <label class="admin-file-field">
            <span>Before / main photo</span>
            <input ref="uploadInput" type="file" accept="image/jpeg,image/png,image/webp,image/heic,image/heif">
            <small>JPG, PNG, WebP or HEIC · maximum 12 MB</small>
          </label>
          <label class="admin-file-field">
            <span>After photo <small>(optional)</small></span>
            <input ref="uploadAfterInput" type="file" accept="image/jpeg,image/png,image/webp,image/heic,image/heif">
            <small>Add it now, or attach it to the work later</small>
          </label>
          <label>
            <span>Caption <small>(optional)</small></span>
            <input v-model="uploadCaption" type="text" maxlength="240" placeholder="Example: Family SUV interior reset">
          </label>
          <label class="admin-upload-visible">
            <input v-model="uploadVisible" type="checkbox">
            Visible on the website
          </label>
          <button class="admin-primary-action" type="submit" :disabled="uploading">
            {{ uploading ? 'Uploading…' : 'Add work' }}
          </button>
        </form>

        <div v-if="portfolio.length === 0" class="admin-empty admin-portfolio-empty">
          <strong>No portfolio photos yet.</strong>
          <span>Your first upload will appear here.</span>
        </div>
        <div v-else class="admin-portfolio-list">
          <article v-for="(image, index) in portfolio" :key="image.id">
            <div class="admin-portfolio-media">
              <figure>
                <span>Before / main</span>
                <img v-if="previewUrls[image.id]" :src="previewUrls[image.id]" :alt="image.caption || image.original_name">
                <div v-else class="admin-photo-placeholder">Preview unavailable</div>
              </figure>
              <figure v-if="image.after_url">
                <span>After</span>
                <img v-if="afterPreviewUrls[image.id]" :src="afterPreviewUrls[image.id]" :alt="`After: ${image.caption || image.original_name}`">
                <div v-else class="admin-photo-placeholder">Preview unavailable</div>
              </figure>
              <div v-else class="admin-after-empty">
                <span>After</span>
                <small>Optional</small>
              </div>
            </div>
            <div class="admin-portfolio-editor">
              <div class="admin-photo-files">
                <span>
                  <strong>{{ image.original_name }}</strong>
                  <small>Before · {{ Math.max(1, Math.round(image.size_bytes / 1024)) }} KB</small>
                </span>
                <span v-if="image.after_original_name">
                  <strong>{{ image.after_original_name }}</strong>
                  <small>After · {{ Math.max(1, Math.round((image.after_size_bytes || 0) / 1024)) }} KB</small>
                </span>
              </div>
              <label>
                <span>Caption</span>
                <input v-model="image.caption" type="text" maxlength="240" placeholder="Optional caption">
              </label>
              <label class="admin-after-upload">
                <span>{{ image.after_url ? 'Replace after photo' : 'Add after photo (optional)' }}</span>
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
                  :disabled="uploadingAfter[image.id]"
                  @change="uploadAfterPhoto(image, $event)"
                >
                <small>{{ uploadingAfter[image.id] ? 'Uploading…' : 'Selecting a file uploads it immediately.' }}</small>
              </label>
              <label class="admin-upload-visible">
                <input v-model="image.is_enabled" type="checkbox">
                Visible on the website
              </label>
              <div class="admin-photo-actions">
                <button type="button" :disabled="index === 0" @click="movePhoto(image, 'up')">Move up</button>
                <button type="button" :disabled="index === portfolio.length - 1" @click="movePhoto(image, 'down')">Move down</button>
                <button type="button" @click="savePhoto(image)">Save photo</button>
                <button v-if="image.after_url" type="button" @click="deleteAfterPhoto(image)">Remove after</button>
                <button class="is-danger" type="button" @click="deletePhoto(image)">Delete</button>
              </div>
            </div>
          </article>
        </div>
      </section>
    </template>
  </AdminShell>
</template>
