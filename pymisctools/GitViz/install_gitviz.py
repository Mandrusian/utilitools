#!/usr/bin/env python3
"""Universal installer for GitViz.

  python3 install_gitviz.py            # install
  python3 install_gitviz.py --uninstall
  python3 install_gitviz.py --build    # also build native bundle
"""

import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "gitviz.py")
APP_NAME = "GitViz"


def detect_platform():
    if sys.platform == "darwin": return "macos"
    if sys.platform == "win32": return "windows"
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    return "linux"


def info(m): print(f"  \u2022 {m}")
def ok(m):   print(f"  \u2713 {m}")
def fail(m): print(f"  \u2715 {m}"); sys.exit(1)


def install_macos():
    dest_dir = os.path.expanduser("~/Library/Application Support/GitViz")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, "gitviz.py")
    shutil.copy2(SRC, dest)
    launcher_dir = "/usr/local/bin" if os.access("/usr/local/bin", os.W_OK) else os.path.expanduser("~/.local/bin")
    os.makedirs(launcher_dir, exist_ok=True)
    launcher = os.path.join(launcher_dir, "gitviz")
    with open(launcher, "w") as f:
        f.write(f"#!/bin/sh\nexec python3 {dest!r} \"$@\"\n")
    os.chmod(launcher, 0o755)
    ok(f"installed  {dest}")
    ok(f"launcher   {launcher}")
    if launcher_dir == os.path.expanduser("~/.local/bin"):
        info("add ~/.local/bin to PATH if not already there")


def install_linux():
    dest_dir = os.path.expanduser("~/.local/share/gitviz")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, "gitviz.py")
    shutil.copy2(SRC, dest)
    launcher_dir = os.path.expanduser("~/.local/bin")
    os.makedirs(launcher_dir, exist_ok=True)
    launcher = os.path.join(launcher_dir, "gitviz")
    with open(launcher, "w") as f:
        f.write(f"#!/bin/sh\nexec python3 {dest!r} \"$@\"\n")
    os.chmod(launcher, 0o755)
    ok(f"installed  {dest}")
    ok(f"launcher   {launcher}")
    info("add ~/.local/bin to PATH if not already there")


def install_termux():
    dest_dir = os.path.expanduser("~/.local/share/gitviz")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, "gitviz.py")
    shutil.copy2(SRC, dest)
    launcher_dir = os.path.expanduser("~/.local/bin")
    os.makedirs(launcher_dir, exist_ok=True)
    launcher = os.path.join(launcher_dir, "gitviz")
    with open(launcher, "w") as f:
        f.write(f"#!/data/data/com.termux/files/usr/bin/sh\nexec python3 {dest!r} \"$@\"\n")
    os.chmod(launcher, 0o755)
    ok(f"installed  {dest}")
    ok(f"launcher   {launcher}")


def install_windows():
    dest_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "GitViz")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, "gitviz.py")
    shutil.copy2(SRC, dest)
    bat = os.path.join(dest_dir, "gitviz.bat")
    with open(bat, "w") as f:
        f.write(f'@echo off\r\npython "{dest}" %*\r\n')
    ok(f"installed  {dest}")
    ok(f"launcher   {bat}")
    info(f"add {dest_dir} to your PATH to run 'gitviz' from anywhere")


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
                    "--console", "--name", "gitviz", SRC], cwd=HERE, check=False)
    info(f"exe in {os.path.join(HERE, 'dist', 'gitviz.exe')}")


def uninstall():
    plat = detect_platform()
    if plat == "macos":
        for p in [os.path.expanduser("~/Library/Application Support/GitViz"),
                  "/usr/local/bin/gitviz",
                  os.path.expanduser("~/.local/bin/gitviz")]:
            if os.path.exists(p):
                if os.path.isdir(p): shutil.rmtree(p)
                else: os.remove(p)
                ok(f"removed {p}")
    elif plat in ("linux", "termux"):
        for p in [os.path.expanduser("~/.local/share/gitviz"),
                  os.path.expanduser("~/.local/bin/gitviz")]:
            if os.path.exists(p):
                if os.path.isdir(p): shutil.rmtree(p)
                else: os.remove(p)
                ok(f"removed {p}")
    elif plat == "windows":
        d = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "GitViz")
        if os.path.isdir(d):
            shutil.rmtree(d); ok(f"removed {d}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--build", action="store_true")
    args = ap.parse_args()
    if not os.path.exists(SRC):
        fail("gitviz.py not found next to installer")
    plat = detect_platform()
    print(f"  GitViz installer \u2014 detected {plat}")
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
