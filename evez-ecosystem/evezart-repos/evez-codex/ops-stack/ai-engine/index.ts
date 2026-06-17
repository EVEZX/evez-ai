import { canonicalize } from 'json-canonicalize';

/**
 * Runs inference and returns canonical representation of request
 * @param request - Inference request
 * @returns Canonical JSON string for hashing
 */
export function runInference(request: Record<string, any>): string {
  const canonical = canonicalize(request);
  return canonical;
}

/**
 * Example inference request data for testing
 */
export const sampleInferenceRequest = {
  model: 'gpt-4-turbo',
  prompt: 'Explain quantum computing',
  temperature: 0.7,
  max_tokens: 500,
  timestamp: 1234567890
};
