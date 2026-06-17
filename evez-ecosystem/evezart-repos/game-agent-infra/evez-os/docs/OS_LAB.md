# OS LAB (Interrogate operating systems — legally, sandboxed)

This project can “interrogate” operating systems by **instrumenting behavior** in an authorized environment:
- VMs you own
- Open-source OS builds
- Intentionally vulnerable images (CTFs) for training *defense*
- Emulators (QEMU) and containers

**Not allowed:** “hidden access,” backdoor hunting on third-party systems, exploitation guidance.

---

## What we measure (safe, defensible)
- Boot characteristics (kernel version, init timing)
- Syscall surface & error behavior (read-only observation)
- Scheduling and timer drift (bench + log)
- Memory pressure response (stress tests you control)
- Networking stack behavior (DNS/TLS/HTTP from inside VM)
- Crash signatures and reproducibility

---

## “Easter egg levels” — the safe version
We create Easter eggs in *our* game:
- hidden missions that trigger when invariants are violated
- red-team/blue-team puzzles inside the scenario packs
- seeded faults inside a VM image you distribute

We do **not** go searching for hidden access in real systems.

---

## Minimal workflow
1) Boot a VM image you are authorized to test.
2) Run probes from inside and outside.
3) Append results to the spine.
4) Let FSC extract Σf and Ω and auto-generate the next mission.

