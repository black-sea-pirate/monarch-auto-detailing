export default defineNuxtConfig({
  compatibilityDate: '2026-08-01',
  telemetry: false,
  css: ['~/assets/css/main.css'],
  devtools: { enabled: true },
  runtimeConfig: {
    public: {
      apiBase: '',
      showPortfolio: false,
    },
  },
  app: {
    head: {
      htmlAttrs: { lang: 'en-CA' },
      title: 'Monarch Auto Interior Detailing | Royal Oak, Calgary NW',
      meta: [
        {
          name: 'description',
          content:
            'Focused interior detailing in Royal Oak and nearby NW Calgary communities. Request a clear photo-based quote.',
        },
        { name: 'theme-color', content: '#0b1713' },
      ],
      link: [{ rel: 'icon', type: 'image/svg+xml', href: '/brand/monarch-symbol-gold.svg?v=4' }],
    },
  },
})
