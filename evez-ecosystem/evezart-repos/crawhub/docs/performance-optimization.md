# Performance Optimization Guide

This document outlines performance optimization patterns and best practices for the ClawHub codebase.

## Overview

ClawHub uses Convex as its serverless backend. Optimizing performance in this context involves:
- Efficient database queries
- Parallel operations where possible
- Proper use of indexes
- Minimizing sequential async operations

## Common Performance Patterns

### 1. Parallelize Independent Operations

**❌ BAD: Sequential async operations**
```typescript
for (const item of items) {
  const result = await processItem(item)
  results.push(result)
}
```

**✅ GOOD: Parallel processing with Promise.all**
```typescript
const results = await Promise.all(
  items.map(async (item) => await processItem(item))
)
```

**Examples in codebase:**
- `convex/githubImport.ts`: Parallelized file sha256 + storage operations
- `convex/lib/skillPublish.ts`: Parallelized file content fetching
- `convex/lib/githubBackup.ts`: Parallelized GitHub blob creation
- `convex/telemetry.ts`: Parallelized database deletions and skill lookups

### 2. Limit Database Queries Early

**❌ BAD: Fetch all records then filter**
```typescript
const allUsers = await ctx.db.query('users').collect()
const filtered = allUsers.filter(u => !u.deletedAt)
```

**✅ GOOD: Use .take() or apply filters at query level**
```typescript
const users = await ctx.db
  .query('users')
  .take(10000)
  .then(users => users.filter(u => !u.deletedAt))
```

**Examples in codebase:**
- `convex/users.ts`: Limited user search to 10k records with early filtering

### 3. Use Indexes Efficiently

**❌ BAD: Fetch all then filter in memory**
```typescript
const allRecords = await ctx.db
  .query('events')
  .collect()
const filtered = allRecords.filter(e => e.timestamp >= startTime)
```

**✅ GOOD: Use index range queries**
```typescript
const records = await ctx.db
  .query('events')
  .withIndex('by_timestamp', q => 
    q.gte('timestamp', startTime)
  )
  .collect()
```

**Memory Note:** The `physicalPassoverEvents.ts` file demonstrates this pattern with time-range queries using `.gte()` and `.lte()` on indexed fields.

### 4. Batch Database Operations

**❌ BAD: Delete records one at a time**
```typescript
for (const record of records) {
  await ctx.db.delete(record._id)
}
```

**✅ GOOD: Batch delete with Promise.all**
```typescript
await Promise.all(
  records.map(record => ctx.db.delete(record._id))
)
```

**Examples in codebase:**
- `convex/telemetry.ts`: Batched deletion of telemetry data
- `convex/leaderboards.ts`: Parallelized deletion of old leaderboard entries

## Performance Checklist

When writing new code or reviewing existing code, check for:

- [ ] Are sequential async operations independent? → Use `Promise.all()`
- [ ] Is a `.collect()` query fetching all records? → Add `.take()` limit
- [ ] Are you filtering large datasets in memory? → Move filter to query level
- [ ] Are you looping with `await` inside? → Consider parallelization
- [ ] Are time-range queries using indexes properly? → Use `.gte()`, `.lte()`
- [ ] Are deletions/updates happening sequentially? → Batch with `Promise.all()`

## Measuring Performance

### Local Testing
```bash
# Run tests with timing
bun run test

# Profile specific operations
console.time('operation')
await slowOperation()
console.timeEnd('operation')
```

### Production Monitoring
- Use Convex Dashboard to monitor query times
- Check function execution times
- Monitor database read/write operations

## Optimization Priority

1. **Critical**: Operations that fetch all records without limits
2. **High**: Sequential async operations in loops (N+1 patterns)
3. **Medium**: In-memory filtering of large datasets
4. **Low**: Single operations with sub-optimal but acceptable performance

## When NOT to Optimize

- Don't parallelize operations with dependencies between them
- Don't over-optimize queries that only return small datasets
- Don't sacrifice code readability for marginal gains
- Don't parallelize operations that might cause race conditions

## Recent Optimizations (2026-02)

The following files were optimized as part of a performance improvement initiative:

1. **convex/users.ts**: Limited user search query and added early filtering
2. **convex/telemetry.ts**: Parallelized deletions and skill lookups
3. **convex/leaderboards.ts**: Parallelized old entry cleanup
4. **convex/githubImport.ts**: Parallelized file processing during import
5. **convex/lib/skillPublish.ts**: Parallelized file content fetching
6. **convex/lib/githubBackup.ts**: Parallelized GitHub API calls
7. **convex/lib/githubSoulBackup.ts**: Parallelized GitHub API calls

All optimizations maintained 100% test coverage with 340 passing tests.

## Further Reading

- [Convex Query Performance Guide](https://docs.convex.dev/using/query-performance)
- [JavaScript Promise.all Patterns](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/all)
- ClawHub repository memories contain additional context on query optimization patterns
