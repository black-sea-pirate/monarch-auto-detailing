<script setup lang="ts">
import { publicContactLinks, socialLinks, whatsappLink } from '~/data/contactLinks'
import { activePrice, formatCad, type PriceKey } from '~/data/siteContent'

const siteUrl = 'https://monarch-yyc.com'
const pageTitle = 'Mobile Interior Car Detailing Calgary | Monarch Auto Detailing'
const pageDescription = 'Mobile interior car detailing across Calgary. Clear starting prices, material-safe service and photo-based quotes from Monarch Auto Detailing.'
const socialImage = `${siteUrl}/brand/monarch-cover.png`

useSeoMeta({
  title: pageTitle,
  description: pageDescription,
  robots: 'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1',
  ogType: 'website',
  ogUrl: `${siteUrl}/`,
  ogLocale: 'en_CA',
  ogSiteName: 'Monarch Auto Detailing',
  ogTitle: pageTitle,
  ogDescription: pageDescription,
  ogImage: socialImage,
  ogImageWidth: 1640,
  ogImageHeight: 624,
  ogImageAlt: 'Monarch Auto Detailing — mobile interior car detailing in Calgary',
  twitterCard: 'summary_large_image',
  twitterTitle: pageTitle,
  twitterDescription: pageDescription,
  twitterImage: socialImage,
  twitterImageAlt: 'Monarch Auto Detailing — mobile interior car detailing in Calgary',
})

useHead({
  link: [
    { rel: 'canonical', href: `${siteUrl}/` },
  ],
  script: [
    {
      key: 'monarch-local-business',
      type: 'application/ld+json',
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@graph': [
          {
            '@type': 'WebSite',
            '@id': `${siteUrl}/#website`,
            url: `${siteUrl}/`,
            name: 'Monarch Auto Detailing',
            inLanguage: 'en-CA',
            publisher: { '@id': `${siteUrl}/#business` },
          },
          {
            '@type': 'AutomotiveBusiness',
            '@id': `${siteUrl}/#business`,
            name: 'Monarch Auto Detailing',
            url: `${siteUrl}/`,
            logo: `${siteUrl}/brand/monarch-symbol-gold.svg`,
            image: socialImage,
            description: pageDescription,
            currenciesAccepted: 'CAD',
            areaServed: {
              '@type': 'City',
              name: 'Calgary',
            },
            sameAs: socialLinks.map(link => link.href),
            hasOfferCatalog: {
              '@type': 'OfferCatalog',
              name: 'Mobile interior detailing services',
              itemListElement: [
                'Maintenance Interior Clean',
                'Deep Interior Detail',
                'Salt & Stain Treatment',
                'Pet Hair Removal',
                'Leather Cleaning & Care',
                'Upholstery Extraction',
              ].map(name => ({
                '@type': 'Offer',
                itemOffered: {
                  '@type': 'Service',
                  name,
                  areaServed: 'Calgary',
                },
              })),
            },
          },
        ],
      }),
    },
  ],
})

const { siteContent, portfolio } = useSiteContent()
const showPricing = computed(() => siteContent.value.sections.pricing_enabled)
const showFoundingOffer = computed(() => siteContent.value.sections.founding_offer_enabled)
const showPortfolio = computed(() => (
  siteContent.value.sections.portfolio_enabled && portfolio.value.length > 0
))
const menuOpen = ref(false)

const priceSetting = (key: PriceKey) => siteContent.value.pricing[key]
const currentPrice = (key: PriceKey) => formatCad(activePrice(priceSetting(key)))
const regularPrice = (key: PriceKey) => formatCad(priceSetting(key).base_price_cents)
const priceIsDiscounted = (key: PriceKey) => (
  priceSetting(key).discount_enabled && priceSetting(key).discount_price_cents !== null
)
const resultsGallery = ref<HTMLElement | null>(null)
const activeResult = ref(0)
const comparisonPositions = reactive<Record<string, number>>({})
let resultsTimer: ReturnType<typeof setInterval> | undefined
let stopResultsWatch: (() => void) | undefined

function stopResultsAutoplay() {
  if (resultsTimer) clearInterval(resultsTimer)
  resultsTimer = undefined
}

function scrollToResult(index: number) {
  const count = portfolio.value.length
  const gallery = resultsGallery.value
  if (!gallery || count === 0) return
  const targetIndex = (index + count) % count
  const item = gallery.querySelectorAll<HTMLElement>('figure')[targetIndex]
  if (!item) return
  activeResult.value = targetIndex
  gallery.scrollTo({
    left: item.offsetLeft - (gallery.clientWidth - item.clientWidth) / 2,
    behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
  })
}

function startResultsAutoplay() {
  stopResultsAutoplay()
  if (
    portfolio.value.length < 2
    || !showPortfolio.value
    || document.hidden
    || window.matchMedia('(prefers-reduced-motion: reduce)').matches
  ) return
  resultsTimer = window.setInterval(() => scrollToResult(activeResult.value + 1), 4500)
}

function syncActiveResult() {
  const gallery = resultsGallery.value
  if (!gallery) return
  const galleryCentre = gallery.scrollLeft + gallery.clientWidth / 2
  const items = [...gallery.querySelectorAll<HTMLElement>('figure')]
  let closestIndex = 0
  let closestDistance = Number.POSITIVE_INFINITY
  items.forEach((item, index) => {
    const itemCentre = item.offsetLeft + item.clientWidth / 2
    const distance = Math.abs(itemCentre - galleryCentre)
    if (distance < closestDistance) {
      closestIndex = index
      closestDistance = distance
    }
  })
  activeResult.value = closestIndex
}

function comparisonPosition(imageId: string) {
  return comparisonPositions[imageId] ?? 50
}

function updateComparisonPosition(imageId: string, event: Event) {
  const input = event.currentTarget as HTMLInputElement
  comparisonPositions[imageId] = Number(input.value)
}

function handleResultsVisibility() {
  if (document.hidden) stopResultsAutoplay()
  else startResultsAutoplay()
}

onMounted(() => {
  stopResultsWatch = watch(
    [() => portfolio.value.length, showPortfolio],
    async () => {
      await nextTick()
      activeResult.value = 0
      startResultsAutoplay()
    },
    { immediate: true },
  )
  document.addEventListener('visibilitychange', handleResultsVisibility)
})

onBeforeUnmount(() => {
  stopResultsAutoplay()
  stopResultsWatch?.()
  document.removeEventListener('visibilitychange', handleResultsVisibility)
})

const coreServices = [
  {
    number: '01',
    slug: 'maintenance',
    title: 'Maintenance Interior Clean',
    copy: 'Routine vacuuming, careful surface cleaning and interior glass care for well-maintained vehicles.',
    image: '/brand/services/maintenance-interior-clean.jpg',
    alt: 'A lightly soiled front passenger area before a maintenance interior clean',
  },
  {
    number: '02',
    slug: 'reset',
    title: 'Deep Interior Detail',
    copy: 'Tool-assisted detailing for visible buildup, with focused work on controls, vents, seams, crevices and other high-touch areas.',
    image: '/brand/services/full-interior-reset.jpg',
    alt: 'A soiled rear seating area before a deep interior detail',
  },
]

const addOnServices = [
  {
    number: '03',
    slug: 'salt',
    title: 'Salt & Stain Treatment',
    copy: 'Targeted treatment for winter salt residue and individual stains, subject to material and condition.',
    image: '/brand/services/salt-stain-treatment.jpg',
    alt: 'Winter salt residue across a dark vehicle footwell',
  },
  {
    number: '04',
    slug: 'pet-hair',
    title: 'Pet Hair Removal',
    copy: 'Mechanical agitation and detailed removal of embedded hair from carpet and textile surfaces.',
    image: '/brand/services/pet-hair-removal.jpg',
    alt: 'Pet hair being lifted from a vehicle carpet with a detailing tool',
  },
  {
    number: '05',
    slug: 'leather',
    title: 'Leather Cleaning & Care',
    copy: 'Material-appropriate cleaning and care selected for the leather type and its current condition.',
    image: '/brand/services/leather-cleaning-care.jpg',
    alt: 'A black leather vehicle seat showing a cleaned comparison area',
  },
  {
    number: '06',
    slug: 'extraction',
    title: 'Upholstery Extraction',
    copy: 'Controlled-moisture deep cleaning for fabric seats and carpet where the material allows it.',
    image: '/brand/services/upholstery-extraction.jpg',
    alt: 'An extractor cleaning a fabric vehicle seat',
  },
]

const pricingPackages = [
  {
    priceKey: 'maintenance' as PriceKey,
    name: 'Maintenance Interior Clean',
    duration: '2–2.5 hours',
    bestFor: 'Lightly soiled, regularly maintained interiors.',
    features: [
      'Thorough vacuum of seats, floors and mats',
      'Careful cleaning of accessible surfaces',
      'Dashboard, console and door panels',
      'Interior glass and mirrors',
      'Light crevice detailing and final inspection',
    ],
    note: 'Heavy salt, stains and pet hair are not included.',
  },
  {
    priceKey: 'deep' as PriceKey,
    name: 'Deep Interior Detail',
    duration: '4–5 hours',
    bestFor: 'Visible buildup, daily-driver wear and interiors needing detailed attention.',
    featured: true,
    features: [
      'Everything in the Maintenance clean',
      'Deep vacuuming and tool-assisted crevice work',
      'Detailed steering wheel, controls and cupholders',
      'Vents, seams and accessible seat-track areas',
      'Thorough dashboard, console, trim and door-panel cleaning',
    ],
    note: 'Extraction, heavy pet hair and intensive stain work are priced separately.',
  },
  {
    priceKey: 'complete' as PriceKey,
    name: 'Complete Interior Reset',
    duration: '6+ hours',
    bestFor: 'A complete interior transformation with deeper material care.',
    features: [
      'Everything in the Deep Interior Detail',
      'Seat, carpet and mat extraction where appropriate',
      'Leather cleaning and care where applicable',
      'Moderate pet hair removal',
      'Targeted salt and stain treatment',
    ],
    note: 'Excessive pet hair, severe staining, smoke, mould and biological contamination require a separate assessment.',
  },
]

const pricedAddOns = [
  {
    priceKey: 'pet_hair' as PriceKey,
    name: 'Pet Hair Removal',
    pricePrefix: 'From $',
    priceSuffix: '',
    timing: 'Allow 45+ min',
    copy: 'For light to moderate embedded pet hair. Heavy accumulation is quoted from photos.',
  },
  {
    priceKey: 'extraction' as PriceKey,
    name: 'Upholstery Extraction',
    pricePrefix: '$',
    priceSuffix: ' / seat',
    timing: 'Full set from $90',
    copy: 'Controlled-moisture extraction for fabric seating where the material allows it.',
  },
  {
    priceKey: 'leather' as PriceKey,
    name: 'Leather Cleaning & Care',
    pricePrefix: 'From $',
    priceSuffix: '',
    timing: 'Allow 30+ min',
    copy: 'Material-appropriate cleaning and care for leather seating and touchpoints.',
  },
  {
    priceKey: 'salt_stain' as PriceKey,
    name: 'Salt & Stain Treatment',
    pricePrefix: 'From $',
    priceSuffix: '',
    timing: 'Confirmed from photos',
    copy: 'Targeted treatment based on the material, age and severity of the affected area.',
  },
]

const method = [
  ['Photo assessment', 'An initial photo review helps define the likely scope.'],
  ['Interior inspection', 'Materials, stains and delicate areas are identified on site.'],
  ['Dry removal', 'Detailed vacuuming, brushing and crevice work remove loose debris.'],
  ['Targeted wet cleaning', 'Controlled-moisture cleaning is matched to each material.'],
  ['Final inspection', 'Completed work is reviewed and practical care notes are provided.'],
]

const materials = [
  {
    name: 'Leather',
    copy: 'Gentle cleaning selected for the leather type and condition, with a discreet spot test where appropriate.',
    image: '/brand/materials/leather.jpg',
    alt: 'Macro view of black automotive leather grain and stitching',
  },
  {
    name: 'Textile',
    copy: 'Controlled-moisture cleaning selected for the fabric and level of soiling.',
    image: '/brand/materials/textile.jpg',
    alt: 'Macro view of dark woven automotive seat textile',
  },
  {
    name: 'Carpet',
    copy: 'Thorough vacuuming, agitation and targeted extraction where appropriate.',
    image: '/brand/materials/carpet.jpg',
    alt: 'Macro view of dense dark automotive carpet fibres',
  },
  {
    name: 'Plastics',
    copy: 'Careful cleaning with a natural, low-gloss finish.',
    image: '/brand/materials/plastics.jpg',
    alt: 'Macro view of grain-textured matte automotive plastic',
  },
  {
    name: 'Piano black',
    copy: 'Soft tools and minimal pressure to reduce the risk of adding marks.',
    image: '/brand/materials/piano-black.jpg',
    alt: 'Macro view of glossy piano-black automotive trim',
  },
]

const faqs = [
  ['Service area', 'Mobile appointments are available across Calgary. Locations outside city limits may be available by quote.'],
  ['Appointment length', 'Timing is confirmed after reviewing the vehicle size, condition and requested scope.'],
  ['Vehicle prep', 'Please remove personal items, child seats and valuables before your appointment.'],
  ['Drying time', 'Fabric and carpet may remain damp after extraction. Drying varies with weather, airflow and how much wet cleaning is required.'],
  ['Stain limitations', 'Some set-in stains, dye transfer, wear and material damage may not be fully removable. Expectations are discussed before work begins.'],
  ['Power and access', 'We require access to a standard electrical outlet and a water source on site.'],
  ['Payment', 'Available payment options are confirmed with your quote.'],
]

</script>

<template>
  <div id="top" class="site-shell">
    <header class="site-header">
      <a class="brand" href="#top" aria-label="Monarch home">
        <img class="brand-symbol" src="/brand/monarch-symbol-gold.svg" alt="" width="44" height="45">
        <img class="brand-wordmark" src="/brand/monarch-wordmark-on-dark.svg" alt="" width="142" height="38">
      </a>

      <nav class="desktop-nav" aria-label="Primary navigation">
        <a href="#services">Services</a>
        <a v-if="showPricing" href="#pricing">Pricing</a>
        <a href="#method">Method</a>
        <a v-if="showPortfolio" href="#results">Results</a>
        <a href="#faq">FAQ</a>
      </nav>

      <a class="header-cta" href="#quote">Request a quote <span aria-hidden="true">↗</span></a>
      <button
        class="menu-button"
        type="button"
        :aria-expanded="menuOpen"
        aria-label="Toggle menu"
        @click="menuOpen = !menuOpen"
      >
        <span />
        <span />
      </button>

      <nav v-if="menuOpen" class="mobile-nav" aria-label="Mobile navigation">
        <a href="#services" @click="menuOpen = false">Services</a>
        <a v-if="showPricing" href="#pricing" @click="menuOpen = false">Pricing</a>
        <a href="#method" @click="menuOpen = false">Method</a>
        <a v-if="showPortfolio" href="#results" @click="menuOpen = false">Results</a>
        <a href="#faq" @click="menuOpen = false">FAQ</a>
        <a href="#quote" @click="menuOpen = false">Request a quote</a>
      </nav>
    </header>

    <main>
      <section class="hero section-wrap">
        <div class="hero-copy">
          <p class="eyebrow"><i /> Mobile interior detailing · Calgary</p>
          <h1>Your cabin,<br><em>reset properly.</em></h1>
          <p class="hero-lede">
            Mobile interior detailing across Calgary for daily drivers, family vehicles and the cars you care about most.
          </p>
          <div class="hero-actions">
            <a class="button button-primary" href="#quote">Request a photo quote <span>↗</span></a>
            <a class="text-link" href="#method">See the method <span>↓</span></a>
          </div>
          <p class="availability"><span /> Mobile appointments across Calgary</p>
        </div>

        <div class="hero-visual" aria-label="Monarch premium interior detailing visual">
          <div class="hero-image" />
          <LiquidOakShader class="hero-shader" />
          <div class="precision-card glass-panel">
            <span class="precision-index">Mobile · Calgary</span>
            <div>
              <small>Interior precision</small>
              <strong>Clean is a standard.<br>Care is the method.</strong>
            </div>
          </div>
        </div>
      </section>

      <section class="trust-strip stitched-divider stitched-divider--bottom" aria-label="Service principles">
        <div><span>01</span><strong>Interior specialist</strong></div>
        <div><span>02</span><strong>Material-safe process</strong></div>
        <div><span>03</span><strong>Photo-based quotes</strong></div>
      </section>

      <section id="services" class="services section-wrap section-pad">
        <div class="section-heading">
          <div>
            <p class="eyebrow"><i /> Focused services</p>
            <h2>Built around the<br><em>condition of your cabin.</em></h2>
          </div>
          <p>
            Clear service levels, with the final scope shaped by the vehicle, materials and current condition.
          </p>
        </div>

        <div class="service-groups">
          <div class="service-group">
            <p class="service-group-label"><span>01</span> Core services</p>
            <div class="service-grid service-grid--core">
              <article
                v-for="service in coreServices"
                :key="service.number"
                :class="['service-card', 'service-card--core', `service-card--${service.slug}`]"
              >
                <img :src="service.image" :alt="service.alt" width="1536" height="1024" loading="lazy" decoding="async">
                <div class="service-card-shade" aria-hidden="true" />
                <div class="service-card-meta">
                  <span>{{ service.number }}</span>
                  <small>Main service</small>
                </div>
                <div class="service-card-copy">
                  <h3>{{ service.title }}</h3>
                  <p>{{ service.copy }}</p>
                </div>
                <i aria-hidden="true">↗</i>
              </article>
            </div>
          </div>

          <div class="service-group">
            <div class="service-group-heading">
              <p class="service-group-label"><span>02</span> Targeted add-ons</p>
              <small>Added only where the condition calls for them.</small>
            </div>
            <div class="service-grid service-grid--addons">
              <article
                v-for="service in addOnServices"
                :key="service.number"
                :class="['service-card', 'service-card--addon', `service-card--${service.slug}`]"
              >
                <img :src="service.image" :alt="service.alt" width="1536" height="1024" loading="lazy" decoding="async">
                <div class="service-card-shade" aria-hidden="true" />
                <div class="service-card-meta">
                  <span>{{ service.number }}</span>
                </div>
                <div class="service-card-copy">
                  <h3>{{ service.title }}</h3>
                  <p>{{ service.copy }}</p>
                </div>
                <i aria-hidden="true">↗</i>
              </article>
            </div>
          </div>
        </div>
      </section>

      <section v-if="showPricing" id="pricing" class="pricing-section section-pad stitched-divider stitched-divider--bottom">
        <div class="section-wrap">
          <div class="section-heading pricing-heading">
            <div>
              <p class="eyebrow"><i /> Clear starting prices</p>
              <h2>Know the starting point.<br><em>Approve the final quote.</em></h2>
            </div>
            <p>
              Every price starts with a sedan in the condition described below. Vehicle size, condition and requested add-ons are confirmed from photos before booking.
            </p>
          </div>

          <div class="pricing-grid">
            <article
              v-for="pricingPackage in pricingPackages"
              :key="pricingPackage.name"
              :class="['pricing-card', { 'pricing-card--featured': pricingPackage.featured }]"
            >
              <span v-if="pricingPackage.featured" class="pricing-card-badge">Most requested</span>
              <div class="pricing-card-topline">
                <span>{{ pricingPackage.duration }}</span>
                <small>Estimated time</small>
              </div>
              <h3>{{ pricingPackage.name }}</h3>
              <p class="pricing-price">
                <small>From</small>
                <del v-if="priceIsDiscounted(pricingPackage.priceKey)">${{ regularPrice(pricingPackage.priceKey) }}</del>
                <strong><sup>$</sup>{{ currentPrice(pricingPackage.priceKey) }}</strong><span>CAD</span>
              </p>
              <p class="pricing-best-for">{{ pricingPackage.bestFor }}</p>
              <ul>
                <li v-for="feature in pricingPackage.features" :key="feature">
                  <span aria-hidden="true">✓</span>{{ feature }}
                </li>
              </ul>
              <p class="pricing-card-note">{{ pricingPackage.note }}</p>
              <a class="pricing-card-link" href="#quote">Request a photo quote <span aria-hidden="true">↗</span></a>
            </article>
          </div>

          <div class="pricing-adjustments">
            <div>
              <span>Vehicle size</span>
              <strong>
                SUV / pickup
                <del v-if="priceIsDiscounted('suv_surcharge')">+${{ regularPrice('suv_surcharge') }}</del>
                +${{ currentPrice('suv_surcharge') }}
              </strong>
              <strong>
                3-row SUV / minivan
                <del v-if="priceIsDiscounted('large_vehicle_surcharge')">+${{ regularPrice('large_vehicle_surcharge') }}</del>
                +${{ currentPrice('large_vehicle_surcharge') }}
              </strong>
            </div>
            <p>Times are estimates, not deadlines. Final scope and price are agreed before the appointment begins.</p>
          </div>

          <div class="priced-addons">
            <div class="priced-addons-heading">
              <p class="service-group-label"><span>+</span> Optional add-ons</p>
              <small>Added only where the condition calls for them.</small>
            </div>
            <div class="priced-addons-grid">
              <article v-for="addOn in pricedAddOns" :key="addOn.name">
                <div>
                  <h3>{{ addOn.name }}</h3>
                  <strong>
                    <del v-if="priceIsDiscounted(addOn.priceKey)">{{ addOn.pricePrefix }}{{ regularPrice(addOn.priceKey) }}{{ addOn.priceSuffix }}</del>
                    {{ addOn.pricePrefix }}{{ currentPrice(addOn.priceKey) }}{{ addOn.priceSuffix }}
                  </strong>
                </div>
                <small>{{ addOn.timing }}</small>
                <p>{{ addOn.copy }}</p>
              </article>
            </div>
          </div>

          <p class="pricing-disclaimer">
            Stains are treated according to material, age and condition. Complete removal cannot be guaranteed. Prices are confirmed before work begins.
          </p>
        </div>
      </section>

      <section id="method" class="method-section section-pad stitched-divider stitched-divider--bottom">
        <div class="method-inner section-wrap">
          <div class="method-intro">
            <p class="eyebrow"><i /> The Monarch method</p>
            <h2>Visible care.<br><em>Controlled process.</em></h2>
            <p>
              Quality should be explained, not merely claimed. Every stage has a clear purpose and is adapted to the interior in front of us.
            </p>
            <div class="method-seal">
              <img class="method-symbol" src="/brand/monarch-symbol-gold.svg" alt="Monarch emblem" width="82" height="83">
              <span>Mobile service<br>Across Calgary</span>
            </div>
          </div>

          <ol class="method-list">
            <li v-for="(step, index) in method" :key="step[0]">
              <span>{{ String(index + 1).padStart(2, '0') }}</span>
              <div>
                <h3>{{ step[0] }}</h3>
                <p>{{ step[1] }}</p>
              </div>
              <i aria-hidden="true" />
            </li>
          </ol>
        </div>
      </section>

      <section id="materials" class="materials section-wrap section-pad">
        <div class="section-heading material-heading">
          <div>
            <p class="eyebrow"><i /> Material care</p>
            <h2>Different surfaces.<br><em>Different decisions.</em></h2>
          </div>
          <p>
            Products and agitation levels are selected around the material type and its current condition.
          </p>
        </div>

        <div class="material-grid stitched-divider stitched-divider--bottom">
          <article v-for="(material, index) in materials" :key="material.name">
            <figure class="material-swatch">
              <img :src="material.image" :alt="material.alt" width="1000" height="667" loading="lazy" decoding="async">
              <span class="material-index">{{ String(index + 1).padStart(2, '0') }}</span>
            </figure>
            <div class="material-copy">
              <h3>{{ material.name }}</h3>
              <p>{{ material.copy }}</p>
            </div>
          </article>
        </div>
      </section>

      <section v-if="showPortfolio" id="results" class="results section-wrap section-pad">
        <div class="results-card">
          <div class="results-text">
            <p class="eyebrow"><i /> Honest proof</p>
            <h2>Real client work.<br><em>Nothing staged.</em></h2>
            <p>
              The portfolio is being built from real appointments only. No stock before-and-after photos and no borrowed results.
            </p>
            <span class="status-pill"><i /> Recent client work</span>
          </div>
          <div
            class="results-carousel"
            @mouseenter="stopResultsAutoplay"
            @mouseleave="startResultsAutoplay"
            @focusin="stopResultsAutoplay"
            @focusout="startResultsAutoplay"
          >
            <div
              ref="resultsGallery"
              class="results-gallery"
              aria-label="Recent interior detailing work"
              @scroll.passive="syncActiveResult"
            >
              <figure v-for="image in portfolio" :key="image.id">
                <div
                  v-if="image.after_url"
                  class="before-after"
                  :style="{ '--comparison-position': `${comparisonPosition(image.id)}%` }"
                >
                  <img
                    class="comparison-before"
                    :src="image.url"
                    :alt="`Before: ${image.caption || 'Monarch interior detailing work'}`"
                    loading="lazy"
                    decoding="async"
                  >
                  <div class="comparison-after">
                    <img
                      :src="image.after_url"
                      :alt="`After: ${image.caption || 'Monarch interior detailing work'}`"
                      loading="lazy"
                      decoding="async"
                    >
                  </div>
                  <span class="comparison-label is-before">Before</span>
                  <span class="comparison-label is-after">After</span>
                  <span class="comparison-divider" aria-hidden="true"><i>↔</i></span>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    :value="comparisonPosition(image.id)"
                    :aria-label="`Compare before and after for ${image.caption || 'this portfolio work'}`"
                    @input="updateComparisonPosition(image.id, $event)"
                  >
                </div>
                <img
                  v-else
                  :src="image.url"
                  :alt="image.caption || 'A recent Monarch interior detailing result'"
                  loading="lazy"
                  decoding="async"
                >
                <figcaption v-if="image.caption">{{ image.caption }}</figcaption>
              </figure>
            </div>
            <div v-if="portfolio.length > 1" class="results-controls">
              <button type="button" aria-label="Previous portfolio photo" @click="scrollToResult(activeResult - 1)">←</button>
              <div aria-label="Choose portfolio photo">
                <button
                  v-for="(image, index) in portfolio"
                  :key="image.id"
                  type="button"
                  :class="{ 'is-active': activeResult === index }"
                  :aria-label="`Show portfolio photo ${index + 1}`"
                  :aria-current="activeResult === index ? 'true' : undefined"
                  @click="scrollToResult(index)"
                />
              </div>
              <button type="button" aria-label="Next portfolio photo" @click="scrollToResult(activeResult + 1)">→</button>
            </div>
          </div>
        </div>
      </section>

      <section v-if="showFoundingOffer" class="founding-banner section-wrap">
        <div class="founding-inner glass-panel">
          <span class="founding-index">NFC / 10</span>
          <div>
            <p class="eyebrow"><i /> Founding client appointments</p>
            <h2>Arrive early.<br><em>Be remembered.</em></h2>
            <p>Join the first Monarch clients and help establish a portfolio built entirely from real work.</p>
          </div>
          <div class="nfc-offer">
            <span>NFC</span>
            <p><small>NFC arrival state only</small><strong>10% off your first interior detail</strong></p>
          </div>
        </div>
      </section>

      <section id="quote" class="quote-section section-pad stitched-divider">
        <div class="quote-inner section-wrap">
          <div class="quote-copy">
            <p class="eyebrow"><i /> Start with clarity</p>
            <h2>Get a clear<br><em>photo quote.</em></h2>
            <p>
              Tell us what you drive, what needs attention and attach a few clear interior photos. We will confirm the scope and timing after review.
            </p>
            <ol class="quote-steps">
              <li><span>1</span>Send vehicle details</li>
              <li><span>2</span>Share interior photos</li>
              <li><span>3</span>Receive scope and quote</li>
            </ol>
          </div>

          <QuoteRequestForm />
        </div>
      </section>

      <section id="faq" class="faq-section section-wrap section-pad">
        <div class="faq-heading">
          <p class="eyebrow"><i /> Before the appointment</p>
          <h2>Frequently asked<br><em>questions.</em></h2>
        </div>
        <div class="faq-list">
          <details v-for="(faq, index) in faqs" :key="faq[0]">
            <summary>
              <span>{{ String(index + 1).padStart(2, '0') }}</span>
              <strong>{{ faq[0] }}</strong>
              <i aria-hidden="true">+</i>
            </summary>
            <p>{{ faq[1] }}</p>
          </details>
        </div>
      </section>

      <section class="final-cta stitched-divider stitched-divider--bottom">
        <div class="section-wrap">
          <p class="eyebrow"><i /> Mobile service · Calgary</p>
          <h2>Ready for a<br><em>cleaner cabin?</em></h2>
          <p>Start with a few photos. Receive a clear proposed scope before booking.</p>
          <div class="final-cta-actions">
            <a class="button button-primary" href="#quote">Request a photo quote <span>↗</span></a>
            <a
              class="button button-whatsapp"
              :href="whatsappLink.href"
              target="_blank"
              rel="noopener noreferrer"
            >
              <SocialBrandIcon name="whatsapp" />
              Message on WhatsApp
            </a>
          </div>
        </div>
      </section>
    </main>

    <a class="mobile-quote-dock" href="#quote">Photo quote <span>↗</span></a>

    <footer class="site-footer section-wrap">
      <div class="footer-brand">
        <img class="brand-symbol" src="/brand/monarch-symbol-gold.svg" alt="" width="36" height="36">
        <img class="brand-wordmark" src="/brand/monarch-wordmark-on-dark.svg" alt="Monarch Auto Detailing" width="112" height="30">
      </div>
      <div class="footer-center">
        <p>Mobile appointments across Calgary.</p>
        <div class="footer-social-links" aria-label="Monarch contact and social links">
          <a
            v-for="link in publicContactLinks"
            :key="link.name"
            :href="link.href"
            :aria-label="link.label"
            :title="link.label"
            target="_blank"
            rel="noopener noreferrer"
            :style="`--social-color: ${link.color}`"
          >
            <SocialBrandIcon :name="link.name" />
          </a>
        </div>
      </div>
      <span>© 2026 Monarch Auto Detailing</span>
    </footer>
  </div>
</template>
