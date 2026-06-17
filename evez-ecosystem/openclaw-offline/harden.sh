#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  EVEZ OpenClaw — Security Hardening Script                 ║
# ║  Post-install: firewall, SSH, fail2ban, audit               ║
# ╚══════════════════════════════════════════════════════════════╝
set -euo pipefail

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo "╔════════════════════════════════════════════════╗"
echo "║  🛡️  EVEZ OpenClaw — Security Hardening        ║"
echo "╚══════════════════════════════════════════════════╝"

# ─── 1. Firewall ───
echo -e "${YELLOW}[1/6] Configuring firewall...${NC}"
if command -v ufw &>/dev/null; then
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow 22/tcp       # SSH
    sudo ufw allow 18789/tcp    # OpenClaw
    sudo ufw allow 443/tcp      # HTTPS
    sudo ufw --force enable
    echo -e "  ${GREEN}✓${NC} UFW enabled (22, 18789, 443)"
elif command -v iptables &>/dev/null; then
    sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
    sudo iptables -A INPUT -p tcp --dport 18789 -j ACCEPT
    sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
    sudo iptables -A INPUT -j DROP
    echo -e "  ${GREEN}✓${NC} iptables rules set"
else
    echo -e "  ${YELLOW}⚠${NC} No firewall available"
fi

# ─── 2. SSH Hardening ───
echo -e "${YELLOW}[2/6] Hardening SSH...${NC}"
SSHD_CONFIG="/etc/ssh/sshd_config"
if [ -f "$SSHD_CONFIG" ]; then
    sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' "$SSHD_CONFIG"
    sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' "$SSHD_CONFIG"
    sudo sed -i 's/^#*X11Forwarding.*/X11Forwarding no/' "$SSHD_CONFIG"
    sudo sed -i 's/^#*MaxAuthTries.*/MaxAuthTries 3/' "$SSHD_CONFIG"
    sudo sed -i 's/^#*LoginGraceTime.*/LoginGraceTime 30/' "$SSHD_CONFIG"
    # Add if not present
    grep -q "AllowTcpForwarding" "$SSHD_CONFIG" || echo "AllowTcpForwarding no" | sudo tee -a "$SSHD_CONFIG" > /dev/null
    grep -q "ClientAliveInterval" "$SSHD_CONFIG" || echo "ClientAliveInterval 300" | sudo tee -a "$SSHD_CONFIG" > /dev/null
    grep -q "ClientAliveCountMax" "$SSHD_CONFIG" || echo "ClientAliveCountMax 2" | sudo tee -a "$SSHD_CONFIG" > /dev/null
    sudo systemctl restart sshd 2>/dev/null || sudo systemctl restart ssh 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} SSH hardened (no password, no root, max 3 tries)"
fi

# ─── 3. fail2ban ───
echo -e "${YELLOW}[3/6] Configuring fail2ban...${NC}"
if command -v fail2ban-server &>/dev/null || [ -f /etc/fail2ban/jail.conf ]; then
    sudo tee /etc/fail2ban/jail.d/openclaw.conf > /dev/null << F2B
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
findtime = 600
bantime = 86400

[openclaw]
enabled = true
port = 18789
filter = openclaw-auth
logpath = /var/log/syslog
maxretry = 5
findtime = 300
bantime = 3600
F2B
    sudo systemctl enable fail2ban
    sudo systemctl restart fail2ban
    echo -e "  ${GREEN}✓${NC} fail2ban configured (SSH: 3 retries → 24h ban)"
else
    echo -e "  ${YELLOW}⚠${NC} fail2ban not installed — run: sudo apt install fail2ban"
fi

# ─── 4. File Permissions ───
echo -e "${YELLOW}[4/6] Setting file permissions...${NC}"
INSTALL_DIR="${1:-/opt/openclaw}"
if [ -d "$INSTALL_DIR" ]; then
    sudo chown -R openclaw:openclaw "$INSTALL_DIR" 2>/dev/null || true
    sudo chmod 700 "$INSTALL_DIR/.openclaw" 2>/dev/null || true
    sudo chmod 600 "$INSTALL_DIR/.openclaw/openclaw.json" 2>/dev/null || true
    sudo chmod 600 "$INSTALL_DIR/.openclaw/credentials"/* 2>/dev/null || true
    sudo chmod -R o-rwx "$INSTALL_DIR/.openclaw" 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} Permissions locked down"
fi

# ─── 5. Kernel Hardening ───
echo -e "${YELLOW}[5/6] Kernel parameters...${NC}"
sudo sysctl -w net.ipv4.tcp_syncookies=1 2>/dev/null || true
sudo sysctl -w net.ipv4.conf.all.accept_redirects=0 2>/dev/null || true
sudo sysctl -w net.ipv4.conf.default.accept_redirects=0 2>/dev/null || true
sudo sysctl -w net.ipv4.icmp_echo_ignore_broadcasts=1 2>/dev/null || true
echo -e "  ${GREEN}✓${NC} Kernel hardened (SYN cookies, no redirects)"

# ─── 6. Audit Log ───
echo -e "${YELLOW}[6/6] Setting up audit logging...${NC}"
if command -v auditctl &>/dev/null; then
    sudo auditctl -w "$INSTALL_DIR/.openclaw/openclaw.json" -p wa -k openclaw_config
    sudo auditctl -w "$INSTALL_DIR/.openclaw/credentials/" -p wa -k openclaw_creds
    echo -e "  ${GREEN}✓${NC} Audit rules set"
else
    echo -e "  ${YELLOW}⚠${NC} auditd not installed — run: sudo apt install auditd"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🛡️  Security hardening complete      ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
