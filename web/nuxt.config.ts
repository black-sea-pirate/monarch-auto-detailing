export default defineNuxtConfig({
  compatibilityDate: '2026-08-01',
  telemetry: false,
  css: ['~/assets/css/main.css', '~/assets/css/admin.css'],
  devtools: { enabled: false },
  runtimeConfig: {
    public: {
      apiBase: '',
      adminDevToken: '',
    },
  },
  routeRules: {
    '/admin/**': { ssr: false },
  },
  app: {
    head: {
      htmlAttrs: { lang: 'en-CA' },
      title: 'Mobile Interior Car Detailing in Calgary | Monarch',
      meta: [
        {
          name: 'description',
          content:
            'Mobile interior car detailing across Calgary. View clear starting prices and request a photo-based quote.',
        },
        { name: 'theme-color', content: '#0b1713' },
      ],
      link: [{ rel: 'icon', type: 'image/svg+xml', href: '/brand/monarch-symbol-gold.svg?v=4' }],
    },
  },
})
