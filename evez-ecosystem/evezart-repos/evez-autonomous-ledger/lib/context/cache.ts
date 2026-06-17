type Entry = {
  value: unknown;
  expiresAt: number;
};

const memoryCache = new Map<string, Entry>();

function now() {
  return Date.now();
}

function read(key: string) {
  const entry = memoryCache.get(key);
  if (!entry) return null;
  if (entry.expiresAt <= now()) {
    memoryCache.delete(key);
    return null;
  }
  return entry.value;
}

function write(key: string, value: unknown, ttlSeconds: number) {
  memoryCache.set(key, {
    value,
    expiresAt: now() + ttlSeconds * 1000,
  });
}

export async function getHotContext(key: string) {
  return read(`ctx:${key}`);
}

export async function setHotContext(key: string, value: unknown, ttl = 900) {
  write(`ctx:${key}`, value, ttl);
}

export async function getHotRoute(key: string) {
  return read(`route:${key}`);
}

export async function setHotRoute(key: string, value: unknown, ttl = 300) {
  write(`route:${key}`, value, ttl);
}
