/**
 * Wallet abstraction module - Agent-safe wallet operations
 *
 * SECURITY: This module provides wallet operations that AI agents can safely use
 * without ever accessing or exposing wallet secrets (private keys, seed phrases).
 *
 * Agents can only:
 * - Reference wallets by WalletId
 * - Get public addresses
 * - Create transaction plans (unsigned)
 * - Check transaction status
 *
 * Actual signing and secret management happens in the Signer boundary.
 */

import type { PublicAddress, TxIntent, TxPlan, WalletId } from './types'
import { createPublicAddress } from './types'
import type { Signer } from './signer'

/**
 * In-memory store for transaction plans
 * In production, this would be stored in a database
 */
const txPlans = new Map<string, TxPlan>()
let planIdCounter = 0

/**
 * Get the public address for a wallet
 *
 * SECURITY: This function does NOT require or expose private keys.
 * It only returns the public address which is safe to display.
 */
export async function getPublicAddress(walletId: WalletId, signer: Signer): Promise<PublicAddress> {
  return await signer.getPublicAddress(walletId)
}

/**
 * Plan a transfer transaction (unsigned)
 *
 * SECURITY: This creates an unsigned transaction plan that agents can inspect.
 * No secrets are required or exposed. The plan can be reviewed before execution.
 */
export async function planTransfer(intent: TxIntent, signer: Signer): Promise<TxPlan> {
  // Validate intent
  if (!intent.fromWalletId) {
    throw new Error('fromWalletId is required')
  }
  if (!intent.toAddress) {
    throw new Error('toAddress is required')
  }
  if (!intent.amount || Number.parseFloat(intent.amount) <= 0) {
    throw new Error('amount must be positive')
  }
  if (!intent.chain) {
    throw new Error('chain is required')
  }

  // Get the from address (no secrets required)
  const fromAddress = await signer.getPublicAddress(intent.fromWalletId)

  // Estimate gas (may require read-only blockchain access)
  let estimatedGas: string | undefined
  let estimatedFee: string | undefined
  try {
    estimatedGas = await signer.estimateGas(intent)
    // Calculate estimated fee based on gas (simplified)
    estimatedFee = (Number.parseFloat(estimatedGas) * 0.00001).toString()
  } catch (error) {
    // Gas estimation is optional - may not be available in all environments
    console.warn('Failed to estimate gas:', error)
  }

  // Create plan
  planIdCounter++
  const planId = `plan-${Date.now()}-${planIdCounter}`
  const now = Date.now()

  const plan: TxPlan = {
    planId,
    intent,
    estimatedGas,
    estimatedFee,
    fromAddress,
    createdAt: now,
    expiresAt: now + 3600000, // 1 hour expiry
    status: 'pending',
  }

  // Store plan
  txPlans.set(planId, plan)

  return plan
}

/**
 * Get a transaction plan by ID
 */
export function getTxPlan(planId: string): TxPlan | undefined {
  return txPlans.get(planId)
}

/**
 * Update transaction plan status
 */
export function updateTxPlanStatus(planId: string, status: TxPlan['status']): void {
  const plan = txPlans.get(planId)
  if (plan) {
    plan.status = status
    txPlans.set(planId, plan)
  }
}

/**
 * Validate that a plan is ready for execution
 */
export function validatePlanForExecution(plan: TxPlan): void {
  if (plan.status !== 'pending') {
    throw new Error(`Plan is not pending: ${plan.status}`)
  }

  if (Date.now() > plan.expiresAt) {
    throw new Error('Plan has expired')
  }
}

/**
 * Clean up expired plans (should be called periodically)
 */
export function cleanupExpiredPlans(): number {
  const now = Date.now()
  let cleaned = 0

  for (const [planId, plan] of txPlans.entries()) {
    if (now > plan.expiresAt && plan.status === 'pending') {
      plan.status = 'expired'
      cleaned++
    }
  }

  return cleaned
}
