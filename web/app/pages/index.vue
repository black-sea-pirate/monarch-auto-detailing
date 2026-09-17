<script setup lang="ts">
const config = useRuntimeConfig()
const showFoundingOffer = false
const showPortfolio = computed(() => String(config.public.showPortfolio).toLowerCase() === 'true')
const menuOpen = ref(false)

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
    title: 'Full Interior Reset',
    copy: 'A deeper clean for accumulated soil. The exact scope is confirmed from photos and the on-site inspection.',
    image: '/brand/services/full-interior-reset.jpg',
    alt: 'A soiled rear seating area before a full interior reset',
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
  ['Service area', 'Royal Oak, Rocky Ridge, Tuscany and Arbour Lake by appointment.'],
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
        <a href="#method" @click="menuOpen = false">Method</a>
        <a v-if="showPortfolio" href="#results" @click="menuOpen = false">Results</a>
        <a href="#faq" @click="menuOpen = false">FAQ</a>
        <a href="#quote" @click="menuOpen = false">Request a quote</a>
      </nav>
    </header>

    <main>
      <section class="hero section-wrap">
        <div class="hero-copy">
          <p class="eyebrow"><i /> Royal Oak · Calgary NW</p>
          <h1>Your cabin,<br><em>reset properly.</em></h1>
          <p class="hero-lede">
            Focused interior detailing for daily drivers, family vehicles and the cars you care about most.
          </p>
          <div class="hero-actions">
            <a class="button button-primary" href="#quote">Request a photo quote <span>↗</span></a>
            <a class="text-link" href="#method">See the method <span>↓</span></a>
          </div>
          <p class="availability"><span /> By appointment · Royal Oak and nearby NW communities</p>
        </div>

        <div class="hero-visual" aria-label="Monarch premium interior detailing visual">
          <div class="hero-image" />
          <LiquidOakShader class="hero-shader" />
          <div class="precision-card glass-panel">
            <span class="precision-index">M / 01</span>
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
            No invented packages and no one-size-fits-all promises. The scope is shaped by the vehicle, materials and current condition.
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
              <span>Royal Oak<br>Calgary NW</span>
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
            <span class="status-pill"><i /> Portfolio being built</span>
          </div>
          <div class="results-art" aria-hidden="true">
            <span class="scan-line" />
            <strong>M</strong>
            <div class="result-label">Before / After archive<br><b>Incoming</b></div>
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
          <p class="eyebrow"><i /> Royal Oak · Calgary NW</p>
          <h2>Ready for a<br><em>cleaner cabin?</em></h2>
          <p>Start with a few photos. Receive a clear proposed scope before booking.</p>
          <a class="button button-primary" href="#quote">Request a photo quote <span>↗</span></a>
        </div>
      </section>
    </main>

    <a class="mobile-quote-dock" href="#quote">Photo quote <span>↗</span></a>

    <footer class="site-footer section-wrap">
      <div class="footer-brand">
        <img class="brand-symbol" src="/brand/monarch-symbol-gold.svg" alt="" width="36" height="36">
        <img class="brand-wordmark" src="/brand/monarch-wordmark-on-dark.svg" alt="Monarch Auto Detailing" width="112" height="30">
      </div>
      <p>Royal Oak and nearby NW Calgary communities · By appointment.</p>
      <span>© 2026 Monarch Auto Interior</span>
    </footer>
  </div>
</template>
