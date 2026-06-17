import { canonicalize } from 'json-canonicalize';

/**
 * Processes a payment and returns canonical representation
 * @param payment - Payment details
 * @returns Canonical JSON string for hashing
 */
export function processPayment(payment: Record<string, any>): string {
  const canonical = canonicalize(payment);
  return canonical;
}

/**
 * Example payment data for testing
 */
export const samplePayment = {
  id: 'pay-001',
  amount: 99.99,
  currency: 'USD',
  customer: 'cust-12345',
  timestamp: 1234567890,
  method: 'credit_card'
};
