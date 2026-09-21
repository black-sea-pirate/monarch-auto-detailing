<script setup lang="ts">
import { socialLinks, whatsappLink } from '~/data/contactLinks'
import { activePrice, formatCad, type PriceKey } from '~/data/siteContent'

const { siteContent } = useSiteContent()
const showPricing = computed(() => siteContent.value.sections.pricing_enabled)
const currentPrice = (key: PriceKey) => formatCad(activePrice(siteContent.value.pricing[key]))
const regularPrice = (key: PriceKey) => formatCad(siteContent.value.pricing[key].base_price_cents)
const priceIsDiscounted = (key: PriceKey) => (
  siteContent.value.pricing[key].discount_enabled
  && siteContent.value.pricing[key].discount_price_cents !== null
)

useHead({
  title: 'Request an Interior Detail | Monarch Calgary',
  meta: [
    {
      name: 'description',
      content: 'Request a photo-based quote for mobile interior car detailing across Calgary.',
    },
  ],
})

</script>

<template>
  <div class="card-page">
    <header class="card-page-header section-wrap">
      <NuxtLink class="brand" to="/" aria-label="Monarch home">
        <img class="brand-symbol" src="/brand/monarch-symbol-gold.svg" alt="" width="44" height="45">
        <img class="brand-wordmark" src="/brand/monarch-wordmark-on-dark.svg" alt="Monarch Auto Detailing" width="142" height="38">
      </NuxtLink>
      <NuxtLink class="card-home-link" to="/">Full website <span aria-hidden="true">↗</span></NuxtLink>
    </header>

    <main class="card-page-main section-wrap">
      <section class="card-page-intro" aria-labelledby="card-page-title">
        <p class="eyebrow"><i /> Mobile interior detailing · Calgary</p>
        <h1 id="card-page-title">Request your<br><em>interior detail.</em></h1>
        <p class="card-page-lede">
          Tell us how to reach you, what your vehicle needs and attach a few clear photos. We will review everything and confirm the scope before booking.
        </p>

        <div v-if="showPricing" class="card-pricing-summary">
          <div class="card-pricing-heading">
            <span>Starting prices</span>
            <NuxtLink to="/#pricing">Full details <i aria-hidden="true">↗</i></NuxtLink>
          </div>
          <div>
            <span>Maintenance Interior Clean</span>
            <strong><del v-if="priceIsDiscounted('maintenance')">${{ regularPrice('maintenance') }}</del> From ${{ currentPrice('maintenance') }}</strong>
          </div>
          <div>
            <span>Deep Interior Detail</span>
            <strong><del v-if="priceIsDiscounted('deep')">${{ regularPrice('deep') }}</del> From ${{ currentPrice('deep') }}</strong>
          </div>
          <div>
            <span>Complete Interior Reset</span>
            <strong><del v-if="priceIsDiscounted('complete')">${{ regularPrice('complete') }}</del> From ${{ currentPrice('complete') }}</strong>
          </div>
        </div>

        <a
          class="card-social-link card-whatsapp-link"
          :href="whatsappLink.href"
          target="_blank"
          rel="noopener noreferrer"
          :style="`--social-color: ${whatsappLink.color}`"
        >
          <span class="card-social-icon"><SocialBrandIcon name="whatsapp" /></span>
          <span>
            <small>Message directly</small>
            <strong>WhatsApp</strong>
          </span>
          <i aria-hidden="true">↗</i>
        </a>

        <div class="card-social-block">
          <p>See our work and updates</p>
          <div class="card-social-links">
            <a
              v-for="social in socialLinks"
              :key="social.name"
              class="card-social-link"
              :href="social.href"
              target="_blank"
              rel="noopener noreferrer"
              :style="`--social-color: ${social.color}`"
            >
              <span class="card-social-icon"><SocialBrandIcon :name="social.name" /></span>
              <span>
                <small>{{ social.label }}</small>
                <strong>{{ social.handle }}</strong>
              </span>
              <i aria-hidden="true">↗</i>
            </a>
          </div>
        </div>

        <p class="card-service-note">
          <span /> Mobile appointments are available across Calgary.
        </p>
      </section>

      <section class="card-page-form" aria-label="Request a quote">
        <QuoteRequestForm request-label="Photo quote request" source="card" />
      </section>
    </main>

    <footer class="card-page-footer section-wrap">
      <span>© 2026 Monarch Auto Interior</span>
      <NuxtLink to="/">Services · Method · FAQ</NuxtLink>
    </footer>
  </div>
</template>
