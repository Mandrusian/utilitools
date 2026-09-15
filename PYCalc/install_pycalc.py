#!/usr/bin/env python3
"""
PYCalc universal installer.

Usage (from the PYCalc project directory):
    python3 install_pycalc.py              # install
    python3 install_pycalc.py --dry-run    # preview
    python3 install_pycalc.py --uninstall  # remove

Detects OS and builds/installs the correct format:
    macOS   → /Applications/PYCalc.app
    Linux   → ~/.local/bin/pycalc + .desktop
    Windows → %LOCALAPPDATA%\\Programs\\PYCalc\\PYCalc.exe + Start Menu
    Termux  → $PREFIX/bin/pycalc (no compile; direct python wrapper)
"""

import argparse, os, platform, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC   = HERE / "PYCalc.py"
PNG   = HERE / "icon" / "master.png"


# ---------- UI ----------
def say(m=""): print(m, flush=True)
def ok(m):    print(f"  \033[92m✓\033[0m {m}", flush=True)
def warn(m):  print(f"  \033[93m!\033[0m {m}", flush=True)
def fail(m):  print(f"  \033[91m✗\033[0m {m}", flush=True)
def die(m, c=1): fail(m); sys.exit(c)


# ---------- detect ----------
def plat():
    if sys.platform == "darwin": return "macos"
    if sys.platform.startswith("win"): return "windows"
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    return "linux"

def arch():
    m = platform.machine().lower()
    return {"x86_64":"x86_64","amd64":"x86_64","arm64":"arm64","aarch64":"arm64"}.get(m, m)


# ---------- prereqs ----------
def check():
    if sys.version_info < (3, 9):
        die(f"Python 3.9+ required, found {platform.python_version()}")
    if not SRC.exists():
        die(f"PYCalc.py not found at {SRC}. Run from the project directory.")


def ensure_pyinstaller():
    try:
        subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                       capture_output=True, check=True)
        return
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    if shutil.which("pyinstaller"):
        return
    say("  Installing PyInstaller (user-level)...")
    cmd = [sys.executable, "-m", "pip", "install", "--user", "pyinstaller"]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        cmd.append("--break-system-packages")
        subprocess.run(cmd, check=True)


def make_ico(png_path, out_path):
    try:
        from PIL import Image
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "--user",
                        "Pillow", "--break-system-packages"],
                       check=True, capture_output=True)
        from PIL import Image
    Image.open(png_path).convert("RGBA").save(out_path, format="ICO",
        sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])


def make_icns(png_path, out_dir):
    iconset = out_dir / "PYCalc.iconset"
    if iconset.exists(): shutil.rmtree(iconset)
    iconset.mkdir()
    for px, suf in [(16,"16x16"),(32,"16x16@2x"),(32,"32x32"),(64,"32x32@2x"),
                    (128,"128x128"),(256,"128x128@2x"),(256,"256x256"),
                    (512,"256x256@2x"),(512,"512x512"),(1024,"512x512@2x")]:
        subprocess.run(["sips","-z",str(px),str(px),str(png_path),
                        "--out", str(iconset / f"icon_{suf}.png")],
                       check=True, capture_output=True)
    icns = out_dir / "PYCalc.icns"
    subprocess.run(["iconutil","-c","icns",str(iconset),"-o",str(icns)], check=True)
    shutil.rmtree(iconset)
    return icns


def build_cmd(name, icon):
    cmd = [sys.executable, "-m", "PyInstaller",
           "--onefile", "--console", "--noconfirm",
           "--name", name,
           "--hidden-import", "readline",
           "--hidden-import", "pyreadline3"]
    if icon: cmd += ["--icon", str(icon)]
    cmd.append(str(SRC))
    return cmd


# ---------- macos ----------
def install_macos(work, dry):
    say("\033[94m▸ macOS\033[0m")
    say("  generating icon..."); icns = make_icns(PNG, work); ok(icns.name)
    say("  building binary...")
    subprocess.run(build_cmd("PYCalc.bin", icns), cwd=work, check=True, capture_output=True)
    bin_ = work / "dist" / "PYCalc.bin"
    ok(f"{bin_.stat().st_size // 1024} KB")

    app = work / "PYCalc.app"
    (app / "Contents" / "MacOS").mkdir(parents=True)
    (app / "Contents" / "Resources").mkdir(parents=True)
    shutil.copy(bin_, app / "Contents" / "MacOS" / "PYCalc.bin")
    shutil.copy(icns, app / "Contents" / "Resources" / "PYCalc.icns")
    (app / "Contents" / "MacOS" / "PYCalc").write_text(
        '#!/bin/bash\nDIR="$(cd "$(dirname "$0")" && pwd)"\nexec "$DIR/PYCalc.bin"\n')
    (app / "Contents" / "MacOS" / "PYCalc").chmod(0o755)
    (app / "Contents" / "Info.plist").write_text(
'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleName</key><string>PYCalc</string>
<key>CFBundleDisplayName</key><string>PYCalc</string>
<key>CFBundleExecutable</key><string>PYCalc</string>
<key>CFBundleIdentifier</key><string>com.mandrusian.pycalc</string>
<key>CFBundleVersion</key><string>1.0</string>
<key>CFBundleShortVersionString</key><string>1.0</string>
<key>CFBundleIconFile</key><string>PYCalc</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSMinimumSystemVersion</key><string>11.0</string>
<key>NSHighResolutionCapable</key><true/>
</dict></plist>
''')
    subprocess.run(["codesign","--deep","--force","--sign","-",str(app)],
                   check=False, capture_output=True)
    target = Path("/Applications") / "PYCalc.app"
    say(f"  installing to {target}")
    if dry:
        ok("[dry-run]")
    else:
        if target.exists(): shutil.rmtree(target)
        shutil.copytree(app, target)
        seen = Path.home() / ".pycalc_seen"
        if seen.exists(): seen.unlink()
        ok(f"installed {target}")
    ok("open from Spotlight: ⌘-Space → PYCalc")


# ---------- linux ----------
def install_linux(work, dry):
    say("\033[94m▸ Linux\033[0m")
    say("  building binary...")
    subprocess.run(build_cmd("pycalc", None), cwd=work, check=True, capture_output=True)
    bin_ = work / "dist" / "pycalc"
    ok(f"{bin_.stat().st_size // 1024} KB")

    bin_dir = Path.home() / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    target = bin_dir / "pycalc"
    if dry:
        ok(f"[dry-run] would install to {target}")
        return
    shutil.copy(bin_, target); target.chmod(0o755)
    ok(f"binary: {target}")

    apps = Path.home() / ".local" / "share" / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    desktop = apps / "pycalc.desktop"
    desktop.write_text(f"""[Desktop Entry]
Type=Application
Name=PYCalc
Comment=Terminal mathematics engine
Exec={target}
Terminal=true
Categories=Utility;Calculator;Education;
""")
    ok(f"desktop: {desktop}")

    if str(bin_dir) not in os.environ.get("PATH",""):
        warn(f"add to PATH:  export PATH=\"{bin_dir}:$PATH\"")
    ok("run `pycalc` from any terminal")


# ---------- windows ----------
def install_windows(work, dry):
    say("\033[94m▸ Windows\033[0m")
    say("  generating icon..."); ico = work / "PYCalc.ico"; make_ico(PNG, ico); ok(ico.name)
    say("  building exe...")
    subprocess.run(build_cmd("PYCalc", ico), cwd=work, check=True, capture_output=True)
    exe = work / "dist" / "PYCalc.exe"
    ok(f"{exe.stat().st_size // 1024} KB")

    local = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
    tdir = local / "Programs" / "PYCalc"
    texe = tdir / "PYCalc.exe"
    if dry:
        ok(f"[dry-run] would install to {texe}")
        return
    tdir.mkdir(parents=True, exist_ok=True)
    shutil.copy(exe, texe)
    ok(f"installed: {texe}")

    sm = Path(os.environ.get("APPDATA","")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    lnk = sm / "PYCalc.lnk"
    ps = f'''$ws=New-Object -ComObject WScript.Shell
$s=$ws.CreateShortcut("{lnk}")
$s.TargetPath="{texe}"; $s.WorkingDirectory="{tdir}"; $s.IconLocation="{texe},0"
$s.Save()'''
    try:
        subprocess.run(["powershell","-NoProfile","-Command",ps], check=True, capture_output=True)
        ok(f"shortcut: {lnk}")
    except Exception as e:
        warn(f"shortcut failed: {e}")

    ps2 = f'''$d="{tdir}"; $p=[Environment]::GetEnvironmentVariable("Path","User")
if ($p -split ";" -notcontains $d) {{ [Environment]::SetEnvironmentVariable("Path","$p;$d","User") }}'''
    try:
        subprocess.run(["powershell","-NoProfile","-Command",ps2], check=True, capture_output=True)
        ok("added to PATH")
    except Exception:
        warn("PATH not modified")
    ok("search PYCalc in Start Menu")


# ---------- termux ----------
def install_termux(work, dry):
    say("\033[94m▸ Termux\033[0m")
    py = shutil.which("python3") or shutil.which("python")
    if not py:
        die("python not installed — run: pkg install python")
    home_src = Path.home() / ".pycalc" / "PYCalc.py"
    home_src.parent.mkdir(parents=True, exist_ok=True)
    prefix = Path(os.environ.get("PREFIX","/data/data/com.termux/files/usr"))
    target = prefix / "bin" / "pycalc"
    if dry:
        ok(f"[dry-run] would install source + wrapper {target}")
        return
    shutil.copy(SRC, home_src)
    ok(f"source: {home_src}")
    target.write_text(f'#!/data/data/com.termux/files/usr/bin/bash\nexec {py} "{home_src}" "$@"\n')
    target.chmod(0o755)
    ok(f"wrapper: {target}")
    if not Path("/sdcard/Download").exists():
        warn("run `termux-setup-storage` to allow SVG export to /sdcard")
    ok("run `pycalc` from any Termux prompt")


# ---------- uninstall ----------
def uninstall():
    p = plat()
    say(f"\033[94m▸ Uninstall ({p})\033[0m")
    removed = 0
    if p == "macos":
        t = Path("/Applications") / "PYCalc.app"
        if t.exists(): shutil.rmtree(t); ok(t); removed += 1
    elif p == "linux":
        for t in [Path.home()/".local"/"bin"/"pycalc",
                  Path.home()/".local"/"share"/"applications"/"pycalc.desktop"]:
            if t.exists(): t.unlink(); ok(t); removed += 1
    elif p == "windows":
        local = Path(os.environ.get("LOCALAPPDATA",""))
        t = local / "Programs" / "PYCalc"
        if t.exists(): shutil.rmtree(t); ok(t); removed += 1
        lnk = Path(os.environ.get("APPDATA",""))/"Microsoft"/"Windows"/"Start Menu"/"Programs"/"PYCalc.lnk"
        if lnk.exists(): lnk.unlink(); ok(lnk); removed += 1
    elif p == "termux":
        for t in [Path(os.environ.get("PREFIX",""))/"bin"/"pycalc",
                  Path.home()/".pycalc"]:
            if t.exists():
                shutil.rmtree(t) if t.is_dir() else t.unlink()
                ok(t); removed += 1
    if removed == 0:
        warn("nothing to uninstall")
    say("\n  Config files kept (delete manually for a clean slate):")
    for cfg in [Path.home()/".pycalc_config.json",
                Path.home()/".pycalc_history",
                Path.home()/".pycalc_sessions"]:
        if cfg.exists(): say(f"    {cfg}")


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description="PYCalc universal installer")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    say()
    say("  \033[94m╔═════════════════════════════════╗\033[0m")
    say("  \033[94m║\033[0m   \033[97mPYCalc installer\033[0m              \033[94m║\033[0m")
    say("  \033[94m╚═════════════════════════════════╝\033[0m")
    say()

    if a.uninstall:
        uninstall(); return

    check()
    p, ar = plat(), arch()
    say(f"  Platform:  \033[97m{p}\033[0m ({ar})")
    say(f"  Python:    \033[97m{platform.python_version()}\033[0m")
    say()

    if p in ("macos", "linux", "windows"):
        ensure_pyinstaller()
    if not PNG.exists() and p in ("macos", "windows"):
        die(f"icon/master.png not found at {PNG}")

    with tempfile.TemporaryDirectory(prefix="pycalc_build_") as tmp:
        work = Path(tmp)
        {"macos": install_macos, "linux": install_linux,
         "windows": install_windows, "termux": install_termux}[p](work, a.dry_run)

    say()
    say("  \033[92mDone.\033[0m")


if __name__ == "__main__":
    main()
