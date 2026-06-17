# Level 1 Solution: THE UNBOXING

## Flag: `FLAG{firecracker_on_kvm}`

## 7-Artifact Evidence Chain

### Artifact 1: KVM Hypervisor Detection
```
$ dmesg | grep -i hypervisor
[    0.000000] Hypervisor detected: KVM
[    0.000000] Booting paravirtualized kernel on KVM
```
**Confidence: 0.99** — KVM signature in early boot messages.

### Artifact 2: No PCI Bus
```
$ cat /proc/cmdline
... pci=off ...
```
**Confidence: 0.95** — `pci=off` is unique to Firecracker. Standard VMs need PCI for virtio devices; Firecracker uses MMIO directly.

### Artifact 3: No PS/2 Devices
```
$ cat /proc/cmdline
... i8042.noaux i8042.nokbd ...
```
**Confidence: 0.90** — Disabling keyboard/mouse controllers. MicroVMs have no physical input devices.

### Artifact 4: No DMI/SMBIOS
```
$ ls /sys/class/dmi/
(empty)
```
**Confidence: 0.95** — No BIOS emulation. Direct kernel boot without firmware tables.

### Artifact 5: TAP Networking
```
$ cat /proc/cmdline
... ip=169.254.0.21::169.254.0.22:255.255.255.0::eth0:off ...
$ ip addr show eth0
2: eth0: <BROADCAST,MULTICAST,UP> ... link/ether ...
```
**Confidence: 0.95** — Link-local IP on TAP device. Firecracker's networking model.

### Artifact 6: Panic Behavior
```
$ cat /proc/cmdline
... panic=1 ...
```
**Confidence: 0.80** — Crash-restart pattern typical of ephemeral microVMs.

### Artifact 7: Builder Hostname
```
$ uname -r
6.1.158 (root@runnervmfxdz0)
```
**Confidence: 0.90** — Builder hostname leaks infrastructure identity (e2b sandbox runner).

## Combined Confidence: 0.95

## Why Standard Detection Failed
Standard container detection checks:
- `/.dockerenv` — FALSE (it's not a Docker container)
- `/proc/1/cgroup` docker/lxc markers — FALSE (it's not a container at all)
- Environment variables — FALSE (no container runtime sets them)

All correct! It's NOT a container. It's a lightweight VM that boots a real Linux kernel inside a real (minimal) virtual machine. From inside, the kernel is real, the filesystem is real, the processes are real. The containment is at the hypervisor layer, which is invisible to userspace container detection tools.

## Contradiction Engine Analysis
The engine would detect:
1. CLAIM: "No container markers" (trust: 0.95)
2. CLAIM: "System is bare metal" (trust: 0.70) — implied by #1
3. OBSERVATION: "KVM hypervisor detected" (trust: 0.99) — contradicts #2
4. **UNSAT CORE**: {bare_metal, kvm_detected} — mutually exclusive
5. **AUTO-TEST**: "Check /proc/cmdline for virtualization-specific parameters"
6. **RESOLUTION**: bare_metal → REFUTED, firecracker_microvm → CONFIRMED
