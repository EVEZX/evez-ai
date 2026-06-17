import { generateText } from 'ai'
import { getModel } from '../utils/registry'

export interface ForecastResult {
  consensus: string
  confidence: number
  models: string[]
  latency: number
}

export class QuantumForecastAgent {
  private models: string[]

  constructor(models: string[] = ['gpt-4o', 'claude-3-5-sonnet-20240620', 'gemini-1.5-pro']) {
    this.models = models
  }

  async forecast(query: string): Promise<ForecastResult> {
    const startTime = Date.now()
    
    // Parallel execution for negative latency (concurrent processing)
    const predictions = await Promise.all(
      this.models.map(async (modelId) => {
        try {
          const { text } = await generateText({
            model: getModel(modelId),
            prompt: `Quantum Forecast: ${query}. Provide a concise, high-probability prediction.`
          })
          return { model: modelId, prediction: text }
        } catch (e) {
          return { model: modelId, prediction: null }
        }
      })
    )

    const validPredictions = predictions.filter(p => p.prediction !== null)
    const consensus = await this.calculateConsensus(validPredictions)
    
    return {
      consensus: consensus.text,
      confidence: consensus.score,
      models: validPredictions.map(p => p.model),
      latency: Date.now() - startTime
    }
  }

  private async calculateConsensus(predictions: any[]) {
    // Meta-model to aggregate predictions and determine consensus
    const { text } = await generateText({
      model: getModel('gpt-4o'),
      prompt: `Aggregate these predictions into a single consensus forecast:
      ${JSON.stringify(predictions)}
      Respond with the consensus text and a confidence score (0-1).`
    })
    
    // Simple score extraction for demo purposes
    const scoreMatch = text.match(/0\.\d+/)
    const score = scoreMatch ? parseFloat(scoreMatch[0]) : 0.8

    return { text, score }
  }
}
