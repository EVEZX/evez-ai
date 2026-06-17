import { canonicalize } from 'json-canonicalize';

/**
 * Validates market data by computing a canonical hash
 * @param data - Market data object to validate
 * @returns Canonical JSON string for hashing
 */
export function validateMarketData(data: Record<string, any>): string {
  const canonical = canonicalize(data);
  return canonical;
}

/**
 * Example market data for testing
 */
export const sampleMarketData = {
  market: 'cryptocurrency',
  ticker: 'BTC-USD',
  price: 50000,
  timestamp: 1234567890,
  volume: 1000000
};
