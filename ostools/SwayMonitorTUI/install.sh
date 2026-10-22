#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
DEST="$BIN_DIR/sway-monitor-tui"

mkdir -p "$BIN_DIR"
install -m 0755 "$SCRIPT_DIR/sway-monitor-tui.py" "$DEST"

printf 'Installed: %s\n' "$DEST"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) printf 'Note: %s is not currently on PATH. Add it to your shell profile.\n' "$BIN_DIR" ;;
esac
printf 'Run: sway-monitor-tui\n'
