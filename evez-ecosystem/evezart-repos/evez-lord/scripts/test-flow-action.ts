import { createHmac } from 'crypto'

const FLOW_SECRET = 'evez-secret-key'
const payload = JSON.stringify({
  query: 'Should I buy BTC at $100k?',
  model: 'gpt-4o',
  searchMode: 'quick'
})

const hmac = createHmac('sha256', FLOW_SECRET)
const signature = hmac.update(payload).digest('hex')

console.log('--- EVEZ Flow Action Test ---')
console.log('Payload:', payload)
console.log('Signature:', signature)
console.log('--- Run this command to test: ---')
console.log(`curl -X POST http://localhost:3000/api/flow-action \\
  -H "Content-Type: application/json" \\
  -H "x-evez-signature: ${signature}" \\
  -d '${payload}'`)
