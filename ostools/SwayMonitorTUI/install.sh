#!/bin/sh
set -eu

REPO_RAW="https://raw.githubusercontent.com/Mandrusian/utilitools/main/ostools/SwayMonitorTUI"
BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
DEST="$BIN_DIR/sway-monitor-tui"
TMP_FILE=$(mktemp)
trap 'rm -f "$TMP_FILE"' EXIT HUP INT TERM

if ! command -v curl >/dev/null 2>&1; then
  echo "Error: curl is required to install sway-monitor-tui." >&2
  exit 1
fi

mkdir -p "$BIN_DIR"

echo "Downloading sway-monitor-tui..."
curl -fL --retry 3 "$REPO_RAW/sway-monitor-tui.py" -o "$TMP_FILE"
install -m 0755 "$TMP_FILE" "$DEST"

echo "Installed: $DEST"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "Note: $BIN_DIR is not currently on PATH. Add it to your shell profile." ;;
esac
echo "Run: sway-monitor-tui"
