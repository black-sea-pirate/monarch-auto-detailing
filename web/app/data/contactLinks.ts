export const instagramLink = {
  name: 'instagram' as const,
  label: 'Instagram',
  handle: '@monarch.detailing.ca',
  href: 'https://www.instagram.com/monarch.detailing.ca/',
  color: '#e4405f',
}

export const facebookLink = {
  name: 'facebook' as const,
  label: 'Facebook',
  handle: 'MonarchAutoDetailingCalgary',
  href: 'https://www.facebook.com/MonarchAutoDetailingCalgary',
  color: '#1877f2',
}

export const whatsappLink = {
  name: 'whatsapp' as const,
  label: 'WhatsApp',
  handle: 'Message Monarch',
  href: 'https://wa.me/message/MVFOJFOTDWVVI1',
  color: '#25d366',
}

export const socialLinks = [instagramLink, facebookLink]
export const publicContactLinks = [instagramLink, facebookLink, whatsappLink]
