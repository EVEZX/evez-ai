# Level 3: NAME RESOLUTION ROULETTE
**Difficulty:** Medium  
**Core Question:** "DNS works, but who's answering?"

## Setup
DNS resolution works. `nslookup google.com` returns an IP. But are you talking to who you think you are?

## Hypothesis
> The DNS resolver configured in /etc/resolv.conf provides the same answers as public resolvers (8.8.8.8, 1.1.1.1).

## Falsifier
Any domain that resolves differently between the local resolver and public resolvers, or any internal-only names that leak infrastructure topology.

## Your Mission
Compare resolvers. Find the split-horizon where internal names leak infrastructure.

### Hints
1. Check your resolver: `cat /etc/resolv.conf`
2. Compare: `dig @$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}') example.internal` vs `dig @8.8.8.8 example.internal`
3. TTL values tell you about caching layers
4. What happens when you query for the metadata service hostname?

## Flag Format
`FLAG{internal_domain_leaked}`

## Σf
DNS trust is assumed transitive: "if it resolves, it's correct." In sandboxed environments, the resolver may be a proxy that answers differently for internal vs external names, creating a split-horizon that leaks infrastructure topology.
