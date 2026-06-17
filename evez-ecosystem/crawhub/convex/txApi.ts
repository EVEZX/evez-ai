/**
 * HTTP API handlers for transaction planning and execution
 *
 * SECURITY: These handlers provide the agent-safe interface for wallet operations.
 * All handlers validate inputs and ensure no secrets are exposed in responses.
 */

import { httpAction } from './_generated/server'
import { api } from './_generated/api'
import type { TxIntent, TxPlan, TxReceipt } from './lib/wallet/types'
import { Chain, createWalletId, createPublicAddress } from './lib/wallet/types'
import { planTransfer, getTxPlan } from './lib/wallet/wallet'
import { executeTransfer, getTxReceipt, getTxStatus } from './lib/wallet/executor'
import { createSigner } from './lib/wallet/signer'
import { logger } from './lib/logger'

/**
 * Create a signer instance based on environment
 * In production, this would read from secure configuration
 */
function getSigner() {
  const signerType = process.env.WALLET_SIGNER_TYPE || 'mock'
  return createSigner({ type: signerType as 'mock' | 'env' | 'vault' })
}

/**
 * POST /api/v1/tx/plan
 *
 * Create a transaction plan (unsigned)
 *
 * Request body:
 * {
 *   fromWalletId: string,
 *   toAddress: string,
 *   amount: string,
 *   asset: { symbol: string, decimals: number, contractAddress?: string },
 *   chain: string,
 *   rail?: string,
 *   memo?: string
 * }
 *
 * Response:
 * {
 *   planId: string,
 *   intent: TxIntent,
 *   estimatedGas?: string,
 *   estimatedFee?: string,
 *   fromAddress: string,
 *   createdAt: number,
 *   expiresAt: number,
 *   status: string
 * }
 */
export const txPlanHttp = httpAction(async (ctx, request) => {
  try {
    const body = await request.json()

    // Validate required fields
    if (!body.fromWalletId || typeof body.fromWalletId !== 'string') {
      return new Response(JSON.stringify({ error: 'fromWalletId is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    if (!body.toAddress || typeof body.toAddress !== 'string') {
      return new Response(JSON.stringify({ error: 'toAddress is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    if (!body.amount || typeof body.amount !== 'string') {
      return new Response(JSON.stringify({ error: 'amount is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    if (!body.asset || typeof body.asset !== 'object') {
      return new Response(JSON.stringify({ error: 'asset is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    if (!body.chain || !Object.values(Chain).includes(body.chain)) {
      return new Response(JSON.stringify({ error: 'valid chain is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    // Create intent
    const intent: TxIntent = {
      fromWalletId: createWalletId(body.fromWalletId),
      toAddress: createPublicAddress(body.toAddress),
      amount: body.amount,
      asset: body.asset,
      chain: body.chain as Chain,
      rail: body.rail,
      memo: body.memo,
    }

    // Create plan
    const signer = getSigner()
    const plan = await planTransfer(intent, signer)

    logger.info('Transaction plan created', {
      planId: plan.planId,
      fromWalletId: body.fromWalletId,
      toAddress: body.toAddress,
      amount: body.amount,
      chain: body.chain,
    })

    return new Response(JSON.stringify(plan), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })
  } catch (error) {
    logger.error('Failed to create transaction plan', { error })

    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : 'Failed to create transaction plan',
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      },
    )
  }
})

/**
 * POST /api/v1/tx/execute
 *
 * Execute a transaction plan
 *
 * Request body:
 * {
 *   planId: string
 * }
 *
 * Response:
 * {
 *   planId: string,
 *   txHash: string,
 *   chain: string,
 *   status: string,
 *   blockNumber?: number,
 *   confirmations?: number,
 *   timestamp: number,
 *   gasUsed?: string,
 *   effectiveFee?: string
 * }
 */
export const txExecuteHttp = httpAction(async (ctx, request) => {
  try {
    const body = await request.json()

    // Validate plan ID
    if (!body.planId || typeof body.planId !== 'string') {
      return new Response(JSON.stringify({ error: 'planId is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    // Execute transaction
    const signer = getSigner()
    const receipt = await executeTransfer(body.planId, signer)

    logger.info('Transaction executed', {
      planId: body.planId,
      txHash: receipt.txHash,
      chain: receipt.chain,
      status: receipt.status,
    })

    return new Response(JSON.stringify(receipt), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })
  } catch (error) {
    logger.error('Failed to execute transaction', { error })

    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : 'Failed to execute transaction',
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      },
    )
  }
})

/**
 * GET /api/v1/tx/:id
 *
 * Get transaction status
 *
 * Response:
 * {
 *   planStatus: string,
 *   receipt?: TxReceipt
 * }
 */
export const txStatusHttp = httpAction(async (ctx, request) => {
  try {
    const url = new URL(request.url)
    const pathParts = url.pathname.split('/')
    const planId = pathParts[pathParts.length - 1]

    if (!planId) {
      return new Response(JSON.stringify({ error: 'planId is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    const status = getTxStatus(planId)

    return new Response(JSON.stringify(status), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })
  } catch (error) {
    logger.error('Failed to get transaction status', { error })

    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : 'Failed to get transaction status',
      }),
      {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      },
    )
  }
})
