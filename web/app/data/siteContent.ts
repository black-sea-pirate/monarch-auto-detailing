export const priceKeys = [
  'maintenance',
  'deep',
  'complete',
  'pet_hair',
  'extraction',
  'leather',
  'salt_stain',
  'suv_surcharge',
  'large_vehicle_surcharge',
] as const

export type PriceKey = typeof priceKeys[number]

export type PriceSetting = {
  base_price_cents: number
  discount_price_cents: number | null
  discount_enabled: boolean
}

export type SiteSections = {
  pricing_enabled: boolean
  portfolio_enabled: boolean
  founding_offer_enabled: boolean
}

export type PortfolioImage = {
  id: string
  caption: string | null
  url: string
  after_url: string | null
}

export type PublicSiteContent = {
  pricing: Record<PriceKey, PriceSetting>
  sections: SiteSections
  portfolio: PortfolioImage[]
  version: number
}

const regularPrice = (basePriceCents: number): PriceSetting => ({
  base_price_cents: basePriceCents,
  discount_price_cents: null,
  discount_enabled: false,
})

export const defaultSiteContent: PublicSiteContent = {
  pricing: {
    maintenance: regularPrice(9900),
    deep: regularPrice(17900),
    complete: regularPrice(24900),
    pet_hair: regularPrice(4500),
    extraction: regularPrice(2500),
    leather: regularPrice(3000),
    salt_stain: regularPrice(3000),
    suv_surcharge: regularPrice(2500),
    large_vehicle_surcharge: regularPrice(5000),
  },
  sections: {
    pricing_enabled: true,
    portfolio_enabled: false,
    founding_offer_enabled: false,
  },
  portfolio: [],
  version: 1,
}

export function cloneDefaultSiteContent(): PublicSiteContent {
  return JSON.parse(JSON.stringify(defaultSiteContent)) as PublicSiteContent
}

export function activePrice(setting: PriceSetting): number {
  return setting.discount_enabled && setting.discount_price_cents !== null
    ? setting.discount_price_cents
    : setting.base_price_cents
}

export function formatCad(cents: number): string {
  return new Intl.NumberFormat('en-CA', {
    maximumFractionDigits: cents % 100 === 0 ? 0 : 2,
    minimumFractionDigits: cents % 100 === 0 ? 0 : 2,
  }).format(cents / 100)
}
