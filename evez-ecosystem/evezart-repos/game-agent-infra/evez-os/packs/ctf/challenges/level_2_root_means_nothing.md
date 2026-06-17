# Level 2: ROOT MEANS NOTHING
**Difficulty:** Medium  
**Core Question:** "uid=0, full capabilities, but you can't touch the disk."

## Setup
You are root. You have every Linux capability. But `/dev/sda` returns "Permission denied."

## Hypothesis
> Root with CapEff=000001ffffffffff has unrestricted access to all system resources.

## Falsifier
Any resource that root cannot access despite having all capabilities.

## Your Mission
Map the real permission boundary that exists below the Linux permission layer. Where does the sandbox actually enforce limits?

### Hints
1. List all capabilities: `cat /proc/self/status | grep Cap`
2. Try to write to /dev/sda: `dd if=/dev/zero of=/dev/sda bs=1 count=1 2>&1`
3. Check what devices are actually available: `ls -la /dev/`
4. Who owns the device restrictions? It's not Linux capabilities...

## Flag Format
`FLAG{enforcement_layer_name}`

## Σf
Linux capability model assumes it's the final arbiter of permissions. In a microVM, the VMM (Virtual Machine Monitor) enforces restrictions at a layer below the kernel, making Linux capabilities a convenient illusion.
