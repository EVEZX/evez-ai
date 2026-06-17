#!/bin/bash
# EVEZ-OS Bootstrap — Full System Rebuild
# Generated: 2026-05-24 by Steven (Counter-Intelligence v1.0)
# Purpose: Reconstruct EVEZ from scratch on any Ubuntu 22.04+ VPS
set -e

echo "⚡ EVEZ-OS BOOTSTRAP — FULL REBUILD"
echo "====================================="

# 1. System hardening
echo "[1/12] Hardening kernel..."
cat > /etc/sysctl.d/99-evez-hardening.conf << 'SYSCTL'
kernel.kptr_restrict=2
kernel.dmesg_restrict=1
kernel.unprivileged_bpf_disabled=1
net.core.bpf_jit_harden=2
kernel.yama.ptrace_scope=2
fs.suid_dumpable=0
kernel.randomize_va_space=2
net.ipv4.tcp_syncookies=1
net.ipv4.conf.all.rp_filter=1
net.ipv4.conf.default.rp_filter=1
net.ipv4.icmp_echo_ignore_broadcasts=1
net.ipv4.conf.all.accept_redirects=0
net.ipv4.conf.default.accept_redirects=0
net.ipv6.conf.all.accept_redirects=0
net.ipv4.conf.all.send_redirects=0
net.ipv4.conf.default.send_redirects=0
vm.swappiness=10
SYSCTL
sysctl --system

# 2. SSH hardening
echo "[2/12] Hardening SSH..."
sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config
sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
echo "MaxAuthTries 3" >> /etc/ssh/sshd_config
echo "AllowUsers openclaw" >> /ssh/sshd_config
systemctl restart sshd

# 3. UFW
echo "[3/12] Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 80/tcp
ufw allow 443
ufw allow 2222/tcp
ufw deny from 80.94.92.0/24 comment "DMZHOST"
ufw deny from 45.148.10.0/24 comment "DMZHOST cluster 2"
ufw deny from 193.32.162.0/24 comment "Solana hunters"
ufw deny from 45.156.87.0/24 comment "VMHeaven"
ufw deny from 45.140.167.0/24 comment "WorkTitans/Stark"
ufw deny from 185.81.124.0/24 comment "Composio CDNEXT"
ufw deny from 185.81.126.0/24 comment "Composio CDNEXT"
ufw deny from 185.81.127.0/24 comment "Composio CDNEXT"
ufw deny from 31.222.254.0/24 comment "PacketHub"
ufw deny from 45.13.235.0/24 comment "PacketHub"
ufw deny from 89.23.112.0/24 comment "Moscow brute force"
ufw deny from 89.23.0.0/16 comment "Russian brute force"
ufw --force enable

# 4. Fail2ban
echo "[4/12] Configuring fail2ban..."
apt-get install -y fail2ban
cat > /etc/fail2ban/jail.d/evez-hardened.conf << 'F2B'
[sshd]
enabled = true
port = 2222
maxretry = 3
findtime = 300
bantime = 86400
[recidive]
enabled = true
bantime = 2592000
findtime = 86400
maxretry = 3
F2B
systemctl enable fail2ban
systemctl restart fail2ban

# 5. Swap
echo "[5/12] Creating swap..."
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# 6. EVEZ services
echo "[6/12] Deploying EVEZ services..."
# (Services are in the backup archive, extracted below)

# 7. Counter-intel daemon
echo "[7/12] Deploying counter-intel..."
cp evez-counterintel.py /home/openclaw/
cp evez-threat-intel.py /home/openclaw/
systemctl --user daemon-reload
systemctl --user enable evez-counterintel
systemctl --user start evez-counterintel

# 8. Audit
echo "[8/12] Installing auditd..."
apt-get install -y auditd
auditctl -w /etc/passwd -p wa -k identity_changes
auditctl -w /etc/shadow -p wa -k password_changes
auditctl -w /etc/ssh/sshd_config -p wa -k ssh_config
auditctl -w /etc/ufw -p wa -k firewall_changes

# 9. Docker + SearXNG
echo "[9/12] SearXNG..."
docker run -d --name searxng -p 127.0.0.1:8888:8080 searxng/searxng 2>/dev/null || true

# 10. Caddy
echo "[10/12] Caddy..."
apt-get install -y caddy 2>/dev/null || true

# 11. OpenClaw gateway
echo "[11/12] OpenClaw gateway..."
# (Installed by OpenClaw itself)

# 12. Verify
echo "[12/12] Verification..."
echo "SSH: $(ss -tlnp | grep 2222 | head -1)"
echo "UFW: $(ufw status | head -1)"
echo "Fail2ban: $(fail2ban-client status 2>/dev/null | head -1)"
echo "Counter-intel: $(systemctl --user is-active evez-counterintel)"
echo ""
echo "⚡ EVEZ-OS REBUILD COMPLETE ⚡"
