# Level 1: THE UNBOXING
**Difficulty:** Easy  
**Core Question:** "Am I in a container?"

## Setup
You have shell access to a Linux system. Standard container detection tools report you're on bare metal.

## Hypothesis
> Standard container detection heuristics (/.dockerenv, cgroup markers, environment variables) are sufficient to determine containment status.

## Falsifier
Any evidence of virtualization, sandboxing, or resource restrictions not visible to standard container detection.

## Your Mission
Determine the actual containment technology. Standard tools say "bare metal." Are they right?

### Hints
1. Check what the kernel knows that userspace tools don't: `dmesg | head -50`
2. Look at the kernel command line: `cat /proc/cmdline`
3. What's missing is as important as what's present: check `/sys/class/dmi/`
4. Compare network interfaces: `ip addr` — what kind of device is your network adapter?

## Flag Format
`FLAG{technology_name_on_hypervisor}`

## Σf (Failure Surface)
Standard container detection assumes containment = containers. It has no model for lightweight VMs that boot real kernels and deliberately mimic bare metal from inside. The failure surface is the assumption gap between "no container markers" and "not sandboxed."
