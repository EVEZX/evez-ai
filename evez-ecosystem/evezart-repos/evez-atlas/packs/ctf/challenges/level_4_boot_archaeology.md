# Level 4: BOOT ARCHAEOLOGY
**Difficulty:** Hard  
**Core Question:** "PID 1 is /sbin/init. That's all you know."

## Setup
The system booted somehow. You're inside it. Reconstruct the entire chain.

## Hypothesis
> The boot chain follows standard BIOS/UEFI → bootloader → kernel → init sequence.

## Falsifier
Any evidence that steps were skipped or performed differently than standard boot.

## Your Mission
Reconstruct: bootloader → kernel → init → userspace. What's missing? What does that tell you?

### Hints
1. Check for BIOS/UEFI artifacts: `ls /sys/firmware/efi/` and `dmesg | grep -i bios`
2. Look at the kernel version: `uname -r` — does it match standard distro kernels?
3. What does `cat /proc/cmdline` tell you about how the kernel was loaded?
4. PCI devices: `lspci` or `ls /sys/bus/pci/devices/`

## Flag Format
`FLAG{boot_method_name}`

## Σf
Boot chain analysis assumes hardware initialization artifacts (BIOS tables, PCI enumeration, ACPI). Direct kernel boot skips all of these, leaving an archaeological gap that reveals the VMM's loading method.
