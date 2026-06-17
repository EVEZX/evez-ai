# Ops Stack Integration Guide

This guide provides detailed information on integrating canonical hashing libraries across multiple languages and running the ops-stack.

## Table of Contents
- [Overview](#overview)
- [Language-Specific Setup](#language-specific-setup)
- [Running Golden Hash Tests](#running-golden-hash-tests)
- [Deployment](#deployment)
- [CI/CD Integration](#cicd-integration)

## Overview

The ops-stack provides a unified approach to canonical JSON serialization (RFC 8785) across multiple languages. This ensures deterministic hashing for:
- Cryptographic signing
- Data verification
- Cache keys
- Distributed system consensus

## Language-Specific Setup

### Node.js/TypeScript

**Installation:**
```bash
npm install json-canonicalize
# or
pnpm add json-canonicalize
```

**Usage:**
```typescript
import { canonicalize } from 'json-canonicalize';

const data = { foo: 'bar', baz: 42 };
const canonical = canonicalize(data);
// Result: '{"baz":42,"foo":"bar"}'
```

### Python

**Installation:**
```bash
pip install rfc8785
```

**Usage:**
```python
import rfc8785

data = {'foo': 'bar', 'baz': 42}
canonical = rfc8785.dumps(data)
# Result: b'{"baz":42,"foo":"bar"}'
```

### Go

**Installation:**
```bash
go get github.com/cyberphone/json-canonicalization/go/src/webpki.org/jsoncanonicalizer
```

**Usage:**
```go
import "github.com/cyberphone/json-canonicalization/go/src/webpki.org/jsoncanonicalizer"

jsonBytes := []byte(`{"foo":"bar","baz":42}`)
canonical, err := jsoncanonicalizer.Transform(jsonBytes)
// Result: {"baz":42,"foo":"bar"}
```

### Rust

**Installation:**
Add to `Cargo.toml`:
```toml
[dependencies]
serde_jcs = "0.1"
serde = { version = "1.0", features = ["derive"] }
```

**Usage:**
```rust
use serde::Serialize;
use serde_jcs;

#[derive(Serialize)]
struct Data {
    foo: String,
    baz: i32,
}

let data = Data { foo: "bar".to_string(), baz: 42 };
let canonical = serde_jcs::to_string(&data)?;
// Result: {"baz":42,"foo":"bar"}
```

### Java

**Maven:**
```xml
<dependency>
    <groupId>org.webpki</groupId>
    <artifactId>webpki.org</artifactId>
    <version>1.0.0</version>
</dependency>
```

**Gradle:**
```gradle
implementation 'org.webpki:webpki.org:1.0.0'
```

**Usage:**
```java
import org.webpki.json.JSONObjectWriter;
import org.webpki.json.JSONOutputFormats;

String canonical = new JSONObjectWriter(json)
    .serializeToString(JSONOutputFormats.CANONICALIZED);
```

## Running Golden Hash Tests

### Quick Start
```bash
cd ops-stack
pnpm install
pnpm test
```

### Individual Module Tests
Each module can be tested independently:
```bash
cd ops-stack
node --loader tsx/esm market-intelligence/index.ts
node --loader tsx/esm notifications/index.ts
# ... etc
```

### Language-Specific Examples
```bash
# Python
cd ops-stack/examples
python3 python_example.py

# Go
cd ops-stack/examples
go run go_example.go

# Rust
cd ops-stack/examples
rustc rust_example.rs && ./rust_example
```

## Deployment

### Using the Deployment Script
```bash
./deploy-ops-stack.sh

# Optional: validate a real health endpoint during smoke tests
OPS_STACK_HEALTHCHECK_URL=https://ops-stack.example.com/health ./deploy-ops-stack.sh
```

The script performs:
1. Preflight checks (Node.js, pnpm, TypeScript)
2. Dependency installation
3. TypeScript build (fails fast if compilation fails)
4. Golden hash tests
5. Mock deployment steps
6. Optional live smoke test when `OPS_STACK_HEALTHCHECK_URL` is set

### Manual Deployment
```bash
cd ops-stack
pnpm install
pnpm build
pnpm test
# Then deploy dist/ directory
```

## CI/CD Integration

### GitHub Actions
The repository includes `.github/workflows/ops-stack-ci.yml` which:
- Runs on every PR affecting ops-stack files
- Tests canonical hashing in Node.js, Python, Go, and Rust
- Validates the deployment script
- Ensures cross-language compatibility

### Running CI Locally
```bash
# Install act (https://github.com/nektos/act)
act pull_request -W .github/workflows/ops-stack-ci.yml
```

## Module Architecture

### Market Intelligence
- Data validation
- Analytics with canonical hashing
- See: `ops-stack/market-intelligence/`

### Notifications
- Multi-channel delivery
- Audit trails with canonical hashing
- See: `ops-stack/notifications/`

### Automation
- Workflow orchestration
- State tracking with canonical hashing
- See: `ops-stack/automation/`

### Monetization
- Payment processing
- Financial records with canonical hashing
- See: `ops-stack/monetization/`

### AI Engine
- Model inference
- Request/response hashing
- See: `ops-stack/ai-engine/`

## Best Practices

1. **Always use canonical serialization for signing**: Ensures consistent signatures across platforms
2. **Test cross-language compatibility**: Run tests in multiple languages to verify consistency
3. **Version your data schemas**: Changes to data structure affect canonical output
4. **Include timestamps carefully**: Only when needed for audit trails
5. **Document golden hashes**: Keep expected outputs in version control

## Troubleshooting

### Import Errors (Node.js)
Use named imports for `json-canonicalize`:
```typescript
import { canonicalize } from 'json-canonicalize';
// NOT: import canonicalize from 'json-canonicalize';
```

### Python bytes vs string
`rfc8785.dumps()` returns bytes. Convert to string if needed:
```python
canonical = rfc8785.dumps(data).decode('utf-8')
```

### Go module errors
Ensure you're in a Go module:
```bash
go mod init your-module-name
go get github.com/cyberphone/json-canonicalization/go/src/webpki.org/jsoncanonicalizer
```

### Rust compilation errors
Ensure serde features are enabled:
```toml
serde = { version = "1.0", features = ["derive"] }
```

## Resources

- [RFC 8785 - JSON Canonicalization Scheme (JCS)](https://www.rfc-editor.org/rfc/rfc8785)
- [json-canonicalize npm package](https://www.npmjs.com/package/json-canonicalize)
- [rfc8785 Python package](https://pypi.org/project/rfc8785/)
- [WebPKI JSON Canonicalization (Go)](https://github.com/cyberphone/json-canonicalization)
- [serde_jcs Rust crate](https://crates.io/crates/serde_jcs)
