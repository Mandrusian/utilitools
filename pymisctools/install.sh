#!/usr/bin/env bash
# utilitools installer — macOS / Linux / Termux
set -e

REPO_URL="${UTILITOOLS_REPO:-https://github.com/Mandrusian/utilitools.git}"
INSTALL_DIR="${UTILITOOLS_DIR:-$HOME/utilitools}"

say() { printf "  \033[94m•\033[0m %s\n" "$1"; }
ok()  { printf "  \033[92m✓\033[0m %s\n" "$1"; }
err() { printf "  \033[91m✗\033[0m %s\n" "$1" >&2; }

echo
echo "  utilitools installer"
echo

# --- 1. Python ---
if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1 && python -c 'import sys; sys.exit(0 if sys.version_info[0]>=3 else 1)' 2>/dev/null; then
    PY=python
else
    say "Python 3 not found — installing"
    if [ "$(uname)" = "Darwin" ]; then
        if ! command -v brew >/dev/null 2>&1; then
            err "Homebrew not found. Install from https://brew.sh and rerun."
            exit 1
        fi
        brew install python3
    elif command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y python3 python3-pip
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3 python3-pip
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm python python-pip
    elif [ -n "$PREFIX" ] && [ -d "/data/data/com.termux" ]; then
        pkg install -y python
    else
        err "No supported package manager. Install Python 3 manually."
        exit 1
    fi
    PY=python3
fi
ok "python: $($PY --version 2>&1 | head -n1)"

# --- 2. git ---
if ! command -v git >/dev/null 2>&1; then
    say "git not found — installing"
    if [ "$(uname)" = "Darwin" ]; then
        brew install git
    elif command -v apt-get >/dev/null 2>&1; then
        sudo apt-get install -y git
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y git
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm git
    elif [ -n "$PREFIX" ] && [ -d "/data/data/com.termux" ]; then
        pkg install -y git
    else
        err "install git manually"; exit 1
    fi
fi
ok "git: $(git --version)"

# --- 3. clone or pull ---
if [ -d "$INSTALL_DIR/.git" ]; then
    say "updating $INSTALL_DIR"
    git -C "$INSTALL_DIR" pull --ff-only || true
else
    say "cloning into $INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR"
fi
ok "utilitools at $INSTALL_DIR"

# --- 4. install pyinit ---
if [ -f "$INSTALL_DIR/pyinit/install_pyinit.py" ]; then
    say "installing pyinit launcher"
    "$PY" "$INSTALL_DIR/pyinit/install_pyinit.py" || true
fi

echo
ok "done"
echo
echo "  run:    pyinit"
echo "  menu lists every tool. use 'pyinit NAME' to launch directly."
echo
