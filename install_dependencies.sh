#!/bin/bash
set -euo pipefail

# Colors for readability
info() { echo -e "\033[1;34m[INFO]\033[0m $*"; }
success() { echo -e "\033[1;32m[SUCCESS]\033[0m $*"; }
error() { echo -e "\033[1;31m[ERROR]\033[0m $*"; }

function install_packages() {
  # Ensure running on Ubuntu/Debian
  if ! command -v apt-get >/dev/null 2>&1; then
      error "This script requires apt-get (Ubuntu/Debian system)."
      exit 1
  fi

  info "Updating package index..."
  sudo apt-get update -qq

  info "Installing required packages..."
  sudo apt-get install -y \
      gdb \
      git \
      libcurl4-gnutls-dev \
      libphysfs-dev


  if [ ! -d /usr/local/ssl ]; then
  	sudo mkdir -p /usr/local/ssl
  fi

  # Required for python
  sudo ln -sf '/etc/ssl/certs' /usr/local/ssl/certs

  success "All packages installed successfully!"
}

# Add .gdbinit for debug
function gdb_init() {
  GDBINIT="$HOME/.gdbinit"
  LINE='set auto-load safe-path /'

  # Check if .gdbinit exists and contains the line
  if ! grep -Fxq "$LINE" "$GDBINIT" 2>/dev/null; then
    info "$LINE" >> "$GDBINIT"
    success "Added '$LINE' to $GDBINIT"
  else
    info "$GDBINIT is ready"
  fi
}

install_packages
gdb_init