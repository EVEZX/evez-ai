import { describe, expect, it } from 'vitest'
import { redactSecrets, redactObject } from './logger'

describe('Logger Redaction', () => {
  describe('redactSecrets', () => {
    it('redacts ethereum private keys', () => {
      const text = 'My key is 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
      const redacted = redactSecrets(text)

      expect(redacted).toBe('My key is [REDACTED]')
    })

    it('redacts private keys without 0x prefix', () => {
      const text = 'Key: 1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
      const redacted = redactSecrets(text)

      expect(redacted).toBe('Key: [REDACTED]')
    })

    it('redacts JWT tokens', () => {
      const text =
        'Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U'
      const redacted = redactSecrets(text)

      expect(redacted).toBe('Token: [REDACTED]')
    })

    it('redacts PEM private keys', () => {
      const text = `Key:
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj
-----END PRIVATE KEY-----`
      const redacted = redactSecrets(text)

      expect(redacted).toContain('[REDACTED]')
      expect(redacted).not.toContain('BEGIN PRIVATE KEY')
    })

    it('redacts API keys with common patterns', () => {
      const text = 'api_key: sk_test_1234567890abcdefghijklmnop'
      const redacted = redactSecrets(text)

      // The entire api_key pattern is matched and redacted
      expect(redacted).toBe('[REDACTED]')
    })

    it('does not redact normal text', () => {
      const text = 'This is a normal log message with userId 123 and amount 1.5'
      const redacted = redactSecrets(text)

      expect(redacted).toBe(text)
    })

    it('does not redact short hex strings', () => {
      const text = 'Transaction hash: 0x1234567890abcdef'
      const redacted = redactSecrets(text)

      // Short hashes should not be redacted (they're not private keys)
      expect(redacted).toBe(text)
    })
  })

  describe('redactObject', () => {
    it('redacts secrets in nested objects', () => {
      const obj = {
        userId: '123',
        wallet: {
          address: '0xabcd',
          privateKey: '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
        },
      }

      const redacted = redactObject(obj)

      expect(redacted).toEqual({
        userId: '123',
        wallet: {
          address: '0xabcd',
          privateKey: '[REDACTED]',
        },
      })
    })

    it('redacts secrets by field name', () => {
      const obj = {
        apiKey: 'sk_test_123456',
        api_secret: 'secret_value',
        publicData: 'visible',
      }

      const redacted = redactObject(obj)

      expect(redacted).toEqual({
        apiKey: '[REDACTED]',
        api_secret: '[REDACTED]',
        publicData: 'visible',
      })
    })

    it('redacts secrets in arrays', () => {
      const obj = {
        keys: [
          {
            name: 'key1',
            value: '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
          },
          { name: 'key2', value: 'public_value' },
        ],
      }

      const redacted = redactObject(obj)

      expect(redacted).toEqual({
        keys: [
          { name: 'key1', value: '[REDACTED]' },
          { name: 'key2', value: 'public_value' },
        ],
      })
    })

    it('handles null and undefined', () => {
      expect(redactObject(null)).toBe(null)
      expect(redactObject(undefined)).toBe(undefined)
    })

    it('handles primitives', () => {
      expect(redactObject(123)).toBe(123)
      expect(redactObject(true)).toBe(true)
      expect(redactObject('text')).toBe('text')
    })

    it('redacts mnemonic phrases', () => {
      const obj = {
        seed: 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        mnemonic: 'test test test test test test test test test test test junk',
      }

      const redacted = redactObject(obj)

      expect(redacted).toEqual({
        seed: '[REDACTED]',
        mnemonic: '[REDACTED]',
      })
    })

    it('redacts seed phrase field name', () => {
      const obj = {
        seedPhrase: 'any value here',
        seed_phrase: 'another value',
      }

      const redacted = redactObject(obj)

      expect(redacted).toEqual({
        seedPhrase: '[REDACTED]',
        seed_phrase: '[REDACTED]',
      })
    })
  })
})
