#!/usr/bin/env python3
import time, math

def is_prime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    r = int(math.sqrt(n))
    for i in range(3, r+1, 2):
        if n % i == 0:
            return False
    return True

start = time.time()
primes = [n for n in range(100000) if is_prime(n)]
elapsed = time.time() - start
print(f"Found {len(primes)} primes in {elapsed:.2f} seconds")
