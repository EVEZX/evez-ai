import { describe, expect, it, beforeEach } from 'vitest'
import { MockSigner } from './signer'
import { getPublicAddress, planTransfer, getTxPlan, cleanupExpiredPlans } from './wallet'
import { executeTransfer, getTxReceipt, getTxStatus } from './executor'
import { Chain, createWalletId, createPublicAddress } from './types'
import type { TxIntent } from './types'

describe('Wallet Abstraction', () => {
  let signer: MockSigner

  beforeEach(() => {
    signer = new MockSigner()
  })

  describe('getPublicAddress', () => {
    it('returns public address for known wallet', async () => {
      const walletId = createWalletId('wallet-1')
      const address = await getPublicAddress(walletId, signer)

      expect(address).toBe('0x1234567890123456789012345678901234567890')
    })

    it('throws for unknown wallet', async () => {
      const walletId = createWalletId('unknown-wallet')

      await expect(getPublicAddress(walletId, signer)).rejects.toThrow('Unknown wallet ID')
    })
  })

  describe('planTransfer', () => {
    it('creates a transaction plan', async () => {
      const intent: TxIntent = {
        fromWalletId: createWalletId('wallet-1'),
        toAddress: createPublicAddress('0xabcdefabcdefabcdefabcdefabcdefabcdefabcd'),
        amount: '1.0',
        asset: { symbol: 'ETH', decimals: 18 },
        chain: Chain.ETHEREUM,
      }

      const plan = await planTransfer(intent, signer)

      expect(plan.planId).toBeTruthy()
      expect(plan.intent).toEqual(intent)
      expect(plan.fromAddress).toBe('0x1234567890123456789012345678901234567890')
      expect(plan.status).toBe('pending')
      expect(plan.estimatedGas).toBe('21000')
    })

    it('validates required fields', async () => {
      const invalidIntent: TxIntent = {
        fromWalletId: createWalletId(''),
        toAddress: createPublicAddress('0xabcd'),
        amount: '',
        asset: { symbol: 'ETH', decimals: 18 },
        chain: Chain.ETHEREUM,
      }

      await expect(planTransfer(invalidIntent, signer)).rejects.toThrow()
    })

    it('rejects negative amounts', async () => {
      const intent: TxIntent = {
        fromWalletId: createWalletId('wallet-1'),
        toAddress: createPublicAddress('0xabcdefabcdefabcdefabcdefabcdefabcdefabcd'),
        amount: '-1.0',
        asset: { symbol: 'ETH', decimals: 18 },
        chain: Chain.ETHEREUM,
      }

      await expect(planTransfer(intent, signer)).rejects.toThrow('amount must be positive')
    })
  })

  describe('getTxPlan', () => {
    it('retrieves stored plan', async () => {
      const intent: TxIntent = {
        fromWalletId: createWalletId('wallet-1'),
        toAddress: createPublicAddress('0xabcdefabcdefabcdefabcdefabcdefabcdefabcd'),
        amount: '1.0',
        asset: { symbol: 'ETH', decimals: 18 },
        chain: Chain.ETHEREUM,
      }

      const plan = await planTransfer(intent, signer)
      const retrieved = getTxPlan(plan.planId)

      expect(retrieved).toEqual(plan)
    })

    it('returns undefined for unknown plan', () => {
      const retrieved = getTxPlan('non-existent-plan')
      expect(retrieved).toBeUndefined()
    })
  })

  describe('executeTransfer', () => {
    it('executes a valid plan', async () => {
      const intent: TxIntent = {
        fromWalletId: createWalletId('wallet-1'),
        toAddress: createPublicAddress('0xabcdefabcdefabcdefabcdefabcdefabcdefabcd'),
        amount: '1.0',
        asset: { symbol: 'ETH', decimals: 18 },
        chain: Chain.ETHEREUM,
      }

      const plan = await planTransfer(intent, signer)
      const receipt = await executeTransfer(plan.planId, signer)

      expect(receipt.planId).toBe(plan.planId)
      expect(receipt.txHash).toBeTruthy()
      expect(receipt.status).toBe('confirmed')
      expect(receipt.chain).toBe(Chain.ETHEREUM)
    })

    it('rejects execution of non-existent plan', async () => {
      await expect(executeTransfer('non-existent', signer)).rejects.toThrow(
        'Transaction plan not found',
      )
    })

    it('updates plan status after execution', async () => {
      const intent: TxIntent = {
        fromWalletId: createWalletId('wallet-1'),
        toAddress: createPublicAddress('0xabcdefabcdefabcdefabcdefabcdefabcdefabcd'),
        amount: '1.0',
        asset: { symbol: 'ETH', decimals: 18 },
        chain: Chain.ETHEREUM,
      }

      const plan = await planTransfer(intent, signer)
      await executeTransfer(plan.planId, signer)

      const updatedPlan = getTxPlan(plan.planId)
      expect(updatedPlan?.status).toBe('completed')
    })
  })

  describe('getTxStatus', () => {
    it('returns status for completed transaction', async () => {
      const intent: TxIntent = {
        fromWalletId: createWalletId('wallet-1'),
        toAddress: createPublicAddress('0xabcdefabcdefabcdefabcdefabcdefabcdefabcd'),
        amount: '1.0',
        asset: { symbol: 'ETH', decimals: 18 },
        chain: Chain.ETHEREUM,
      }

      const plan = await planTransfer(intent, signer)
      await executeTransfer(plan.planId, signer)

      const status = getTxStatus(plan.planId)

      expect(status.planStatus).toBe('completed')
      expect(status.receipt).toBeTruthy()
      expect(status.receipt?.txHash).toBeTruthy()
    })

    it('throws for non-existent plan', () => {
      expect(() => getTxStatus('non-existent')).toThrow('Transaction plan not found')
    })
  })

  describe('cleanupExpiredPlans', () => {
    it('marks expired plans', async () => {
      const intent: TxIntent = {
        fromWalletId: createWalletId('wallet-1'),
        toAddress: createPublicAddress('0xabcdefabcdefabcdefabcdefabcdefabcdefabcd'),
        amount: '1.0',
        asset: { symbol: 'ETH', decimals: 18 },
        chain: Chain.ETHEREUM,
      }

      const plan = await planTransfer(intent, signer)

      // Force expiry
      plan.expiresAt = Date.now() - 1000

      const cleaned = cleanupExpiredPlans()

      expect(cleaned).toBeGreaterThan(0)

      const updatedPlan = getTxPlan(plan.planId)
      expect(updatedPlan?.status).toBe('expired')
    })
  })
})
