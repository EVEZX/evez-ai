# Ops Stack

A comprehensive operational stack with canonical hashing support for data integrity and golden hash testing.

## Architecture

The ops-stack consists of five core modules:

- **market-intelligence/** - Market data aggregation and analytics
- **notifications/** - Multi-channel notification delivery
- **automation/** - Workflow automation and orchestration
- **monetization/** - Billing and payment processing
- **ai-engine/** - AI model management and inference

Each module implements canonical JSON serialization (RFC 8785) using the `json-canonicalize` library for deterministic hashing.

## Quick Start

### Installation

```bash
cd ops-stack
pnpm install
```

### Running Golden Hash Tests

```bash
# Using npm scripts
pnpm test

# Or directly
node --loader ts-node/esm ops-stack.ts
```

### Building

```bash
pnpm build
```

## Golden Hash Tests

The ops-stack includes deterministic canonicalization tests to ensure data integrity across all modules. These tests validate that data structures are serialized consistently, which is critical for:

- Cryptographic signing
- Data verification
- Cache keys
- Distributed system consensus

Each module's sample data is canonicalized and compared against expected "golden" hashes to ensure consistency.

## Multi-Language Support

While the main ops-stack is implemented in TypeScript, the devcontainer includes support for canonical hashing libraries in multiple languages:

### Node.js/TypeScript
```typescript
import canonicalize from 'json-canonicalize';
const canonical = canonicalize(data);
```

### Python
```python
import rfc8785
canonical = rfc8785.dumps(data)
```

### Go
```go
import "github.com/cyberphone/json-canonicalization/go/src/webpki.org/jsoncanonicalizer"
canonical, _ := jsoncanonicalizer.Transform(jsonBytes)
```

### Rust
```rust
use serde_jcs;
let canonical = serde_jcs::to_string(&data)?;
```

### Java
```java
import org.webpki.json.JSONObjectWriter;
String canonical = new JSONObjectWriter(json).serializeToString(JSONOutputFormats.CANONICALIZED);
```

## Modules

### Market Intelligence
Provides market data validation and analytics with canonical hashing for data integrity.

### Notifications
Handles notification delivery with canonical hashing for audit trails.

### Automation
Manages workflow execution with canonical state tracking.

### Monetization
Processes payments with canonical hashing for financial record integrity.

### AI Engine
Manages AI model inference with canonical request/response hashing.

## Development

### Local Setup

1. Install dependencies:
   ```bash
   pnpm install
   ```

2. Run tests:
   ```bash
   pnpm test
   ```

3. Build:
   ```bash
   pnpm build
   ```

### GitHub Codespaces

This repository includes a devcontainer configuration optimized for Codespaces:

1. Click "Code" → "Create codespace on main"
2. Wait for the container to build (includes all language tooling)
3. Run tests: `cd ops-stack && pnpm test`

The devcontainer includes:
- Node.js (v22) with pnpm, TypeScript, ts-node
- Rust with cargo and rustfmt
- Go 1.22+
- Python 3 with pip
- Java 21 with Maven and Gradle
- Docker
- All canonical hashing libraries pre-installed

## CI/CD

The ops-stack includes GitHub Actions workflows for continuous integration:

- **ops-stack-ci.yml** - Runs golden hash tests on every PR

## License

Apache-2.0
