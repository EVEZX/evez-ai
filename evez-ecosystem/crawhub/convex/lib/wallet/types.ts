/**
 * Wallet abstraction types for secure transaction handling.
 *
 * SECURITY: These types ensure that wallet secrets (private keys, seed phrases)
 * never appear in AI prompts, tool calls, or application logs.
 */

/**
 * Opaque identifier for a wallet. Never contains or reveals private keys.
 * Used by agents to reference wallets without exposing secrets.
 */
export type WalletId = string & { readonly __brand: 'WalletId' }

/**
 * Blockchain network identifier
 */
export enum Chain {
  ETHEREUM = 'ethereum',
  POLYGON = 'polygon',
  ARBITRUM = 'arbitrum',
  OPTIMISM = 'optimism',
  BASE = 'base',
  SOLANA = 'solana',
}

/**
 * Rail/protocol identifier for cross-chain transfers
 */
export enum Rail {
  NATIVE = 'native',
  BRIDGE = 'bridge',
  CROSS_CHAIN_SWAP = 'cross-chain-swap',
}

/**
 * Public blockchain address (safe to display)
 */
export type PublicAddress = string & { readonly __brand: 'PublicAddress' }

/**
 * Asset type for transfers
 */
export interface Asset {
  symbol: string
  decimals: number
  contractAddress?: string
}

/**
 * Unsigned transaction intent - safe for AI agents to handle
 */
export interface TxIntent {
  fromWalletId: WalletId
  toAddress: PublicAddress
  amount: string
  asset: Asset
  chain: Chain
  rail?: Rail
  memo?: string
}

/**
 * Transaction plan with preview information (unsigned)
 */
export interface TxPlan {
  planId: string
  intent: TxIntent
  estimatedGas?: string
  estimatedFee?: string
  fromAddress: PublicAddress
  createdAt: number
  expiresAt: number
  status: 'pending' | 'executing' | 'completed' | 'failed' | 'expired'
}

/**
 * Transaction receipt after execution
 */
export interface TxReceipt {
  planId: string
  txHash: string
  chain: Chain
  status: 'pending' | 'confirmed' | 'failed'
  blockNumber?: number
  confirmations?: number
  timestamp: number
  gasUsed?: string
  effectiveFee?: string
}

/**
 * Helper to create a WalletId from a string
 */
export function createWalletId(id: string): WalletId {
  return id as WalletId
}

/**
 * Helper to create a PublicAddress from a string
 */
export function createPublicAddress(address: string): PublicAddress {
  return address as PublicAddress
}
