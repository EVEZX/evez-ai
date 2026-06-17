# Wallet Security Architecture

This document describes the secure wallet abstraction and transaction-intent pipeline implemented in crawhub.

## Overview

The wallet security system ensures that **wallet secrets (private keys, seed phrases, API client secrets) never appear in AI prompts, tool calls, application logs, or source control**. This is achieved through:

1. **Opaque identifiers** - Wallets are referenced by `WalletId`, never by secrets
2. **Unsigned transaction plans** - AI agents work with unsigned transaction intents
3. **Signing boundary** - Secret operations are isolated in the `Signer` interface
4. **Automatic redaction** - Centralized logger redacts secrets before logging
5. **CI guardrails** - Automated secret detection prevents accidental commits

## Threat Model

### What We Protect Against

1. **Secrets in AI Context**
   - Private keys appearing in Copilot chat responses
   - Seed phrases in tool call parameters
   - API secrets in agent prompts or outputs

2. **Accidental Exposure**
   - Secrets committed to git history
   - Secrets logged to application logs
   - Secrets sent in API responses

3. **Insider Threats**
   - Developers accidentally logging secrets
   - Test data containing real secrets
   - Debug output exposing sensitive data

### Security Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent/AI Layer (SAFE)                     │
│  - Uses WalletId references only                            │
│  - Creates unsigned transaction intents                      │
│  - Reviews transaction plans                                 │
│  - Queries transaction status                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               Application Layer (REDACTED)                   │
│  - Logger redacts secrets automatically                      │
│  - API validates inputs/outputs                              │
│  - No secrets in request/response bodies                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Signing Boundary (SECRET ZONE)                  │
│  - Signer interface accesses secrets                         │
│  - Secrets loaded from env/vault                             │
│  - Signs transactions                                        │
│  - Returns only public data (tx hashes)                      │
└─────────────────────────────────────────────────────────────┘
```

## Architecture

### Core Components

#### 1. Type System (`convex/lib/wallet/types.ts`)

Defines secure types that agents can safely use:

- `WalletId` - Opaque identifier for wallets
- `PublicAddress` - Public blockchain addresses
- `TxIntent` - Unsigned transaction description
- `TxPlan` - Transaction preview (unsigned)
- `TxReceipt` - Transaction result (no secrets)

**Key principle:** These types never contain or reference secrets.

#### 2. Wallet Operations (`convex/lib/wallet/wallet.ts`)

Agent-safe operations:

```typescript
// Get public address (no secrets required)
const address = await getPublicAddress(walletId, signer)

// Plan a transfer (creates unsigned plan)
const plan = await planTransfer({
  fromWalletId: 'wallet-1',
  toAddress: '0xabcd...',
  amount: '1.0',
  asset: { symbol: 'ETH', decimals: 18 },
  chain: Chain.ETHEREUM,
}, signer)
```

#### 3. Signer Interface (`convex/lib/wallet/signer.ts`)

The **signing boundary** where secrets are accessed:

```typescript
interface Signer {
  // Get public address (no secrets in/out)
  getPublicAddress(walletId: WalletId): Promise<PublicAddress>
  
  // Sign and broadcast (secrets used internally only)
  signAndBroadcast(intent: TxIntent): Promise<TxReceipt>
  
  // Estimate gas (read-only, no secrets needed)
  estimateGas(intent: TxIntent): Promise<string>
}
```

**Security requirements for Signer implementations:**

1. Load secrets from secure sources (env vars, vault)
2. NEVER return or log secrets
3. NEVER expose secrets in error messages
4. Validate all inputs before using secrets
5. Return only public data (addresses, tx hashes)

#### 4. Transaction Executor (`convex/lib/wallet/executor.ts`)

Executes transaction plans using the signer:

```typescript
// Execute a plan by ID (secrets stay in signer)
const receipt = await executeTransfer(planId, signer)

// Get transaction status (only public data)
const status = getTxStatus(planId)
```

#### 5. Secure Logger (`convex/lib/logger.ts`)

Automatically redacts secrets:

```typescript
import { logger } from './lib/logger'

// Safe: Public identifiers only
logger.info('Transfer planned', { 
  walletId: 'wallet-1',
  planId: 'plan-123',
  amount: '1.0'
})

// Protected: Even if you accidentally log secrets
logger.error('Error', { 
  privateKey: '0x1234...' // Will be [REDACTED]
})
```

**Redaction patterns:**

- Ethereum/EVM private keys (64 hex chars)
- Base58 private keys (Solana, Bitcoin)
- Mnemonic seed phrases (12-24 BIP39 words)
- JWT tokens
- API keys and tokens
- PEM private keys
- AWS access keys

### API Endpoints

#### POST `/api/v1/tx/plan`

Create an unsigned transaction plan.

**Request:**
```json
{
  "fromWalletId": "wallet-1",
  "toAddress": "0xabcd...",
  "amount": "1.0",
  "asset": {
    "symbol": "ETH",
    "decimals": 18
  },
  "chain": "ethereum"
}
```

**Response:**
```json
{
  "planId": "plan-1234567890-1",
  "intent": { ... },
  "estimatedGas": "21000",
  "estimatedFee": "0.00021",
  "fromAddress": "0x1234...",
  "createdAt": 1676543210000,
  "expiresAt": 1676546810000,
  "status": "pending"
}
```

#### POST `/api/v1/tx/execute`

Execute a transaction plan (signing happens server-side).

**Request:**
```json
{
  "planId": "plan-1234567890-1"
}
```

**Response:**
```json
{
  "planId": "plan-1234567890-1",
  "txHash": "0xabcdef...",
  "chain": "ethereum",
  "status": "confirmed",
  "blockNumber": 1000000,
  "confirmations": 1,
  "timestamp": 1676543220000,
  "gasUsed": "21000",
  "effectiveFee": "0.00021"
}
```

#### GET `/api/v1/tx/:id`

Get transaction status.

**Response:**
```json
{
  "planStatus": "completed",
  "receipt": {
    "planId": "plan-1234567890-1",
    "txHash": "0xabcdef...",
    "status": "confirmed",
    ...
  }
}
```

## Configuration

### Development Setup (Mock Signer)

For development and testing, use the `MockSigner` which requires no real secrets:

```bash
# .env.local
WALLET_SIGNER_TYPE=mock
```

The mock signer simulates blockchain operations without accessing real networks or requiring real private keys.

### Production Setup (Environment Variables)

For production, use the `EnvSigner` with secrets in environment variables:

```bash
# .env.local (NEVER COMMIT THIS FILE)
WALLET_SIGNER_TYPE=env

# Wallet secrets (examples - use your own secure values)
WALLET_HOT_1_KEY="..." # Load from secure vault
WALLET_HOT_2_KEY="..." # Load from secure vault
```

**Important:**

1. ✅ Store secrets in `.env.local` (gitignored)
2. ✅ Use different keys for dev/staging/production
3. ✅ Rotate keys regularly
4. ✅ Use hardware wallets for high-value wallets
5. ❌ NEVER commit secrets to git
6. ❌ NEVER log secrets
7. ❌ NEVER send secrets in API requests/responses

### Production Setup (Vault)

For enterprise deployments, use a secure vault:

```bash
# .env.local
WALLET_SIGNER_TYPE=vault
VAULT_ADDR=https://vault.example.com
VAULT_TOKEN=... # From secure source
```

Implement a custom `VaultSigner` that:

1. Authenticates to vault service
2. Retrieves wallet keys from vault
3. Uses keys for signing (never logs or returns them)
4. Implements automatic key rotation

## CI/CD Guardrails

### Secret Detection

The repository includes automated secret detection:

```bash
# Run locally before committing
node scripts/detect-secrets.js

# Check staged changes
node scripts/detect-secrets.js --staged
```

### GitHub Actions

The workflow `.github/workflows/secret-detection.yml` runs on every push and PR to detect:

- Private keys
- Seed phrases
- API tokens
- AWS credentials
- Other secret patterns

If secrets are detected, the workflow fails with details about what was found.

### Pre-commit Hook (Optional)

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
node scripts/detect-secrets.js --staged
exit $?
```

## Best Practices

### For Developers

1. **Never hardcode secrets**
   - Use environment variables
   - Use secure vaults
   - Generate test secrets, never use production keys

2. **Use the logger**
   - Always use `logger` from `convex/lib/logger`
   - Never use raw `console.log` for sensitive operations
   - Review logs before committing

3. **Review diffs**
   - Check diffs for secrets before committing
   - Run `node scripts/detect-secrets.js` locally
   - Use `.gitignore` for sensitive files

4. **Test with mock data**
   - Use `MockSigner` for development
   - Use test wallets with no real value
   - Never test with production keys

### For AI Agents

1. **Use opaque identifiers**
   - Reference wallets by `WalletId` only
   - Never request or store private keys
   - Work with unsigned transaction plans

2. **Review before execution**
   - Display transaction plans to users
   - Confirm amounts, addresses, fees
   - Verify chain and asset details

3. **Handle errors safely**
   - Log errors through redacted logger
   - Never expose secret values in errors
   - Use generic error messages

## Testing

### Unit Tests

Tests are located in `convex/lib/wallet/*.test.ts`:

```bash
# Run wallet abstraction tests
bun test convex/lib/wallet/

# Run logger redaction tests
bun test convex/lib/logger.test.ts
```

### Integration Tests

Test the API endpoints:

```bash
# Start local dev server
bun run dev

# In another terminal
curl -X POST http://localhost:3000/api/v1/tx/plan \
  -H "Content-Type: application/json" \
  -d '{
    "fromWalletId": "wallet-1",
    "toAddress": "0xabcd...",
    "amount": "1.0",
    "asset": {"symbol": "ETH", "decimals": 18},
    "chain": "ethereum"
  }'
```

### Security Tests

Verify secret redaction:

```bash
# Test that secrets are redacted
bun test convex/lib/logger.test.ts

# Test that API never exposes secrets
# (Check responses contain only public data)
```

## Incident Response

If a secret is accidentally exposed:

1. **Immediate Actions**
   - Rotate the exposed secret immediately
   - Revoke any tokens/keys that were exposed
   - Check for unauthorized transactions

2. **Investigation**
   - Review logs to find exposure source
   - Check git history for committed secrets
   - Audit who had access to the secret

3. **Remediation**
   - Remove secret from git history (use `git filter-branch`)
   - Update all systems using the old secret
   - Document the incident

4. **Prevention**
   - Review how the exposure occurred
   - Add additional detection patterns
   - Improve developer training

## Additional Resources

- [BIP39 Mnemonic Phrases](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki)
- [Ethereum Private Key Security](https://ethereum.org/en/developers/docs/accounts/)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)

## Support

For security concerns or questions:

1. Review this documentation
2. Check the code examples in `convex/lib/wallet/`
3. Run the test suite for examples
4. Open an issue (DO NOT include secrets in issues!)
