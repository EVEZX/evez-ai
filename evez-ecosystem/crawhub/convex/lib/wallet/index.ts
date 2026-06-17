/**
 * Wallet abstraction module - Public API
 *
 * SECURITY: This module provides a secure wallet abstraction for AI agents.
 * No private keys, seed phrases, or secrets are exposed through this API.
 *
 * Usage:
 * - Agents use WalletId to reference wallets (no secrets)
 * - Plan transactions with planTransfer (creates unsigned plans)
 * - Execute transactions with executeTransfer (signing happens in isolated boundary)
 * - Query status with getTxStatus (only public data)
 */

// Export types
export type { WalletId, PublicAddress, TxIntent, TxPlan, TxReceipt, Asset } from './types'
export { Chain, Rail, createWalletId, createPublicAddress } from './types'

// Export signer interface (for extension)
export type { Signer, SignerConfig } from './signer'
export { MockSigner, EnvSigner, createSigner } from './signer'

// Export wallet operations (agent-safe)
export { getPublicAddress, planTransfer, getTxPlan, cleanupExpiredPlans } from './wallet'

// Export executor operations (signing boundary)
export { executeTransfer, getTxReceipt, getTxStatus } from './executor'
