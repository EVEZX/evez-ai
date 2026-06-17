#!/usr/bin/env node

/**
 * Secret detection script for CI/CD pipeline
 *
 * This script scans git diffs for potential secrets to prevent them from being committed.
 * It checks for:
 * - Private keys (hex, base58, PEM)
 * - Mnemonic seed phrases
 * - API tokens and keys
 * - AWS credentials
 * - Other common secret patterns
 *
 * Usage:
 *   node scripts/detect-secrets.js [--staged]
 *
 * Exit codes:
 *   0 - No secrets detected
 *   1 - Secrets detected (fails CI)
 *   2 - Script error
 */

import { execSync } from 'node:child_process'
import * as process from 'node:process'

// Secret patterns to detect
const SECRET_PATTERNS = [
  {
    name: 'Ethereum/EVM Private Key',
    pattern: /\b(0x)?[0-9a-fA-F]{64}\b/g,
    description: '64-character hex string (private key)',
  },
  {
    name: 'Base58 Private Key',
    pattern: /\b[1-9A-HJ-NP-Za-km-z]{43,44}\b/g,
    description: 'Base58 encoded key (Solana, Bitcoin)',
  },
  {
    name: 'Mnemonic Seed Phrase',
    pattern:
      /\b(abandon|ability|able|about|above|absent|absorb|abstract|absurd|abuse|access|accident|account|accuse|achieve|acid|acoustic|acquire|across|act|action|actor|actress|actual|adapt|add|addict|address|adjust|admit|adult|advance|advice|aerobic|affair|afford|afraid|again|age|agent|agree|ahead|aim|air|airport|aisle|alarm|album|alcohol|alert|alien|all|alley|allow|almost|alone|alpha|already|also|alter|always|amateur|amazing|among|amount|amused|analyst|anchor|ancient|anger|angle|angry|animal|ankle|announce|annual|another|answer|antenna|antique|anxiety|any|apart|apology|appear|apple|approve|april|arch|arctic|area|arena|argue|arm|armed|armor|army|around|arrange|arrest|arrive|arrow|art|artefact|artist|artwork|ask|aspect|assault|asset|assist|assume|asthma|athlete|atom|attack|attend|attitude|attract|auction|audit|august|aunt|author|auto|autumn|average|avocado|avoid|awake|aware|away|awesome|awful|awkward|axis|baby|bachelor|bacon|badge|bag|balance|balcony|ball|bamboo|banana|banner|bar|barely|bargain|barrel|base|basic|basket|battle|beach|bean|beauty|because|become|beef|before|begin|behave|behind|believe|below|belt|bench|benefit|best|betray|better|between|beyond|bicycle|bid|bike|bind|biology|bird|birth|bitter|black|blade|blame|blanket|blast|bleak|bless|blind|blood|blossom|blouse|blue|blur|blush|board|boat|body|boil|bomb|bone|bonus|book|boost|border|boring|borrow|boss|bottom|bounce|box|boy|bracket|brain|brand|brass|brave|bread|breeze|brick|bridge|brief|bright|bring|brisk|broccoli|broken|bronze|broom|brother|brown|brush|bubble|buddy|budget|buffalo|build|bulb|bulk|bullet|bundle|bunker|burden|burger|burst|bus|business|busy|butter|buyer|buzz)(\s+\w+){11,23}\b/gi,
    description: 'BIP39 mnemonic phrase (12-24 words)',
  },
  {
    name: 'JWT Token',
    pattern: /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/g,
    description: 'JSON Web Token',
  },
  {
    name: 'PEM Private Key',
    pattern: /-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----/gi,
    description: 'PEM format private key',
  },
  {
    name: 'Extended Private Key',
    pattern: /\bxprv[0-9A-Za-z]{100,}\b/g,
    description: 'BIP32 extended private key',
  },
  {
    name: 'AWS Access Key',
    pattern: /\b(AKIA|A3T|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[0-9A-Z]{16}\b/g,
    description: 'AWS access key ID',
  },
  {
    name: 'API Key Pattern',
    pattern: /\b(api[_-]?key|api[_-]?token|access[_-]?token)[:\s=]+["']?[^\s"']{20,}["']?\b/gi,
    description: 'API key or token',
  },
  {
    name: 'Generic Secret Pattern',
    pattern: /\b(secret|password|passwd|pwd)[:\s=]+["']?[^\s"']{8,}["']?\b/gi,
    description: 'Generic secret or password',
  },
]

// Files to exclude from scanning
const EXCLUDED_PATTERNS = [
  'package-lock.json',
  'bun.lock',
  'yarn.lock',
  'pnpm-lock.yaml',
  '.lock',
  'detect-secrets.js', // This file itself
  'wallet/types.ts', // Type definitions (no actual secrets)
  'wallet.test.ts', // Test files with mock data
  'logger.test.ts', // Test files with example patterns
]

function shouldExcludeFile(filename) {
  return EXCLUDED_PATTERNS.some((pattern) => filename.includes(pattern))
}

function getDiff(staged) {
  try {
    const cmd = staged ? 'git diff --cached' : 'git diff HEAD'
    const diff = execSync(cmd, { encoding: 'utf8', maxBuffer: 10 * 1024 * 1024 })
    return diff
  } catch (error) {
    console.error('Failed to get git diff:', error.message)
    process.exit(2)
  }
}

function parseDiff(diff) {
  const files = []
  let currentFile = null
  let currentLines = []
  let lineNumber = 0

  for (const line of diff.split('\n')) {
    // New file
    if (line.startsWith('diff --git')) {
      if (currentFile) {
        files.push({ ...currentFile, lines: currentLines })
      }
      const match = line.match(/diff --git a\/(.+) b\/(.+)/)
      currentFile = { filename: match ? match[2] : 'unknown' }
      currentLines = []
      lineNumber = 0
    }
    // Added line
    else if (line.startsWith('+') && !line.startsWith('+++')) {
      lineNumber++
      currentLines.push({ lineNumber, content: line.slice(1) })
    }
    // Track line numbers
    else if (line.startsWith('@@')) {
      const match = line.match(/\+(\d+)/)
      lineNumber = match ? Number.parseInt(match[1], 10) - 1 : 0
    }
  }

  if (currentFile) {
    files.push({ ...currentFile, lines: currentLines })
  }

  return files
}

function scanForSecrets(files) {
  const findings = []

  for (const file of files) {
    // Skip excluded files
    if (shouldExcludeFile(file.filename)) {
      continue
    }

    for (const { lineNumber, content } of file.lines) {
      for (const { name, pattern, description } of SECRET_PATTERNS) {
        pattern.lastIndex = 0 // Reset regex state
        const matches = content.match(pattern)

        if (matches) {
          findings.push({
            file: file.filename,
            line: lineNumber,
            type: name,
            description,
            preview: content.trim().slice(0, 100), // First 100 chars
          })
        }
      }
    }
  }

  return findings
}

function main() {
  const args = process.argv.slice(2)
  const staged = args.includes('--staged')

  console.log(`🔍 Scanning for secrets in ${staged ? 'staged' : 'uncommitted'} changes...`)

  const diff = getDiff(staged)

  if (!diff.trim()) {
    console.log('✅ No changes to scan')
    process.exit(0)
  }

  const files = parseDiff(diff)
  const findings = scanForSecrets(files)

  if (findings.length === 0) {
    console.log('✅ No secrets detected')
    process.exit(0)
  }

  console.error('\n❌ SECRETS DETECTED!\n')
  console.error('The following potential secrets were found in your changes:\n')

  for (const finding of findings) {
    console.error(`  ${finding.file}:${finding.line}`)
    console.error(`    Type: ${finding.type}`)
    console.error(`    Description: ${finding.description}`)
    console.error(`    Preview: ${finding.preview}`)
    console.error('')
  }

  console.error('⚠️  Please remove these secrets before committing!')
  console.error('   - Use environment variables or secure vaults for secrets')
  console.error('   - Never commit private keys, seed phrases, or API tokens')
  console.error('   - Review docs/wallet-security.md for guidance')
  console.error('')

  process.exit(1)
}

main()
