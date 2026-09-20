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

export function useAdminApi() {
  async function request<T>(path: string, options: Parameters<typeof $fetch<T>>[1] = {}) {
    try {
      return await $fetch<T>(path, {
        credentials: 'include',
        ...options,
        headers: {
          Accept: 'application/json',
          ...options.headers,
        },
      })
    } catch (error: unknown) {
      const payload = error as { data?: { detail?: string }, message?: string }
      throw new Error(payload.data?.detail || payload.message || 'The admin request failed.')
    }
  }

  return { request }
}
