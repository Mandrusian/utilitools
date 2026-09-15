#!/usr/bin/env python3
"""Installer for pyinit.

  python3 install_pyinit.py            # install launcher on PATH
  python3 install_pyinit.py --uninstall
"""

import argparse
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "pyinit.py")


def detect_platform():
    if sys.platform == "darwin": return "macos"
    if sys.platform == "win32": return "windows"
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    return "linux"


def info(m): print(f"  \u2022 {m}")
def ok(m):   print(f"  \u2713 {m}")
def fail(m): print(f"  \u2715 {m}"); sys.exit(1)


def _write_unix_launcher(path, root):
    with open(path, "w") as f:
        f.write(f"#!/bin/sh\nUTILITOOLS_ROOT={root!r} exec python3 {SRC!r} \"$@\"\n")
    os.chmod(path, 0o755)


def install_macos(root):
    launcher_dir = "/usr/local/bin" if os.access("/usr/local/bin", os.W_OK) else os.path.expanduser("~/.local/bin")
    os.makedirs(launcher_dir, exist_ok=True)
    path = os.path.join(launcher_dir, "pyinit")
    _write_unix_launcher(path, root)
    ok(f"launcher   {path}")
    if launcher_dir == os.path.expanduser("~/.local/bin"):
        info("add ~/.local/bin to PATH if not already there")


def install_linux(root):
    launcher_dir = os.path.expanduser("~/.local/bin")
    os.makedirs(launcher_dir, exist_ok=True)
    path = os.path.join(launcher_dir, "pyinit")
    _write_unix_launcher(path, root)
    ok(f"launcher   {path}")
    info("add ~/.local/bin to PATH if not already there")


def install_termux(root):
    launcher_dir = os.path.expanduser("~/.local/bin")
    os.makedirs(launcher_dir, exist_ok=True)
    path = os.path.join(launcher_dir, "pyinit")
    with open(path, "w") as f:
        f.write(f"#!/data/data/com.termux/files/usr/bin/sh\nUTILITOOLS_ROOT={root!r} exec python3 {SRC!r} \"$@\"\n")
    os.chmod(path, 0o755)
    ok(f"launcher   {path}")


def install_windows(root):
    dest_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "pyinit")
    os.makedirs(dest_dir, exist_ok=True)
    bat = os.path.join(dest_dir, "pyinit.bat")
    with open(bat, "w") as f:
        f.write(f'@echo off\r\nset UTILITOOLS_ROOT={root}\r\npython "{SRC}" %*\r\n')
    ok(f"launcher   {bat}")
    info(f"add {dest_dir} to your PATH to run 'pyinit' from anywhere")


def uninstall():
    plat = detect_platform()
    paths = []
    if plat == "macos":
        paths = ["/usr/local/bin/pyinit", os.path.expanduser("~/.local/bin/pyinit")]
    elif plat in ("linux", "termux"):
        paths = [os.path.expanduser("~/.local/bin/pyinit")]
    elif plat == "windows":
        d = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "pyinit")
        if os.path.isdir(d): shutil.rmtree(d); ok(f"removed {d}")
        return
    for p in paths:
        if os.path.exists(p):
            os.remove(p); ok(f"removed {p}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--root", help="path to utilitools root (default: two levels up from this file)")
    args = ap.parse_args()
    if not os.path.exists(SRC): fail("pyinit.py not found next to installer")
    if args.uninstall: uninstall(); return
    root = args.root or os.path.dirname(HERE)
    root = os.path.abspath(root)
    if not os.path.isdir(root): fail(f"root not found: {root}")
    plat = detect_platform()
    print(f"  pyinit installer \u2014 detected {plat}")
    print(f"  root       {root}")
    if plat == "macos":   install_macos(root)
    elif plat == "linux": install_linux(root)
    elif plat == "termux": install_termux(root)
    elif plat == "windows": install_windows(root)
    else: fail(f"unsupported platform: {plat}")


if __name__ == "__main__":
    main()
