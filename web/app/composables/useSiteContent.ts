import { cloneDefaultSiteContent, type PublicSiteContent } from '~/data/siteContent'

export function useSiteContent() {
  const config = useRuntimeConfig()
  const apiBase = String(config.public.apiBase || '').replace(/\/$/, '')
  const endpoint = `${apiBase}/api/v1/site`
  const { data, refresh } = useFetch<PublicSiteContent>(endpoint, {
    server: false,
    key: 'public-site-content',
    default: cloneDefaultSiteContent,
  })

  const siteContent = computed(() => data.value || cloneDefaultSiteContent())
  const portfolio = computed(() => siteContent.value.portfolio.map(image => ({
    ...image,
    url: image.url.startsWith('http') ? image.url : `${apiBase}${image.url}`,
    after_url: image.after_url
      ? (image.after_url.startsWith('http') ? image.after_url : `${apiBase}${image.after_url}`)
      : null,
  })))

  return { siteContent, portfolio, refreshSiteContent: refresh }
}
