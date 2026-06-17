# Security Policy

## Supported Versions
| Version | Supported |
|---------|-----------|
| 2.0.x   | ✅ |
| < 2.0   | ❌ |

## Reporting a Vulnerability
Email security concerns to the repository owner.

**Do NOT open a public issue for security vulnerabilities.**

## Security Measures
- All API endpoints use CORS restrictions
- JWT verification available on all Edge Functions
- Row Level Security (RLS) on all database tables
- Audit logging with automatic triggers
- HMAC signature verification for webhooks
- No PII stored in logs

## Data Protection
- SSN data is hashed (never stored in plain text)
- Credit data access requires authentication
- API keys with scoped permissions
- Rate limiting enforced per API key

## Compliance
- ECOA: No protected class data collected or used
- FCRA: All credit data from permissible CRA sources
- Reg B: Adverse action notices generated automatically
