import math, re, hashlib
from typing import List

DIM = 128
_token_re = re.compile(r"[a-zA-Z0-9_]+")

def tokenize(text: str) -> List[str]:
    return _token_re.findall(text.lower())

def _bucket(token: str) -> int:
    h = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(h, "little") % DIM

def embed(text: str) -> List[float]:
    v = [0.0] * DIM
    toks = tokenize(text)
    if not toks:
        return v
    for t in toks:
        b = _bucket(t)
        hb = hashlib.blake2b((t+"#s").encode("utf-8"), digest_size=1).digest()[0]
        s = 1.0 if (hb % 2 == 0) else -1.0
        v[b] += s
    n = math.sqrt(sum(x*x for x in v)) or 1.0
    return [x / n for x in v]

def cosine(a: List[float], b: List[float]) -> float:
    return sum(x*y for x,y in zip(a,b))
