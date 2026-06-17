/**
 * Signer interface for wallet operations.
 *
 * SECURITY: This interface abstracts secret management and ensures that
 * private keys, seed phrases, and API secrets never leave the signer boundary.
 * All secret operations happen behind this interface.
 */

import type { Chain, PublicAddress, TxIntent, TxReceipt, WalletId } from './types'

/**
 * Signer configuration - stored securely outside codebase
 */
export interface SignerConfig {
  // Secrets are loaded from environment or secure vault
  // NEVER hardcoded or logged
  type: 'env' | 'vault' | 'mock'
}

/**
 * Signer interface - the execution boundary for secret operations
 *
 * Implementations MUST:
 * - Load secrets from secure sources (env vars, OS keychain, vault)
 * - NEVER return or log secrets
 * - NEVER expose secrets in error messages
 * - Validate all inputs before using secrets
 */
export interface Signer {
  /**
   * Get public address for a wallet (no secrets required)
   */
  getPublicAddress(walletId: WalletId): Promise<PublicAddress>

  /**
   * Sign and broadcast a transaction
   *
   * SECURITY: This is the only method that accesses secrets.
   * It must never return or log private keys.
   */
  signAndBroadcast(intent: TxIntent): Promise<TxReceipt>

  /**
   * Estimate gas for a transaction (may require read-only chain access)
   */
  estimateGas(intent: TxIntent): Promise<string>

  /**
   * Get supported chains
   */
  getSupportedChains(): Chain[]
}

/**
 * Mock/NOOP signer for development and testing
 *
 * This signer does NOT require real secrets and is safe for dev environments.
 * It simulates transaction operations without accessing real blockchains.
 */
export class MockSigner implements Signer {
  private mockWallets: Map<WalletId, PublicAddress> = new Map()
  private mockTxCounter = 0

  constructor() {
    // Pre-populate with test wallets (these are NOT real private keys)
    this.mockWallets.set(
      'wallet-1' as WalletId,
      '0x1234567890123456789012345678901234567890' as PublicAddress,
    )
    this.mockWallets.set(
      'wallet-2' as WalletId,
      '0xabcdefabcdefabcdefabcdefabcdefabcdefabcd' as PublicAddress,
    )
    this.mockWallets.set(
      'wallet-sol-1' as WalletId,
      'SoL1111111111111111111111111111111111111111' as PublicAddress,
    )
  }

  async getPublicAddress(walletId: WalletId): Promise<PublicAddress> {
    const address = this.mockWallets.get(walletId)
    if (!address) {
      throw new Error(`Unknown wallet ID: ${walletId}`)
    }
    return address
  }

  async signAndBroadcast(intent: TxIntent): Promise<TxReceipt> {
    // Simulate transaction broadcast
    this.mockTxCounter++
    const txHash = `0xmock${this.mockTxCounter.toString().padStart(60, '0')}`

    return {
      planId: '', // Will be set by caller
      txHash,
      chain: intent.chain,
      status: 'confirmed',
      blockNumber: 1000000 + this.mockTxCounter,
      confirmations: 1,
      timestamp: Date.now(),
      gasUsed: '21000',
      effectiveFee: '0.001',
    }
  }

  async estimateGas(intent: TxIntent): Promise<string> {
    // Return mock gas estimate based on chain
    switch (intent.chain) {
      case 'solana':
        return '5000'
      default:
        return '21000'
    }
  }

  getSupportedChains(): Chain[] {
    return [
      'ethereum' as Chain,
      'polygon' as Chain,
      'arbitrum' as Chain,
      'optimism' as Chain,
      'base' as Chain,
      'solana' as Chain,
    ]
  }
}

/**
 * Environment-based signer that reads secrets from environment variables
 *
 * SECURITY: This signer reads private keys from environment variables.
 * - Private keys MUST be stored in .env.local (never committed)
 * - Keys MUST be named with WALLET_ prefix for easy identification
 * - This signer MUST NOT log or return the actual keys
 */
export class EnvSigner implements Signer {
  private walletEnvMap: Map<WalletId, string> = new Map()

  constructor(walletIds: WalletId[]) {
    // Map wallet IDs to their env var names
    // The actual secrets stay in process.env and are never exposed
    for (const walletId of walletIds) {
      const envKey = `WALLET_${walletId.toUpperCase().replace(/-/g, '_')}_KEY`
      this.walletEnvMap.set(walletId, envKey)
    }
  }

  async getPublicAddress(walletId: WalletId): Promise<PublicAddress> {
    const envKey = this.walletEnvMap.get(walletId)
    if (!envKey) {
      throw new Error(`Wallet not configured: ${walletId}`)
    }

    // In a real implementation, derive public address from private key
    // WITHOUT exposing the private key
    throw new Error('EnvSigner.getPublicAddress: Not implemented - requires crypto library')
  }

  async signAndBroadcast(intent: TxIntent): Promise<TxReceipt> {
    const envKey = this.walletEnvMap.get(intent.fromWalletId)
    if (!envKey) {
      throw new Error(`Wallet not configured: ${intent.fromWalletId}`)
    }

    // In a real implementation:
    // 1. Read private key from process.env[envKey] (NEVER log it)
    // 2. Sign the transaction
    // 3. Broadcast to the network
    // 4. Return receipt with tx hash (NO SECRETS)

    throw new Error('EnvSigner.signAndBroadcast: Not implemented - requires blockchain client')
  }

  async estimateGas(intent: TxIntent): Promise<string> {
    // In a real implementation, query the blockchain for gas estimate
    throw new Error('EnvSigner.estimateGas: Not implemented - requires blockchain client')
  }

  getSupportedChains(): Chain[] {
    // Would be determined by configured RPC endpoints
    return []
  }
}

/**
 * Create a signer based on configuration
 */
export function createSigner(config: SignerConfig): Signer {
  switch (config.type) {
    case 'mock':
      return new MockSigner()
    case 'env':
      // In production, this would read wallet IDs from config
      throw new Error('EnvSigner requires wallet configuration')
    case 'vault':
      throw new Error('Vault signer not yet implemented')
    default:
      throw new Error(`Unknown signer type: ${config.type}`)
  }
}
