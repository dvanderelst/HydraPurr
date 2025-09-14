#!/usr/bin/env bash
set -euo pipefail

# CircuitPython REPL launcher for Linux (works great in PyCharm's Terminal)
# Usage: ./cp_repl.sh [--raw]    # pass --raw to disable miniterm's key menu if you prefer

BAUD=115200
RAW_ARG=""
if [[ "${1:-}" == "--raw" ]]; then RAW_ARG="--raw"; fi

# 1) Pick a Python to run pyserial/miniterm
pick_python() {
  if command -v python >/dev/null 2>&1; then echo python
  elif command -v python3 >/dev/null 2>&1; then echo python3
  else
    echo "No 'python' or 'python3' found in PATH." >&2
    exit 1
  fi
}
PY="$(pick_python)"

# 2) Ensure pyserial is available (for miniterm & port listing)
if "$PY" - <<'PYCODE' >/dev/null 2>&1
import serial, serial.tools.miniterm, serial.tools.list_ports  # noqa: F401
PYCODE
then
  : # pyserial present
else
  echo "[setup] Installing pyserial into the current Python environment..."
  "$PY" -m pip install pyserial >/dev/null
fi

# 3) Gather candidate ports
declare -a CANDIDATES=()

# Prefer stable by-id symlinks
if compgen -G "/dev/serial/by-id/*" > /dev/null; then
  while IFS= read -r p; do CANDIDATES+=("$p"); done < <(ls -1 /dev/serial/by-id/* 2>/dev/null)
fi

# Fallback to ttyACM/ttyUSB if nothing in by-id
if [[ ${#CANDIDATES[@]} -eq 0 ]]; then
  while IFS= read -r p; do CANDIDATES+=("$p"); done < <(ls -1 /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || true)
fi

# As a last resort, ask pyserial to enumerate everything
if [[ ${#CANDIDATES[@]} -eq 0 ]]; then
  mapfile -t CANDIDATES < <("$PY" - <<'PYCODE'
from serial.tools import list_ports
for p in list_ports.comports():
    if p.device.startswith("/dev/"):
        print(p.device)
PYCODE
)
fi

# 4) Choose a port (auto if only one; prompt if multiple)
choose_port() {
  local -n arr=$1
  if [[ ${#arr[@]} -eq 0 ]]; then
    echo "No serial ports found."
    echo "Tips:"
    echo "  • Make sure the board isn't in bootloader (RPI-RP2) mode."
    echo "  • Use a data USB cable."
    echo "  • Close other serial monitors (Thonny/Mu)."
    echo "  • Check permissions: add yourself to 'dialout' and re-login:"
    echo "      sudo usermod -a -G dialout \"$USER\""
    exit 1
  elif [[ ${#arr[@]} -eq 1 ]]; then
    echo "${arr[0]}"
  else
    echo "Multiple serial ports found:"
    local i=1
    for p in "${arr[@]}"; do
      echo "  [$i] $p"
      ((i++))
    done
    while true; do
      read -rp "Select a port number: " idx
      if [[ "$idx" =~ ^[0-9]+$ ]] && (( idx>=1 && idx<=${#arr[@]} )); then
        echo "${arr[$((idx-1))]}"
        return 0
      fi
      echo "Invalid selection. Try again."
    done
  fi
}

PORT="$(choose_port CANDIDATES)"

# 5) Quick permission sanity check
if [[ ! -r "$PORT" ]]; then
  echo "Cannot read $PORT (permissions?)."
  echo "Try: sudo usermod -a -G dialout \"$USER\"  (then log out/in)"
  exit 1
fi

echo
echo "================= CircuitPython REPL ================="
echo "Port: $PORT"
echo "Baud: $BAUD"
if [[ -z "$RAW_ARG" ]]; then
  echo "Keys:  Ctrl+C interrupt | Ctrl+D soft reboot | Ctrl+] then q to quit"
else
  echo "Keys:  Ctrl+C interrupt | Ctrl+D soft reboot | (no miniterm menu in --raw mode)"
fi
echo "======================================================"
echo

exec "$PY" -m serial.tools.miniterm "$PORT" "$BAUD" $RAW_ARG
