# AI Engine Module

This module provides AI model management and inference capabilities.

## Features

- Model deployment and versioning
- Inference pipeline management
- Canonical data hashing for model artifacts and predictions

## Usage

```typescript
import { runInference } from './ai-engine/index.js';

const request = {
  model: 'gpt-4',
  input: 'Hello, world!'
};
const hash = runInference(request);
console.log('Inference request hash:', hash);
```

## Testing

This module includes golden hash tests to ensure deterministic canonicalization of AI requests.
