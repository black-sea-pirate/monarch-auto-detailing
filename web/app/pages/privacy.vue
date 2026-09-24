<script setup lang="ts">
const siteUrl = 'https://monarch-yyc.com'

useSeoMeta({
  title: 'Privacy Policy | Monarch Auto Detailing',
  description: 'How Monarch Auto Detailing handles quote requests, contact details, photos and videos.',
  ogType: 'website',
  ogUrl: `${siteUrl}/privacy`,
  ogTitle: 'Privacy Policy | Monarch Auto Detailing',
  ogDescription: 'How we use and protect the information you send with a quote request.',
})

useHead({
  link: [{ rel: 'canonical', href: `${siteUrl}/privacy` }],
})
</script>

<template>
  <div class="card-page privacy-page">
    <header class="card-page-header section-wrap">
      <NuxtLink class="brand" to="/" aria-label="Monarch home">
        <img class="brand-symbol" src="/brand/monarch-symbol-gold.svg" alt="" width="44" height="45">
        <img class="brand-wordmark" src="/brand/monarch-wordmark-on-dark.svg" alt="Monarch Auto Detailing" width="142" height="38">
      </NuxtLink>
      <NuxtLink class="card-home-link" to="/">Back to website <span aria-hidden="true">↗</span></NuxtLink>
    </header>

    <main class="privacy-content section-wrap">
      <div class="privacy-intro">
        <p class="eyebrow"><i /> Monarch Auto Detailing · Calgary</p>
        <h1>Privacy policy</h1>
        <p>When you request a quote, you trust us with your contact details and sometimes photos or videos of your vehicle. This page explains what happens to them.</p>
        <span>Last updated September 23, 2026</span>
      </div>

      <div class="privacy-sections">
        <section aria-labelledby="privacy-collect">
          <h2 id="privacy-collect">What we collect</h2>
          <p>A quote request includes your name, preferred contact method and contact details, vehicle type, service area, selected services and anything you write in the form. You may also choose to upload photos and videos. We record a request number and dates needed to manage the request. Our website and security providers may process basic technical information, such as your IP address and browser requests.</p>
          <p>Please avoid including people, documents, licence plates or other private details in photos and videos unless they are needed to explain the work.</p>
        </section>

        <section aria-labelledby="privacy-use">
          <h2 id="privacy-use">Why we use it</h2>
          <p>We use this information to review your vehicle, prepare a quote, contact you through your chosen method and manage the request. We also use limited technical information to operate and protect the website. We do not sell your information or use your quote request for marketing messages without asking separately.</p>
        </section>

        <section aria-labelledby="privacy-sharing">
          <h2 id="privacy-sharing">Who handles it</h2>
          <p>Your full request and uploaded media are kept in a restricted admin inbox on our Amazon Lightsail server in Montréal, Canada. Cloudflare delivers and protects the website and admin access. A Telegram notification to the owner contains the request number, vehicle type, service area, selected services and the number of files. It does not include your name, contact details, written description or uploaded media.</p>
          <p>The site also loads fonts from Google. Cloudflare may process web traffic in Canada, the United States and other countries on its global network. Telegram may store the short notification in data centres outside Canada, and Google may process technical connection data outside Canada. If you contact us through WhatsApp or another social link, that service handles your message under its own privacy terms.</p>
          <p>We do not currently add advertising pixels or separate visitor analytics scripts to these pages. Cloudflare may use cookies needed to secure the website.</p>
        </section>

        <section aria-labelledby="privacy-retention">
          <h2 id="privacy-retention">How long we keep it</h2>
          <p>Unfinished quote drafts and their uploads are scheduled for removal after 24 hours. If we accept a request for follow-up, its name, contact details, written description, service area and uploads are scheduled for removal 30 days after acceptance. Requests that are not accepted are scheduled for removal 90 days after creation. You can ask us to remove your contact details and media sooner.</p>
          <p>After that removal, a limited record can remain in the system, including the request number, vehicle type, selected services, dates, status and notification or admin activity. Technical logs and copies held by service providers may follow separate retention periods.</p>
          <p>Messages you later exchange with us by email, WhatsApp or another contact service are separate from the quote inbox and may remain there until deleted separately.</p>
        </section>

        <section aria-labelledby="privacy-contact">
          <h2 id="privacy-contact">Your questions and choices</h2>
          <p>To ask what information we have, request a correction or deletion, or withdraw consent, email our owner and privacy contact at <a href="mailto:andrii.kodzhebash@gmail.com">andrii.kodzhebash@gmail.com</a>. We may need to confirm that a request is yours before sharing or changing your information. You can also ask about how our service providers handle information outside Canada.</p>
        </section>

        <section aria-labelledby="privacy-changes">
          <h2 id="privacy-changes">Changes to this policy</h2>
          <p>We will update this page if the way we handle information changes. The date above shows when this version was last updated.</p>
        </section>
      </div>
    </main>

    <footer class="card-page-footer section-wrap">
      <span>© 2026 Monarch Auto Detailing</span>
      <NuxtLink to="/">Back to website</NuxtLink>
    </footer>
  </div>
</template>
