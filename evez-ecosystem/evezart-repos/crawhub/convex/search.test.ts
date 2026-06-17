/* @vitest-environment node */

import { describe, expect, it } from 'vitest'
import { __test } from './search'

describe('search helpers', () => {
  it('advances candidate limit until max', () => {
    expect(__test.getNextCandidateLimit(50, 1000)).toBe(100)
    expect(__test.getNextCandidateLimit(800, 1000)).toBe(1000)
    expect(__test.getNextCandidateLimit(1000, 1000)).toBeNull()
  })
})
