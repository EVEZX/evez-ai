#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -eq 0 ]]; then
  SUDO=""
else
  if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
  else
    echo "This script must be run as root or with sudo." >&2
    exit 1
  fi
fi

install_tailscale() {
  if [[ ! -f /etc/os-release ]]; then
    echo "Unable to detect OS: /etc/os-release not found." >&2
    return 1
  fi

  . /etc/os-release

  local os_id
  local codename
  os_id=${ID}
  codename=${VERSION_CODENAME:-}

  if [[ -z ${codename} ]]; then
    echo "Unable to detect OS codename from /etc/os-release." >&2
    return 1
  fi

  case "${os_id}" in
    ubuntu|debian)
      ;;
    *)
      echo "Unsupported OS for Tailscale apt repo setup: ${os_id}." >&2
      return 1
      ;;
  esac

  ${SUDO} mkdir -p /usr/share/keyrings /etc/apt/sources.list.d

  ${SUDO} curl -fsSL "https://pkgs.tailscale.com/stable/${os_id}/${codename}.noarmor.gpg" \
    -o /usr/share/keyrings/tailscale-archive-keyring.gpg
  ${SUDO} curl -fsSL "https://pkgs.tailscale.com/stable/${os_id}/${codename}.tailscale-keyring.list" \
    -o /etc/apt/sources.list.d/tailscale.list

  ${SUDO} apt-get update
  ${SUDO} apt-get install -y tailscale
}

if [[ ${1:-} == "--install-tailscale" ]]; then
  install_tailscale
fi
