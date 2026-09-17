<script setup lang="ts">
useHead({
  title: 'Request an Interior Detail | Monarch Calgary',
  meta: [
    {
      name: 'description',
      content: 'Request a photo-based interior detailing quote from Monarch in Royal Oak and nearby NW Calgary communities.',
    },
  ],
})

const socialLinks = [
  {
    name: 'instagram' as const,
    label: 'Instagram',
    handle: '@monarch.detailing.ca',
    href: 'https://www.instagram.com/monarch.detailing.ca/',
    color: '#e4405f',
  },
  {
    name: 'facebook' as const,
    label: 'Facebook',
    handle: 'MonarchAutoDetailingCalgary',
    href: 'https://www.facebook.com/MonarchAutoDetailingCalgary',
    color: '#1877f2',
  },
]
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
        <p class="eyebrow"><i /> Royal Oak · Calgary NW</p>
        <h1 id="card-page-title">Request your<br><em>interior detail.</em></h1>
        <p class="card-page-lede">
          Tell us how to reach you, what your vehicle needs and attach a few clear photos. We will review everything and confirm the scope before booking.
        </p>

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
          <span /> By appointment in Royal Oak and nearby NW Calgary communities.
        </p>
      </section>

      <section class="card-page-form" aria-label="Request a quote">
        <QuoteRequestForm request-label="Card / quote" source="card" />
      </section>
    </main>

    <footer class="card-page-footer section-wrap">
      <span>© 2026 Monarch Auto Interior</span>
      <NuxtLink to="/">Services · Method · FAQ</NuxtLink>
    </footer>
  </div>
</template>
