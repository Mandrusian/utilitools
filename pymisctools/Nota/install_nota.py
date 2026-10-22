#!/usr/bin/env python3
"""Universal installer for Nota.

  python3 install_nota.py            # install
  python3 install_nota.py --uninstall
  python3 install_nota.py --build    # also build a native bundle
"""

import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "nota.py")
APP_NAME = "Nota"


def detect_platform():
    if sys.platform == "darwin": return "macos"
    if sys.platform == "win32": return "windows"
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    return "linux"


def info(m): print(f"  \u2022 {m}")
def ok(m):   print(f"  \u2713 {m}")
def fail(m): print(f"  \u2715 {m}"); sys.exit(1)


def install_macos():
    dest_dir = os.path.expanduser("~/Library/Application Support/Nota")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, "nota.py")
    shutil.copy2(SRC, dest)
    launcher_dir = "/usr/local/bin" if os.access("/usr/local/bin", os.W_OK) else os.path.expanduser("~/.local/bin")
    os.makedirs(launcher_dir, exist_ok=True)
    launcher = os.path.join(launcher_dir, "nota")
    with open(launcher, "w") as f:
        f.write(f"#!/bin/sh\nexec python3 {dest!r} \"$@\"\n")
    os.chmod(launcher, 0o755)
    ok(f"installed  {dest}")
    ok(f"launcher   {launcher}")
    if launcher_dir == os.path.expanduser("~/.local/bin"):
        info("add ~/.local/bin to PATH if not already there")


def install_linux():
    dest_dir = os.path.expanduser("~/.local/share/nota")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, "nota.py")
    shutil.copy2(SRC, dest)
    launcher_dir = os.path.expanduser("~/.local/bin")
    os.makedirs(launcher_dir, exist_ok=True)
    launcher = os.path.join(launcher_dir, "nota")
    with open(launcher, "w") as f:
        f.write(f"#!/bin/sh\nexec python3 {dest!r} \"$@\"\n")
    os.chmod(launcher, 0o755)
    ok(f"installed  {dest}")
    ok(f"launcher   {launcher}")
    info("add ~/.local/bin to PATH if not already there")


def install_termux():
    dest_dir = os.path.expanduser("~/.local/share/nota")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, "nota.py")
    shutil.copy2(SRC, dest)
    launcher_dir = os.path.expanduser("~/.local/bin")
    os.makedirs(launcher_dir, exist_ok=True)
    launcher = os.path.join(launcher_dir, "nota")
    with open(launcher, "w") as f:
        f.write(f"#!/data/data/com.termux/files/usr/bin/sh\nexec python3 {dest!r} \"$@\"\n")
    os.chmod(launcher, 0o755)
    ok(f"installed  {dest}")
    ok(f"launcher   {launcher}")


def install_windows():
    dest_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Nota")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, "nota.py")
    shutil.copy2(SRC, dest)
    bat = os.path.join(dest_dir, "nota.bat")
    with open(bat, "w") as f:
        f.write(f'@echo off\r\npython "{dest}" %*\r\n')
    ok(f"installed  {dest}")
    ok(f"launcher   {bat}")
    info(f"add {dest_dir} to your PATH to run 'nota' from anywhere")


def build_macos_app():
    try:
        import PyInstaller  # noqa
    except ImportError:
        info("PyInstaller not found, skipping .app build (pip install pyinstaller)")
        return
    info("building .app (this can take a minute)")
    subprocess.run([sys.executable, "-m", "PyInstaller", "--windowed", "--name", APP_NAME,
                    "--onefile", SRC], cwd=HERE, check=False)
    info(f"binary in {os.path.join(HERE, 'dist', APP_NAME)}")


def build_windows_exe():
    try:
        import PyInstaller  # noqa
    except ImportError:
        info("PyInstaller not found, skipping .exe build (pip install pyinstaller)")
        return
    info("building .exe")
    subprocess.run([sys.executable, "-m", "PyInstaller", "--onefile",
                    "--console", "--name", "nota", SRC], cwd=HERE, check=False)
    info(f"exe in {os.path.join(HERE, 'dist', 'nota.exe')}")


def uninstall():
    plat = detect_platform()
    if plat == "macos":
        for p in [os.path.expanduser("~/Library/Application Support/Nota"),
                  "/usr/local/bin/nota",
                  os.path.expanduser("~/.local/bin/nota")]:
            if os.path.exists(p):
                if os.path.isdir(p): shutil.rmtree(p)
                else: os.remove(p)
                ok(f"removed {p}")
    elif plat in ("linux", "termux"):
        for p in [os.path.expanduser("~/.local/share/nota"),
                  os.path.expanduser("~/.local/bin/nota")]:
            if os.path.exists(p):
                if os.path.isdir(p): shutil.rmtree(p)
                else: os.remove(p)
                ok(f"removed {p}")
    elif plat == "windows":
        d = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Nota")
        if os.path.isdir(d):
            shutil.rmtree(d); ok(f"removed {d}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--build", action="store_true", help="also build native bundle")
    args = ap.parse_args()
    if not os.path.exists(SRC):
        fail("nota.py not found next to installer")
    plat = detect_platform()
    print(f"  Nota installer \u2014 detected {plat}")
    if args.uninstall: uninstall(); return
    if plat == "macos":   install_macos()
    elif plat == "linux": install_linux()
    elif plat == "termux": install_termux()
    elif plat == "windows": install_windows()
    else: fail(f"unsupported platform: {plat}")
    if args.build:
        if plat == "macos": build_macos_app()
        elif plat == "windows": build_windows_exe()
        else: info("native bundle build only supported on macOS/Windows")


if __name__ == "__main__":
    main()
