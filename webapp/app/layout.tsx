import type { Metadata } from 'next'
import './globals.css'
import { Providers } from './providers'

export const metadata: Metadata = {
  title: 'IsDiscipline — Социальная сеть для тех, кто добивается',
  description: 'Общайся, достигай целей и прокачивай себя вместе с сообществом',
  icons: { icon: '/favicon.ico' },
  openGraph: {
    title: 'IsDiscipline',
    description: 'Социальная сеть нового поколения',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
