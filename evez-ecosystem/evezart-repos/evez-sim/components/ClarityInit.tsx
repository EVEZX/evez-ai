'use client'

import { useEffect, useRef } from 'react'

declare global {
  interface Window {
    clarity: (action: string, event?: string, data?: Record<string, unknown>) => void
  }
}

const CLARITY_PROJECT_ID = process.env.NEXT_PUBLIC_CLARITY_PROJECT_ID || ''

export default function ClarityInit() {
  const prevFireRef = useRef<string | null>(null)

  useEffect(() => {
    if (!CLARITY_PROJECT_ID) return

    const script = document.createElement('script')
    script.innerHTML = '(function(c,l,a,r,i,t,y){c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);})(window,document,"clarity","script","' + CLARITY_PROJECT_ID + '");'
    document.head.appendChild(script)

    const pollBusState = async () => {
      try {
        const res = await fetch('/api/bus-state')
        if (!res.ok) return
        const data = await res.json()
        if (!window.clarity) return

        window.clarity('event', 'bus_state_tick', {
          n: data.n,
          fire: data.fire,
          ceiling: data.ceiling || false,
          poly_c: data.poly_c,
          v_global: data.v_global,
          loops: data.loops || 0
        })

        const prevFire = prevFireRef.current
        if (prevFire !== null && prevFire !== data.fire) {
          window.clarity('event', 'bus_fire_transition', {
            from: prevFire,
            to: data.fire,
            n: data.n
          })
        }
        prevFireRef.current = data.fire

        if (data.ceiling) {
          window.clarity('event', 'bus_ceiling_event', {
            n: data.n,
            ceiling_type: data.ceiling_label || 'CEILING'
          })
        }
      } catch {
        // silent
      }
    }

    pollBusState()
    const interval = setInterval(pollBusState, 30000)
    return () => clearInterval(interval)
  }, [])

  return null
}