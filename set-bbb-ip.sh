#!/bin/bash

# Static IP configuration script for ConnMan
# Targets the service named "AR Wired" only

IP_ADDR="192.168.137.125"
NETMASK="255.255.255.0"
GATEWAY="192.168.137.1"

# Ensure the script is run as root
if [[ "$EUID" -ne 0 ]]; then
  echo "❌ Please run this script as root (use sudo)"
  exit 1
fi

# Find ConnMan service with label "AR Wired"
SERVICE=$(connmanctl services | awk '/AR Wired/ {print $NF}')

if [[ -z "$SERVICE" ]]; then
  echo "❌ Could not find ConnMan service named 'AR Wired'"
  exit 1
fi

echo "🔧 Found service: $SERVICE"
echo "📡 Setting static IP: $IP_ADDR, Netmask: $NETMASK, Gateway: $GATEWAY"

# Apply static IP config
connmanctl config "$SERVICE" --ipv4 manual "$IP_ADDR" "$NETMASK" "$GATEWAY"

echo "✅ Static IP $IP_ADDR applied to service: $SERVICE"
