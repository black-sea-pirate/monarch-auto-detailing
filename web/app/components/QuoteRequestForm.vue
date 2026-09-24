<script setup lang="ts">
import { instagramLink, whatsappLink } from '~/data/contactLinks'

type QuoteForm = {
  name: string
  contact: string
  vehicle: string
  community: string
  concern: string
}

type QuoteDraft = {
  id: string
  upload_token: string
}

type SubmittedQuote = {
  id: string
  status: string
}

type ContactMethod = 'whatsapp' | 'messenger' | 'telegram' | 'viber' | 'sms' | 'email'

type ContactMethodOption = {
  id: ContactMethod
  label: string
  color: string
  inputLabel: string
  placeholder: string
  type: 'text' | 'tel' | 'email'
  autocomplete: string
  inputmode: 'text' | 'tel' | 'email'
}

const props = withDefaults(defineProps<{
  requestLabel?: string
  source?: 'website' | 'card'
}>(), {
  requestLabel: 'Photo quote request',
  source: 'website',
})

const config = useRuntimeConfig()
const submitting = ref(false)
const uploadProgress = ref(0)
const submitState = ref<'idle' | 'success' | 'error'>('idle')
const submitMessage = ref('')
const contactMethod = ref<ContactMethod>('whatsapp')
const contactValue = ref('')
const selectedNeeds = ref<string[]>([])
const concernDetails = ref('')
const photoFiles = ref<File[]>([])
const videoFiles = ref<File[]>([])

const MAX_PHOTOS = 10
const MAX_VIDEOS = 2
const MAX_PHOTO_BYTES = 12 * 1024 * 1024
const MAX_VIDEO_BYTES = 50 * 1024 * 1024
const MAX_TOTAL_BYTES = 150 * 1024 * 1024

const contactMethods: ContactMethodOption[] = [
  {
    id: 'whatsapp',
    label: 'WhatsApp',
    color: '#25d366',
    inputLabel: 'WhatsApp number',
    placeholder: '+1 403 555 0123',
    type: 'tel',
    autocomplete: 'tel',
    inputmode: 'tel',
  },
  {
    id: 'messenger',
    label: 'Messenger',
    color: '#0866ff',
    inputLabel: 'Facebook profile or Messenger username',
    placeholder: 'Profile link or username',
    type: 'text',
    autocomplete: 'off',
    inputmode: 'text',
  },
  {
    id: 'telegram',
    label: 'Telegram',
    color: '#26a5e4',
    inputLabel: 'Telegram phone or username',
    placeholder: '+1 403 555 0123 or @username',
    type: 'text',
    autocomplete: 'off',
    inputmode: 'text',
  },
  {
    id: 'viber',
    label: 'Viber',
    color: '#7360f2',
    inputLabel: 'Viber number',
    placeholder: '+1 403 555 0123',
    type: 'tel',
    autocomplete: 'tel',
    inputmode: 'tel',
  },
  {
    id: 'sms',
    label: 'SMS',
    color: '#65d46e',
    inputLabel: 'Mobile number',
    placeholder: '+1 403 555 0123',
    type: 'tel',
    autocomplete: 'tel',
    inputmode: 'tel',
  },
  {
    id: 'email',
    label: 'Email',
    color: '#e8a36a',
    inputLabel: 'Email address',
    placeholder: 'name@example.com',
    type: 'email',
    autocomplete: 'email',
    inputmode: 'email',
  },
]

const activeContactMethod = computed(
  () => contactMethods.find(method => method.id === contactMethod.value) ?? contactMethods[0]!,
)

const vehicleOptions = [
  'I’m not sure — help me choose',
  'Sedan',
  'SUV / Crossover',
  'Pickup truck',
  'Coupe',
  'Hatchback',
  'Wagon',
  'Van / Minivan',
  'Other',
]

const needOptions = [
  { id: 'maintenance', label: 'Maintenance Interior Clean' },
  { id: 'reset', label: 'Deep Interior Detail' },
  { id: 'salt', label: 'Salt & Stain Treatment' },
  { id: 'pet-hair', label: 'Pet Hair Removal' },
  { id: 'leather', label: 'Leather Cleaning & Care' },
  { id: 'extraction', label: 'Upholstery Extraction' },
]

const initialVehicle = vehicleOptions[0]!
const form = reactive<QuoteForm>({
  name: '',
  contact: '',
  vehicle: initialVehicle,
  community: '',
  concern: '',
})

const totalUploadBytes = computed(() =>
  [...photoFiles.value, ...videoFiles.value].reduce((total, file) => total + file.size, 0),
)

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / (1024 * 1024)).toFixed(bytes >= 10 * 1024 * 1024 ? 0 : 1)} MB`
}

function setFileError(message: string) {
  submitState.value = 'error'
  submitMessage.value = message
}

function addSelectedFiles(event: Event, kind: 'photo' | 'video') {
  const input = event.target as HTMLInputElement
  const incoming = Array.from(input.files ?? [])
  input.value = ''
  if (incoming.length === 0) return

  const current = kind === 'photo' ? photoFiles.value : videoFiles.value
  const maximum = kind === 'photo' ? MAX_PHOTOS : MAX_VIDEOS
  const perFileLimit = kind === 'photo' ? MAX_PHOTO_BYTES : MAX_VIDEO_BYTES
  if (current.length + incoming.length > maximum) {
    setFileError(`You can attach up to ${maximum} ${kind === 'photo' ? 'photos' : 'videos'}.`)
    return
  }

  const tooLarge = incoming.find(file => file.size > perFileLimit)
  if (tooLarge) {
    setFileError(
      `${tooLarge.name} is too large. ${kind === 'photo' ? 'Photos' : 'Videos'} must be ${formatBytes(perFileLimit)} or smaller.`,
    )
    return
  }

  const duplicateKeys = new Set(current.map(file => `${file.name}:${file.size}:${file.lastModified}`))
  const uniqueFiles = incoming.filter(
    file => !duplicateKeys.has(`${file.name}:${file.size}:${file.lastModified}`),
  )
  const nextTotal = totalUploadBytes.value + uniqueFiles.reduce((total, file) => total + file.size, 0)
  if (nextTotal > MAX_TOTAL_BYTES) {
    setFileError(`All attachments together must be ${formatBytes(MAX_TOTAL_BYTES)} or smaller.`)
    return
  }

  if (kind === 'photo') photoFiles.value = [...current, ...uniqueFiles]
  else videoFiles.value = [...current, ...uniqueFiles]
  submitState.value = 'idle'
  submitMessage.value = ''
}

function removeSelectedFile(kind: 'photo' | 'video', index: number) {
  if (kind === 'photo') photoFiles.value = photoFiles.value.filter((_, itemIndex) => itemIndex !== index)
  else videoFiles.value = videoFiles.value.filter((_, itemIndex) => itemIndex !== index)
}

function apiUrl(path: string) {
  const apiBase = String(config.public.apiBase || '').replace(/\/$/, '')
  return `${apiBase}${path}`
}

async function readApiError(response: Response, fallback: string) {
  try {
    const payload = await response.json() as { detail?: string }
    return payload.detail || fallback
  } catch {
    return fallback
  }
}

async function createQuoteDraft(): Promise<QuoteDraft> {
  const response = await fetch(apiUrl('/api/v1/quote-requests'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...form,
      contact: contactValue.value.trim(),
      contact_method: contactMethod.value,
      concern: concernDetails.value.trim(),
      requested_services: selectedNeeds.value,
      source: props.source,
    }),
  })
  if (!response.ok) {
    throw new Error(await readApiError(response, 'The request could not be started.'))
  }
  return await response.json() as QuoteDraft
}

function uploadQuoteFile(
  draft: QuoteDraft,
  kind: 'photo' | 'video',
  file: File,
  completedBytes: number,
  allBytes: number,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest()
    request.open('POST', apiUrl(`/api/v1/quote-requests/${draft.id}/uploads`))
    request.setRequestHeader('X-Upload-Token', draft.upload_token)
    request.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && allBytes > 0) {
        uploadProgress.value = Math.min(
          99,
          Math.round(((completedBytes + event.loaded) / allBytes) * 100),
        )
      }
    })
    request.addEventListener('load', () => {
      if (request.status >= 200 && request.status < 300) {
        resolve()
        return
      }
      try {
        const response = JSON.parse(request.responseText) as { detail?: string }
        reject(new Error(response.detail || 'The request could not be submitted.'))
      } catch {
        reject(new Error('The request could not be submitted.'))
      }
    })
    request.addEventListener('error', () => reject(new Error('The server could not be reached.')))
    const body = new FormData()
    body.append('kind', kind)
    body.append('upload', file, file.name)
    request.send(body)
  })
}

async function finalizeQuoteDraft(draft: QuoteDraft): Promise<SubmittedQuote> {
  const response = await fetch(apiUrl(`/api/v1/quote-requests/${draft.id}/submit`), {
    method: 'POST',
    headers: { 'X-Upload-Token': draft.upload_token },
  })
  if (!response.ok) {
    throw new Error(await readApiError(response, 'The request could not be submitted.'))
  }
  return await response.json() as SubmittedQuote
}

async function submitQuote() {
  submitState.value = 'idle'
  submitMessage.value = ''

  if (selectedNeeds.value.length === 0 && !concernDetails.value.trim()) {
    submitState.value = 'error'
    submitMessage.value = 'Choose at least one service or describe what needs attention.'
    return
  }

  submitting.value = true
  uploadProgress.value = 0
  try {
    const draft = await createQuoteDraft()
    const uploads = [
      ...photoFiles.value.map(file => ({ kind: 'photo' as const, file })),
      ...videoFiles.value.map(file => ({ kind: 'video' as const, file })),
    ]
    let completedBytes = 0
    for (const item of uploads) {
      await uploadQuoteFile(draft, item.kind, item.file, completedBytes, totalUploadBytes.value)
      completedBytes += item.file.size
      uploadProgress.value = totalUploadBytes.value > 0
        ? Math.min(99, Math.round((completedBytes / totalUploadBytes.value) * 100))
        : 0
    }
    const submitted = await finalizeQuoteDraft(draft)
    uploadProgress.value = 100
    submitState.value = 'success'
    submitMessage.value = `Request #${submitted.id.slice(0, 8).toUpperCase()} received. Your details and attachments are ready for review.`
    Object.assign(form, { name: '', contact: '', vehicle: initialVehicle, community: '', concern: '' })
    contactMethod.value = 'whatsapp'
    contactValue.value = ''
    selectedNeeds.value = []
    concernDetails.value = ''
    photoFiles.value = []
    videoFiles.value = []
  } catch (error) {
    submitState.value = 'error'
    submitMessage.value = error instanceof Error
      ? error.message
      : 'The request could not be submitted. Please try again.'
  } finally {
    submitting.value = false
    uploadProgress.value = 0
  }
}
</script>

<template>
  <form class="quote-form glass-panel" @submit.prevent="submitQuote">
    <div class="form-topline">
      <span>{{ requestLabel }}</span>
      <i>Private &amp; secure</i>
    </div>

    <fieldset class="contact-picker">
      <legend>Preferred contact</legend>
      <p>Choose where you would like to receive your quote.</p>
      <div class="contact-options">
        <label
          v-for="methodOption in contactMethods"
          :key="methodOption.id"
          class="contact-option"
          :style="`--contact-color: ${methodOption.color}`"
        >
          <input v-model="contactMethod" type="radio" name="contact-method" :value="methodOption.id">
          <span class="contact-option-card">
            <ContactMethodIcon :name="methodOption.id" />
            <strong>{{ methodOption.label }}</strong>
            <i aria-hidden="true" />
          </span>
        </label>
      </div>
    </fieldset>

    <label class="contact-detail-field" for="contact-detail">
      <span class="input-label">{{ activeContactMethod.inputLabel }}</span>
      <input
        id="contact-detail"
        v-model.trim="contactValue"
        :type="activeContactMethod.type"
        :autocomplete="activeContactMethod.autocomplete"
        :inputmode="activeContactMethod.inputmode"
        :placeholder="activeContactMethod.placeholder"
        maxlength="180"
        required
      >
    </label>

    <div class="field-row">
      <label>
        <span class="input-label">Your name</span>
        <input v-model.trim="form.name" type="text" autocomplete="name" placeholder="First and last name" required>
      </label>
      <label class="vehicle-field">
        <span class="input-label">Vehicle</span>
        <span class="select-wrap">
          <select v-model="form.vehicle" required>
            <option v-for="vehicleOption in vehicleOptions" :key="vehicleOption" :value="vehicleOption">
              {{ vehicleOption }}
            </option>
          </select>
        </span>
      </label>
    </div>

    <label>
      <span class="input-label">Service location / community</span>
      <input v-model.trim="form.community" type="text" autocomplete="address-level3" placeholder="Calgary community or postal code" required>
    </label>

    <fieldset class="needs-fieldset">
      <legend>What needs attention?</legend>
      <p>Select everything that may apply. We will confirm the right scope after reviewing the photos.</p>
      <div class="need-options">
        <label v-for="needOption in needOptions" :key="needOption.id" class="need-option">
          <input v-model="selectedNeeds" type="checkbox" :value="needOption.label">
          <span class="need-option-card">
            <i aria-hidden="true">✓</i>
            <strong>{{ needOption.label }}</strong>
          </span>
        </label>
      </div>
    </fieldset>

    <label class="concern-details">
      <span class="input-label">Anything else?</span>
      <textarea
        v-model.trim="concernDetails"
        rows="4"
        maxlength="2500"
        :required="selectedNeeds.length === 0"
        placeholder="Not sure what to choose, or need something different? Describe it here."
      />
      <small>Optional when at least one service is selected.</small>
    </label>

    <fieldset class="media-upload-fieldset">
      <legend>Photos & videos</legend>
      <p>For the clearest quote, add 4–8 daylight photos. Videos are optional.</p>

      <div class="media-upload-actions">
        <label class="media-upload-action">
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
            multiple
            @change="addSelectedFiles($event, 'photo')"
          >
          <span class="media-upload-icon" aria-hidden="true">+</span>
          <span><strong>Add photos</strong><small>{{ photoFiles.length }} / {{ MAX_PHOTOS }} · max 12 MB each</small></span>
        </label>
        <label class="media-upload-action">
          <input
            type="file"
            accept="video/mp4,video/quicktime,video/webm"
            multiple
            @change="addSelectedFiles($event, 'video')"
          >
          <span class="media-upload-icon is-video" aria-hidden="true">▶</span>
          <span><strong>Add videos</strong><small>{{ videoFiles.length }} / {{ MAX_VIDEOS }} · max 50 MB each</small></span>
        </label>
      </div>

      <div v-if="photoFiles.length || videoFiles.length" class="selected-media">
        <div class="selected-media-summary">
          <span>{{ photoFiles.length }} photo{{ photoFiles.length === 1 ? '' : 's' }} · {{ videoFiles.length }} video{{ videoFiles.length === 1 ? '' : 's' }}</span>
          <strong>{{ formatBytes(totalUploadBytes) }} / 150 MB</strong>
        </div>
        <ul>
          <li v-for="(file, index) in photoFiles" :key="`photo-${file.name}-${file.lastModified}`">
            <span class="file-kind">IMG</span>
            <span><strong>{{ file.name }}</strong><small>{{ formatBytes(file.size) }}</small></span>
            <button type="button" :aria-label="`Remove ${file.name}`" @click="removeSelectedFile('photo', index)">×</button>
          </li>
          <li v-for="(file, index) in videoFiles" :key="`video-${file.name}-${file.lastModified}`">
            <span class="file-kind is-video">VID</span>
            <span><strong>{{ file.name }}</strong><small>{{ formatBytes(file.size) }}</small></span>
            <button type="button" :aria-label="`Remove ${file.name}`" @click="removeSelectedFile('video', index)">×</button>
          </li>
        </ul>
      </div>

      <p class="upload-privacy-note">
        Photos are resized and stripped of location metadata. Files stay private and are removed 30 days after acceptance, or within 90 days if the request is not actioned.
      </p>
    </fieldset>

    <button class="button button-primary form-submit" type="submit" :disabled="submitting">
      {{ submitting ? (uploadProgress > 0 ? `Uploading ${uploadProgress}%` : 'Sending…') : 'Send request' }} <span>↗</span>
    </button>

    <p class="form-consent">
      By sending, you consent to Monarch using these details and media to prepare your quote. Telegram receives a short summary, including your vehicle type and service area, but not your name, contact details or media. Read our <NuxtLink to="/privacy">privacy policy</NuxtLink>.
    </p>

    <p v-if="submitMessage" class="form-message" :class="`is-${submitState}`" role="status">
      {{ submitMessage }}
    </p>

    <p class="form-followup-note">
      <template v-if="submitState === 'error'">Having trouble sending your request? Message us directly on</template>
      <template v-else>If you haven't heard from us within 24 hours after sending your request, message us directly on</template>
      <a :href="whatsappLink.href" target="_blank" rel="noopener noreferrer">WhatsApp</a>
      or <a :href="instagramLink.href" target="_blank" rel="noopener noreferrer">Instagram</a>.
    </p>
  </form>
</template>
