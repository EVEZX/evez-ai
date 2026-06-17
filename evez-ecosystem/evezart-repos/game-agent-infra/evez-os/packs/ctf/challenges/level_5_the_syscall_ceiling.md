# Level 5: THE SYSCALL CEILING
**Difficulty:** Hard  
**Core Question:** "Seccomp=0 says your syscalls are unrestricted. Test that."

## Setup
`/proc/self/status` reports `Seccomp: 0` (disabled). The kernel says you have no syscall filtering.

## Hypothesis
> Seccomp mode 0 means all syscalls are available and unrestricted.

## Falsifier
Any syscall that fails despite Seccomp reporting no filtering, or any evidence of filtering at a layer below Linux.

## Your Mission
Find where the real syscall boundary lives — not where Linux says it is.

### Hints
1. Verify seccomp: `grep Seccomp /proc/self/status`
2. Try unusual syscalls: `python3 -c "import ctypes; ctypes.CDLL(None).syscall(435)"` (different syscall numbers)
3. The kernel inside the VM reports no filtering. But what about the kernel OUTSIDE?
4. Look for virtio device restrictions that indicate VMM-level syscall interception

## Flag Format
`FLAG{actual_filtering_layer}`

## Σf
Seccomp reports the guest kernel's filtering state. In a microVM, the host kernel and VMM provide an additional syscall filtering layer invisible to the guest. The guest's Seccomp=0 is true within the guest's reality — but the guest's reality is not the complete picture.
