# Monetization Module

This module handles billing, subscriptions, and revenue management.

## Features

- Subscription management
- Payment processing
- Canonical data hashing for financial record integrity

## Usage

```typescript
import { processPayment } from './monetization/index.js';

const payment = {
  amount: 99.99,
  currency: 'USD',
  customer: 'cust_123'
};
const hash = processPayment(payment);
console.log('Payment hash:', hash);
```

## Testing

This module includes golden hash tests to ensure deterministic canonicalization of financial records.
