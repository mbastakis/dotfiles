#!/bin/bash
set -euo pipefail

case "$NAME" in
  cpu)
    sketchybar --set "$NAME" label="CPU ${CPU_USAGE:---}"
    ;;
  ram)
    sketchybar --set "$NAME" label="RAM ${RAM_USAGE:---}"
    ;;
  network)
    network_interface="$(route -n get default 2>/dev/null | awk '/interface:/{print $2; exit}')"
    interface_key="$(printf '%s' "$network_interface" | tr '.-' '__')"
    rx_variable="NETWORK_RX_${interface_key}"
    tx_variable="NETWORK_TX_${interface_key}"
    rx="${!rx_variable:---}"
    tx="${!tx_variable:---}"
    sketchybar --set "$NAME" label="↓ $rx  ↑ $tx"
    ;;
esac
