export type AdminQuoteStatus = 'new' | 'viewed' | 'accepted'

export type AdminQuoteListItem = {
  id: string
  number: string
  name: string
  vehicle: string
  community: string
  requested_services: string[]
  status: AdminQuoteStatus
  photo_count: number
  video_count: number
  created_at: string
  viewed_at: string | null
  accepted_at: string | null
  notification_delivered: boolean
}

export type AdminQuoteUpload = {
  id: string
  kind: 'photo' | 'video'
  original_name: string
  content_type: string
  size_bytes: number
  url: string
}

export type AdminQuoteDetail = AdminQuoteListItem & {
  contact_method: string
  contact: string
  concern: string
  source: string
  upload_bytes: number
  purge_after: string | null
  uploads: AdminQuoteUpload[]
  delivery: {
    delivered: boolean
    attempts: number
    last_error: string | null
    last_attempt_at: string | null
  }
}

export type AdminQuoteList = {
  items: AdminQuoteListItem[]
  total: number
  new_count: number
}

export type AdminPriceSetting = {
  base_price_cents: number
  discount_price_cents: number | null
  discount_enabled: boolean
}

export type AdminSiteSettings = {
  pricing: Record<string, AdminPriceSetting>
  sections: {
    pricing_enabled: boolean
    portfolio_enabled: boolean
    founding_offer_enabled: boolean
  }
  version: number
  updated_at: string | null
  updated_by: string | null
}

export type AdminPortfolioImage = {
  id: string
  original_name: string
  after_original_name: string | null
  caption: string | null
  sort_order: number
  is_enabled: boolean
  size_bytes: number
  after_size_bytes: number | null
  url: string
  after_url: string | null
  created_at: string
}

export function useAdminApi() {
  const config = useRuntimeConfig()
  const apiBase = String(config.public.apiBase || '').replace(/\/$/, '')
  const devToken = String(config.public.adminDevToken || '')

  async function request<T>(path: string, options: Parameters<typeof $fetch<T>>[1] = {}) {
    try {
      return await $fetch<T>(`${apiBase}${path}`, {
        credentials: 'include',
        ...options,
        headers: {
          Accept: 'application/json',
          ...(devToken ? { 'X-Admin-Dev-Token': devToken } : {}),
          ...options.headers,
        },
      })
    } catch (error: unknown) {
      const payload = error as {
        data?: { detail?: string | { msg?: string }[] }
        message?: string
      }
      const detail = payload.data?.detail
      const detailMessage = typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map(item => item.msg).filter(Boolean).join(' ')
          : ''
      throw new Error(detailMessage || payload.message || 'The admin request failed.')
    }
  }

  function mediaUrl(path: string) {
    return path.startsWith('http') ? path : `${apiBase}${path}`
  }

  return { request, mediaUrl }
}
