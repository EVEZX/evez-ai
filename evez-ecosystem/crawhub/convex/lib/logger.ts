/**
 * Secure logging with automatic secret redaction
 *
 * SECURITY: This logger automatically redacts sensitive information before logging.
 * It protects against accidental exposure of:
 * - Private keys (hex, base58, etc.)
 * - Seed phrases / mnemonic phrases
 * - API tokens and secrets
 * - Other sensitive patterns
 *
 * Usage:
 *   import { logger } from './logger'
 *   logger.info('User action', { userId, walletId })  // Safe
 *   logger.error('Failed', { error })  // Redacted automatically
 */

/**
 * Patterns that indicate secrets - these will be redacted
 */
const SECRET_PATTERNS = [
  // Ethereum/EVM private keys (64 hex chars, often prefixed with 0x)
  /\b(0x)?[0-9a-fA-F]{64}\b/g,

  // Base58 private keys (Solana, Bitcoin, etc.) - typically 43-44 chars
  /\b[1-9A-HJ-NP-Za-km-z]{43,44}\b/g,

  // Mnemonic seed phrases (12, 15, 18, 21, 24 words from BIP39 wordlist)
  /\b(abandon|ability|able|about|above|absent|absorb|abstract|absurd|abuse|access|accident|account|accuse|achieve|acid|acoustic|acquire|across|act|action|actor|actress|actual|adapt|add|addict|address|adjust|admit|adult|advance|advice|aerobic|affair|afford|afraid|again|age|agent|agree|ahead|aim|air|airport|aisle|alarm|album|alcohol|alert|alien|all|alley|allow|almost|alone|alpha|already|also|alter|always|amateur|amazing|among|amount|amused|analyst|anchor|ancient|anger|angle|angry|animal|ankle|announce|annual|another|answer|antenna|antique|anxiety|any|apart|apology|appear|apple|approve|april|arch|arctic|area|arena|argue|arm|armed|armor|army|around|arrange|arrest|arrive|arrow|art|artefact|artist|artwork|ask|aspect|assault|asset|assist|assume|asthma|athlete|atom|attack|attend|attitude|attract|auction|audit|august|aunt|author|auto|autumn|average|avocado|avoid|awake|aware|away|awesome|awful|awkward|axis|baby|bachelor|bacon|badge|bag|balance|balcony|ball|bamboo|banana|banner|bar|barely|bargain|barrel|base|basic|basket|battle|beach|bean|beauty|because|become|beef|before|begin|behave|behind|believe|below|belt|bench|benefit|best|betray|better|between|beyond|bicycle|bid|bike|bind|biology|bird|birth|bitter|black|blade|blame|blanket|blast|bleak|bless|blind|blood|blossom|blouse|blue|blur|blush|board|boat|body|boil|bomb|bone|bonus|book|boost|border|boring|borrow|boss|bottom|bounce|box|boy|bracket|brain|brand|brass|brave|bread|breeze|brick|bridge|brief|bright|bring|brisk|broccoli|broken|bronze|broom|brother|brown|brush|bubble|buddy|budget|buffalo|build|bulb|bulk|bullet|bundle|bunker|burden|burger|burst|bus|business|busy|butter|buyer|buzz)(\s+\w+){11,23}\b/gi,

  // Common API token patterns
  /\b(api[_-]?key|api[_-]?token|access[_-]?token|auth[_-]?token|bearer\s+)[:\s=]*[^\s\n]{20,}\b/gi,

  // JWT tokens
  /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/g,

  // Private key markers in PEM format
  /-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(RSA\s+)?PRIVATE\s+KEY-----/gi,

  // Extended private keys (xprv)
  /\bxprv[0-9A-Za-z]{100,}\b/g,

  // AWS access keys
  /\b(AKIA|A3T|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[0-9A-Z]{16}\b/g,
]

/**
 * Common secret field names - values of these will be redacted
 */
const SECRET_FIELD_NAMES = new Set([
  'privateKey',
  'private_key',
  'privatekey',
  'secretKey',
  'secret_key',
  'secretkey',
  'apiKey',
  'api_key',
  'apikey',
  'apiSecret',
  'api_secret',
  'apisecret',
  'accessToken',
  'access_token',
  'accesstoken',
  'authToken',
  'auth_token',
  'authtoken',
  'password',
  'passwd',
  'pwd',
  'mnemonic',
  'seedPhrase',
  'seed_phrase',
  'seedphrase',
  'seed',
])

/**
 * Redact secrets from a string
 */
export function redactSecrets(text: string): string {
  let redacted = text

  for (const pattern of SECRET_PATTERNS) {
    redacted = redacted.replace(pattern, '[REDACTED]')
  }

  return redacted
}

/**
 * Redact secrets from an object (deep)
 */
export function redactObject(obj: unknown): unknown {
  if (obj === null || obj === undefined) {
    return obj
  }

  if (typeof obj === 'string') {
    return redactSecrets(obj)
  }

  if (typeof obj !== 'object') {
    return obj
  }

  if (Array.isArray(obj)) {
    return obj.map((item) => redactObject(item))
  }

  const redacted: Record<string, unknown> = {}

  for (const [key, value] of Object.entries(obj)) {
    // If the key name suggests it's a secret, redact the entire value
    if (SECRET_FIELD_NAMES.has(key) || SECRET_FIELD_NAMES.has(key.toLowerCase())) {
      redacted[key] = '[REDACTED]'
    } else {
      redacted[key] = redactObject(value)
    }
  }

  return redacted
}

/**
 * Logger levels
 */
export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
}

/**
 * Secure logger interface
 */
export interface Logger {
  debug(message: string, data?: unknown): void
  info(message: string, data?: unknown): void
  warn(message: string, data?: unknown): void
  error(message: string, data?: unknown): void
}

/**
 * Secure logger implementation with automatic redaction
 */
class SecureLogger implements Logger {
  private minLevel: LogLevel

  constructor(minLevel: LogLevel = LogLevel.INFO) {
    this.minLevel = minLevel
  }

  private shouldLog(level: LogLevel): boolean {
    const levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR]
    return levels.indexOf(level) >= levels.indexOf(this.minLevel)
  }

  private log(level: LogLevel, message: string, data?: unknown): void {
    if (!this.shouldLog(level)) {
      return
    }

    const timestamp = new Date().toISOString()
    const redactedMessage = redactSecrets(message)
    const redactedData = data ? redactObject(data) : undefined

    const logEntry = {
      timestamp,
      level,
      message: redactedMessage,
      ...(redactedData ? { data: redactedData } : {}),
    }

    // In production, this would send to a logging service
    console.log(JSON.stringify(logEntry))
  }

  debug(message: string, data?: unknown): void {
    this.log(LogLevel.DEBUG, message, data)
  }

  info(message: string, data?: unknown): void {
    this.log(LogLevel.INFO, message, data)
  }

  warn(message: string, data?: unknown): void {
    this.log(LogLevel.WARN, message, data)
  }

  error(message: string, data?: unknown): void {
    this.log(LogLevel.ERROR, message, data)
  }
}

/**
 * Default logger instance
 *
 * SAFE USAGE:
 *   logger.info('User logged in', { userId: '123', walletId: 'wallet-1' })
 *   logger.error('Transfer failed', { error, planId: 'plan-123' })
 *
 * UNSAFE (but will be redacted):
 *   logger.info('Key', { privateKey: '0x123...' })  // Will be redacted
 *   logger.error('Error', { error: 'Failed with key 0x123...' })  // Will be redacted
 */
export const logger = new SecureLogger(
  process.env.LOG_LEVEL === 'debug' ? LogLevel.DEBUG : LogLevel.INFO,
)

/**
 * Create a logger with custom configuration
 */
export function createLogger(minLevel: LogLevel): Logger {
  return new SecureLogger(minLevel)
}
