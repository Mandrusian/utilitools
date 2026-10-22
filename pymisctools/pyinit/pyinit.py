#!/usr/bin/env python3
"""pyinit — launcher for the utilitools suite."""

import json
import os
import re
import subprocess
import sys


RESET  = "\033[0m"
LGRAY  = "\033[37m"
DGRAY  = "\033[90m"
BLUE   = "\033[94m"
DBLUE  = "\033[34m"
WHITE  = "\033[97m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
MAGENTA= "\033[95m"


def _build_logo():
    return [
        "\033[0;31;40m                                             \033[0m",
        "\033[0;31;40m                                        \033[0;91;40m\u2584\033[0;91;41m\u2580\033[0;90;40m\u2584\033[0;31;40m  \033[0m",
        "\033[0;31;40m                   \033[0;91;40m\u2588\033[0;90;40m\u2584\033[0;31;40m             \033[0;91;40m\u2588\033[0;90;40m\u2584\033[0;31;40m   \033[0;91;40m\u2588\033[0;31;40m\u2588\u2588\033[0;90;41m\u2584\033[0;90;40m\u258c\033[0;31;40m \033[0m",
        "\033[0;31;40m                  \033[0;91;40m\u2590\033[0;31;40m\u2588\u2588\033[0;90;40m\u258c\033[0;31;40m \033[0;91;41m\u2588\u2580\033[0;31;40m\u2584\u2584\u2584\033[0;91;41m\u2580\u2580\033[0;31;40m\u2584  \033[0;91;40m\u2590\033[0;31;40m\u2588\u2588\033[0;90;40m\u258c\033[0;31;40m \033[0;91;40m\u2590\033[0;31;40m\u2588\u2588\033[0;90;40m\u258c\033[0;31;40m   \033[0m",
        "\033[0;31;40m \033[0;91;40m\u2584\033[0;91;41m\u2580\033[0;31;40m\u2588\u2588\033[0;90;41m\u2580\u2580\033[0;90;40m\u2584\033[0;31;40m \033[0;91;40m\u2584\033[0;91;41m\u2580\033[0;31;40m\u2588\033[0;90;40m\u258c\033[0;31;40m  \033[0;90;40m\u2584\033[0;31;40m  \033[0;90;40m\u2584\u2584\u2580\033[0;31;40m  \033[0;91;40m\u2590\033[0;31;40m\u2588\033[0;90;41m\u2584\033[0;31;40m\u2580\033[0;91;41m\u2584\033[0;31;40m\u2588\u2588\033[0;90;41m\u2590\033[0;31;40m  \033[0;90;40m\u2584\u2584\u2580\033[0;31;40m  \033[0;91;41m\u258c\033[0;31;40m\u2588\u2588\u2588\033[0;90;41m\u2580\u2580\033[0;90;40m\u2584\033[0m",
        "\033[0;91;40m\u2590\033[0;31;40m\u2588\u2588\033[0;90;41m\u2584\033[0;90;40m\u2580\033[0;31;40m \033[0;91;40m\u2590\033[0;31;40m\u2588\033[0;91;40m\u2590\033[0;31;40m\u2588\u2588\033[0;90;41m\u2584\033[0;31;40m  \033[0;91;40m\u2590\033[0;31;40m\u2588\033[0;90;40m\u258c\033[0;91;40m\u2590\033[0;31;40m\u2588\033[0;90;41m\u2590\033[0;31;40m   \033[0;91;41m\u258c\033[0;31;40m\u2588\u2588\033[0;90;40m\u258c\033[0;31;40m  \033[0;91;41m\u258c\033[0;31;40m\u2588\033[0;90;40m\u258c\033[0;91;40m\u2590\033[0;31;40m\u2588\033[0;90;41m\u2590\033[0;31;40m  \033[0;91;40m\u2590\033[0;31;40m\u2588\033[0;90;41m\u2590\033[0;90;40m\u2580\033[0;31;40m    \033[0m",
        "\033[0;91;41m\u258c \033[0;90;41m\u2590\033[0;31;40m \033[0;91;40m\u2584\033[0;31;40m\u2584\033[0;91;41m\u2580\033[0;90;41m\u2590\033[0;91;41m\u258c \033[0;90;41m\u2590\033[0;90;40m\u2584\033[0;31;40m \u2584\033[0;91;41m\u2580\033[0;90;41m\u2590\033[0;31;40m \033[0;91;41m\u258c \033[0;90;41m\u2590\033[0;31;40m  \033[0;91;40m\u2590\033[0;31;40m\u2588\u2588\033[0;90;41m\u2590\033[0;31;40m  \033[0;91;40m\u2590\033[0;31;40m\u2588\u2588\033[0;90;40m\u258c\033[0;91;41m\u258c \033[0;90;41m\u2590\033[0;31;40m  \033[0;91;41m\u258c \033[0;90;41m\u2590\033[0;90;40m\u2584\033[0;31;40m    \033[0m",
        "\033[0;91;40m\u2590\033[0;31;40m\u2588\033[0;90;41m\u2580\033[0;90;40m\u258c\033[0;91;40m\u2580\033[0;31;40m\u2580\033[0;90;40m\u2580\033[0;31;40m \033[0;91;40m\u2580\033[0;91;41m\u2584\033[0;31;40m\u2588\u2588\033[0;90;41m\u2584\033[0;91;41m\u2584\033[0;31;40m\u2588\u2588\033[0;90;40m\u258c\033[0;91;40m\u2580\033[0;91;41m\u2584\033[0;31;40m\u2588\033[0;90;40m\u258c\033[0;31;40m \033[0;91;40m\u2588\033[0;91;41m\u2584\033[0;31;40m\u2588\u2588\033[0;90;41m\u2588\033[0;31;40m \033[0;91;41m\u2588\u2584\033[0;31;40m\u2588\033[0;90;41m\u2590\033[0;91;40m\u2580\033[0;91;41m\u2584\033[0;31;40m\u2588\033[0;90;40m\u258c\033[0;31;40m \033[0;91;40m\u2580\033[0;91;41m\u2584\033[0;31;40m\u2588\u2588\033[0;90;41m\u2584\u2584\033[0;90;40m\u2580\033[0;31;40m \033[0m",
        "\033[0;91;40m\u2590\033[0;31;40m\u2588\033[0;90;41m\u2584\033[0;31;40m          \033[0;91;41m\u258c\033[0;31;40m\u2588\033[0;90;41m\u2590\033[0;31;40m \033[0;37;40m                            \033[0m",
        "\033[0;91;40m\u2590\033[0;31;40m\u2588\033[0;90;40m\u258c\033[0;31;40m     \033[0;90;41m\u2580\033[0;91;41m\u2584\033[0;90;41m\u2584\033[0;31;40m\u2584\033[0;91;41m\u2580\033[0;31;40m\u2588\033[0;90;41m\u2584\033[0;31;40m  \033[0;37;40m                            \033[0m",
    ]


def logo():
    for line in _build_logo():
        print(line)
    print()


def _supports_color():
    if os.environ.get("NO_COLOR"): return False
    if os.environ.get("PYINIT_NO_COLOR"): return False
    if os.environ.get("PYINIT_FORCE_COLOR"): return True
    if not sys.stdout.isatty(): return False
    return True


def _strip_color():
    global RESET, LGRAY, DGRAY, BLUE, DBLUE, WHITE, CYAN, GREEN, YELLOW, RED, MAGENTA
    RESET = LGRAY = DGRAY = BLUE = DBLUE = WHITE = CYAN = GREEN = YELLOW = RED = MAGENTA = ""


# ============================================================
# ROOT DISCOVERY
# ============================================================
def find_root():
    """Where is ~/utilitools?"""
    env = os.environ.get("UTILITOOLS_ROOT")
    if env and os.path.isdir(env): return os.path.abspath(env)
    here = os.path.dirname(os.path.abspath(__file__))
    # walk up until we find a folder that contains other folders with install_*.py
    cur = here
    for _ in range(4):
        parent = os.path.dirname(cur)
        if parent == cur: break
        cur = parent
        if os.path.isdir(cur):
            subs = [d for d in os.listdir(cur) if os.path.isdir(os.path.join(cur, d))]
            if len(subs) >= 1:
                # accept if at least one subfolder contains a *.py file
                for s in subs:
                    sd = os.path.join(cur, s)
                    try:
                        if any(f.endswith(".py") for f in os.listdir(sd)):
                            return cur
                    except OSError:
                        pass
    # fallback: two levels up from this file
    return os.path.dirname(os.path.dirname(here))


# ============================================================
# TOOL DISCOVERY
# ============================================================
def _read_desc(folder):
    r = os.path.join(folder, "README.md")
    if not os.path.exists(r): return ""
    try:
        with open(r) as f: lines = f.readlines()
    except OSError:
        return ""
    seen_title = False
    for line in lines:
        s = line.strip()
        if not s: continue
        if s.startswith("#"):
            if not seen_title:
                seen_title = True
                continue
            return s.lstrip("#").strip()[:90]
        return s[:90]
    return ""


def discover(root):
    tools = []
    if not os.path.isdir(root): return tools
    for name in sorted(os.listdir(root), key=lambda s: s.lower()):
        d = os.path.join(root, name)
        if not os.path.isdir(d): continue
        if name.startswith("."): continue
        if name.lower() == "pyinit": continue

        # explicit manifest wins
        manifest = os.path.join(d, "pyinit.json")
        if os.path.exists(manifest):
            try:
                with open(manifest) as f: m = json.load(f)
                entry_name = m.get("entry")
                if entry_name:
                    ep = os.path.join(d, entry_name)
                    if os.path.exists(ep):
                        tools.append({
                            "name":  m.get("name", name),
                            "dir":   d,
                            "entry": ep,
                            "desc":  m.get("description", _read_desc(d)),
                        })
                        continue
            except Exception:
                pass

        # auto-detect entry
        candidates = [name + ".py", name.lower() + ".py", name.replace(" ", "") + ".py"]
        entry_path = None
        for c in candidates:
            p = os.path.join(d, c)
            if os.path.exists(p):
                entry_path = p; break
        if not entry_path:
            for f in sorted(os.listdir(d)):
                if f.endswith(".py") and not f.startswith("install_") and not f.startswith("_") and f != "__init__.py":
                    entry_path = os.path.join(d, f); break
        if not entry_path: continue

        tools.append({
            "name":  name,
            "dir":   d,
            "entry": entry_path,
            "desc":  _read_desc(d),
        })
    return tools


# ============================================================
# UI
# ============================================================
def clear():
    sys.stdout.write("\033[2J\033[H"); sys.stdout.flush()


def divider():
    import shutil
    w = min(max(shutil.get_terminal_size((100, 30)).columns - 4, 40), 80)
    print("  " + DGRAY + "\u2500" * w + RESET)


def banner(root):
    clear()
    logo()
    print(f"  {DGRAY}{root}{RESET}")
    print()


def render_menu(tools):
    for i, t in enumerate(tools, 1):
        desc = t["desc"] or ""
        print(f"  {BLUE}[{i}]{RESET} {WHITE}{t['name']:<14}{RESET} {DGRAY}{desc}{RESET}")
    print()
    print(f"  {DGRAY}[r]{RESET} refresh   {DGRAY}[q]{RESET} quit")
    print()


# ============================================================
# LAUNCH
# ============================================================
def launch(tool, args=None):
    cmd = [sys.executable, tool["entry"]]
    if args: cmd += args
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"  {RED}\u2715{RESET} failed to launch {tool['name']}: {e}")
        try: input(f"  {DGRAY}press enter to continue\u2026{RESET}")
        except (EOFError, KeyboardInterrupt): pass


# ============================================================
# MAIN
# ============================================================
def main():
    if not _supports_color(): _strip_color()
    root = find_root()
    if not os.path.isdir(root):
        print(f"  {RED}\u2715{RESET} utilitools root not found")
        print(f"  {DGRAY}set UTILITOOLS_ROOT or move this file into ~/utilitools/pyinit/{RESET}")
        sys.exit(1)

    tools = discover(root)
    if not tools:
        print(f"  {RED}\u2715{RESET} no tools found in {root}")
        sys.exit(1)

    # allow `pyinit toolname [args...]` to skip the menu
    argv = sys.argv[1:]
    if argv:
        target = argv[0].lower()
        for t in tools:
            if t["name"].lower() == target or os.path.basename(t["entry"]).lower() == target:
                launch(t, argv[1:]); return
        # not found: fall through to menu with an error printed once

    while True:
        banner(root)
        render_menu(tools)
        if argv:
            print(f"  {DGRAY}no tool matched '{argv[0]}'{RESET}")
            argv = []
            print()
        try:
            choice = input(f"  {BLUE}\u276f{RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(); return
        if not choice: continue
        if choice in ("q", "quit", "exit"): return
        if choice in ("r", "refresh"):
            tools = discover(root); continue
        if choice.isdigit():
            n = int(choice)
            if 1 <= n <= len(tools):
                clear()
                launch(tools[n - 1])
                # loop back to menu after the tool exits
                continue
        # maybe a name
        for t in tools:
            if t["name"].lower() == choice or os.path.basename(t["entry"]).lower().startswith(choice):
                clear()
                launch(t)
                break


if __name__ == "__main__":
    main()
