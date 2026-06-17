# Market Intelligence Module

This module provides market intelligence and analytics capabilities for the ops stack.

## Features

- Market data aggregation
- Trend analysis
- Canonical data hashing for data integrity

## Usage

```typescript
import { validateMarketData } from './market-intelligence/index.js';

const data = { market: 'crypto', timestamp: 1234567890 };
const hash = validateMarketData(data);
console.log('Market data hash:', hash);
```

## Testing

This module includes golden hash tests to ensure deterministic canonicalization of market data.
