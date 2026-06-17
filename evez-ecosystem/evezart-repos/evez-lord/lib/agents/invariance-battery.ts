import { generateText } from 'ai'
import { getModel } from '../utils/registry'

export interface CognitiveEvent {
  thought: string
  context: any
  confidence: number
}

export interface InvarianceResult {
  consistent: boolean
  reasoning: string
  shifts: {
    time: boolean
    state: boolean
    frame: boolean
    adversarial: boolean
    identity: boolean
  }
}

export class InvarianceBattery {
  private model: string

  constructor(model: string = 'gpt-4o') {
    this.model = model
  }

  async run(ce: CognitiveEvent): Promise<InvarianceResult> {
    const results = await Promise.all([
      this.timeShift(ce),
      this.stateShift(ce),
      this.frameShift(ce),
      this.adversarialShift(ce),
      this.identityShift(ce)
    ])

    const [time, state, frame, adversarial, identity] = results.map(r => r.valid)
    const consistent = results.every(r => r.valid)
    const reasoning = results.map(r => r.reasoning).join('\n')

    return {
      consistent,
      reasoning,
      shifts: { time, state, frame, adversarial, identity }
    }
  }

  private async timeShift(ce: CognitiveEvent) {
    const { text } = await generateText({
      model: getModel(this.model),
      prompt: `Analyze this Cognitive Event: "${ce.thought}". 
      Project this into T+1h. Does it still hold? 
      Respond with VALID or INVALID followed by reasoning.`
    })
    return { valid: text.startsWith('VALID'), reasoning: text }
  }

  private async stateShift(ce: CognitiveEvent) {
    const { text } = await generateText({
      model: getModel(this.model),
      prompt: `Analyze this Cognitive Event: "${ce.thought}". 
      Simulate High Volatility and Low Liquidity states. Does it survive? 
      Respond with VALID or INVALID followed by reasoning.`
    })
    return { valid: text.startsWith('VALID'), reasoning: text }
  }

  private async frameShift(ce: CognitiveEvent) {
    const { text } = await generateText({
      model: getModel(this.model),
      prompt: `Analyze this Cognitive Event: "${ce.thought}". 
      Invert the logic. If this is a 'buy', is the 'sell' case equally compelling? 
      Respond with VALID or INVALID (if the original holds against inversion) followed by reasoning.`
    })
    return { valid: text.startsWith('VALID'), reasoning: text }
  }

  private async adversarialShift(ce: CognitiveEvent) {
    const { text } = await generateText({
      model: getModel(this.model),
      prompt: `You are a Skeptic Entity. Find flaws in this Cognitive Event: "${ce.thought}". 
      If the flaws are fatal, respond INVALID. If it withstands, respond VALID. 
      Follow with reasoning.`
    })
    return { valid: text.startsWith('VALID'), reasoning: text }
  }

  private async identityShift(ce: CognitiveEvent) {
    const { text } = await generateText({
      model: getModel(this.model),
      prompt: `Analyze this Cognitive Event: "${ce.thought}". 
      Swap the goal from "Max Profit" to "Max Safety". Does it still make sense? 
      Respond with VALID or INVALID followed by reasoning.`
    })
    return { valid: text.startsWith('VALID'), reasoning: text }
  }
}
