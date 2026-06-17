/**
 * Transaction executor - The signing boundary
 *
 * SECURITY: This module is the ONLY place where secrets are accessed for signing.
 * It ensures that:
 * - Secrets never leave the signer boundary
 * - Transaction plans are validated before execution
 * - Results contain only public information (tx hashes, receipts)
 * - Errors never expose secrets
 */

import type { TxPlan, TxReceipt } from './types'
import type { Signer } from './signer'
import { getTxPlan, updateTxPlanStatus, validatePlanForExecution } from './wallet'

/**
 * In-memory store for transaction receipts
 * In production, this would be stored in a database
 */
const txReceipts = new Map<string, TxReceipt>()

/**
 * Execute a transaction plan
 *
 * SECURITY: This is the execution boundary where secrets are used.
 * The signer handles all secret operations internally.
 * This function only deals with plan IDs and public data.
 *
 * @param planId - The transaction plan ID
 * @param signer - The signer instance (manages secrets internally)
 * @returns Transaction receipt (no secrets)
 */
export async function executeTransfer(planId: string, signer: Signer): Promise<TxReceipt> {
  // Get the plan
  const plan = getTxPlan(planId)
  if (!plan) {
    throw new Error(`Transaction plan not found: ${planId}`)
  }

  // Validate plan
  try {
    validatePlanForExecution(plan)
  } catch (error) {
    throw new Error(
      `Plan validation failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
    )
  }

  // Mark plan as executing
  updateTxPlanStatus(planId, 'executing')

  try {
    // Execute via signer (secrets stay inside signer boundary)
    const receipt = await signer.signAndBroadcast(plan.intent)

    // Add plan ID to receipt
    receipt.planId = planId

    // Store receipt
    txReceipts.set(planId, receipt)

    // Update plan status
    updateTxPlanStatus(planId, 'completed')

    return receipt
  } catch (error) {
    // Mark plan as failed
    updateTxPlanStatus(planId, 'failed')

    // Re-throw error (signer should sanitize error messages)
    throw new Error(
      `Transaction execution failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
    )
  }
}

/**
 * Get transaction receipt by plan ID
 */
export function getTxReceipt(planId: string): TxReceipt | undefined {
  return txReceipts.get(planId)
}

/**
 * Get transaction status
 */
export function getTxStatus(planId: string): {
  planStatus: TxPlan['status']
  receipt?: TxReceipt
} {
  const plan = getTxPlan(planId)
  if (!plan) {
    throw new Error(`Transaction plan not found: ${planId}`)
  }

  const receipt = txReceipts.get(planId)

  return {
    planStatus: plan.status,
    receipt,
  }
}
