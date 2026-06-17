import { v } from 'convex/values'
import { internalMutation } from './_generated/server'

export const checkRateLimitInternal = internalMutation({
  args: {
    key: v.string(),
    limit: v.number(),
    windowMs: v.number(),
  },
  handler: async (ctx, args) => {
    const now = Date.now()
    const windowStart = Math.floor(now / args.windowMs) * args.windowMs
    const resetAt = windowStart + args.windowMs
    if (args.limit <= 0) {
      return { allowed: false, remaining: 0, limit: args.limit, resetAt }
    }

    const existing = await ctx.db
      .query('rateLimits')
      .withIndex('by_key_window', (q) => q.eq('key', args.key).eq('windowStart', windowStart))
      .unique()

    if (!existing) {
      await ctx.db.insert('rateLimits', {
        key: args.key,
        windowStart,
        count: 1,
        limit: args.limit,
        updatedAt: now,
      })
      return { allowed: true, remaining: Math.max(0, args.limit - 1), limit: args.limit, resetAt }
    }

    if (existing.count >= args.limit) {
      return { allowed: false, remaining: 0, limit: args.limit, resetAt }
    }

    await ctx.db.patch(existing._id, {
      count: existing.count + 1,
      limit: args.limit,
      updatedAt: now,
    })
    return {
      allowed: true,
      remaining: Math.max(0, args.limit - existing.count - 1),
      limit: args.limit,
      resetAt,
    }
  },
})
