/**
 * Root Layout
 * Member 3 - Frontend
 * Global styles and metadata
 */

import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'CarVal - AI Vehicle Intelligence',
  description: 'Next-generation vehicle inspection & valuation platform powered by advanced AI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="bg-black text-white antialiased">
        {children}
      </body>
    </html>
  )
}
