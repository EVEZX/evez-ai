import { NextRequest, NextResponse } from 'next/server'
import { createResearcher } from '@/lib/agents/researcher'
import { InvarianceBattery } from '@/lib/agents/invariance-battery'
import { QuantumForecastAgent } from '@/lib/agents/quantum-forecast'
import { createHmac } from 'crypto'

const FLOW_SECRET = process.env.FLOW_SECRET || 'evez-secret-key'

function verifyHmac(req: NextRequest, body: string) {
  const signature = req.headers.get('x-evez-signature')
  if (!signature) return false
  const hmac = createHmac('sha256', FLOW_SECRET)
  const digest = hmac.update(body).digest('hex')
  return signature === digest
}

export async function POST(req: NextRequest) {
  const bodyText = await req.text()
  
  if (process.env.NODE_ENV !== 'development' && !verifyHmac(req, bodyText)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const payload = JSON.parse(bodyText)
  const { query, model = 'gpt-4o', searchMode = 'adaptive' } = payload

  try {
    // 1. Generate Cognitive Event (CE)
    const researcher = createResearcher({ model, searchMode })
    const result = await researcher.generate({
      messages: [{ role: 'user', content: query }]
    })
    
    const ce = {
      thought: result.text,
      context: payload,
      confidence: 0.9 // Placeholder for actual confidence scoring
    }

    // 2. Run Invariance Battery
    const battery = new InvarianceBattery(model)
    const invarianceResult = await battery.run(ce)

    // 3. Quantum Forecast (Negative Latency Consensus)
    const forecaster = new QuantumForecastAgent()
    const forecast = await forecaster.forecast(query)

    // 4. Return result with consistency flag for n8n branching
    return NextResponse.json({
      consistent: invarianceResult.consistent,
      cognitiveEvent: ce,
      invarianceDetails: invarianceResult,
      quantumForecast: forecast,
      timestamp: new Date().toISOString()
    })

  } catch (error: any) {
    console.error('Flow Action Error:', error)
    return NextResponse.json({ 
      consistent: false, 
      error: error.message,
      retry: true 
    }, { status: 500 })
  }
}
