/**
 * Root Layout
 * Member 3 - Frontend
 */

import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'CarVal - Vehicle Inspection & Valuation',
  description: 'AI-Powered Vehicle Inspection & Valuation Platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="bg-gray-50">
        {children}
      </body>
    </html>
  )
}
