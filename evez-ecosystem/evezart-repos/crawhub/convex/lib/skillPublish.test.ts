import { describe, expect, it } from 'vitest'
import { __test } from './skillPublish'

describe('skillPublish', () => {
  it('merges github source into metadata', () => {
    const merged = __test.mergeSourceIntoMetadata(
      { clawdis: { emoji: 'x' } },
      {
        kind: 'github',
        url: 'https://github.com/a/b',
        repo: 'a/b',
        ref: 'main',
        commit: '0123456789012345678901234567890123456789',
        path: 'skills/demo',
        importedAt: 123,
      },
    )
    expect((merged as Record<string, unknown>).clawdis).toEqual({ emoji: 'x' })
    const source = (merged as Record<string, unknown>).source
    expect(source).toEqual(
      expect.objectContaining({
        kind: 'github',
        repo: 'a/b',
        path: 'skills/demo',
      }),
    )
  })
})
