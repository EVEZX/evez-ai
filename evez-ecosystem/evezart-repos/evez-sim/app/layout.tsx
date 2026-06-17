import type { Metadata } from 'next'
import ClarityInit from '@/components/ClarityInit'

export const metadata: Metadata = {
  title: 'EVEZ-OS Simulation',
  description: 'Barnes-Hut force-graph - FSC ENGINE - dual-descent physics',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0, background: '#000a03', overflow: 'hidden' }}>
        <ClarityInit />
        {children}
      </body>
    </html>
  )
}