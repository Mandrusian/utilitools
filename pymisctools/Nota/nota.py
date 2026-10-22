#!/usr/bin/env python3
"""Nota — plain-text notebooks for the terminal."""

import argparse
import ast
import atexit
import json
import math
import os
import re
import shutil
import sys
import time


# ============================================================
# READLINE
# ============================================================
def _is_wine():
    if os.environ.get("WINEPREFIX") or os.environ.get("WINEDLLPATH"):
        return True
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        ntdll = ctypes.windll.ntdll
        ntdll.wine_get_version.restype = ctypes.c_char_p
        return bool(ntdll.wine_get_version())
    except Exception:
        return False


READLINE_OK = False
try:
    import readline
    READLINE_OK = True
    _HISTFILE = os.path.expanduser("~/.nota_history")
    try: readline.read_history_file(_HISTFILE)
    except (FileNotFoundError, OSError): pass
    readline.set_history_length(2000)
    def _save_history():
        try: readline.write_history_file(_HISTFILE)
        except OSError: pass
    atexit.register(_save_history)
except ImportError:
    try:
        import pyreadline3 as readline
        READLINE_OK = True
        _HISTFILE = os.path.expanduser("~/.nota_history")
        try: readline.read_history_file(_HISTFILE)
        except (FileNotFoundError, OSError): pass
    except ImportError:
        pass


def _paint(s):
    if not READLINE_OK: return s
    return re.sub(r"\x1b\[[0-9;]*m", lambda m: "\001" + m.group() + "\002", s)


def prompt_main():
    return _paint(f"  {BLUE}\u276f{RESET} ")


def prompt_choice():
    return _paint(f"  {BLUE}\u276f{RESET} ")


# ============================================================
# THEME
# ============================================================
RESET = "\033[0m"
THEME_PRESETS = {
    "default": {
        "LGRAY":"\033[37m","DGRAY":"\033[90m","BLUE":"\033[94m","DBLUE":"\033[34m",
        "WHITE":"\033[97m","CYAN":"\033[96m","GREEN":"\033[92m","YELLOW":"\033[93m",
        "RED":"\033[91m","MAGENTA":"\033[95m",
        "RAINBOW":["\033[91m","\033[33m","\033[93m","\033[92m","\033[96m","\033[94m","\033[95m"],
    },
    "dark": {
        "LGRAY":"\033[38;5;245m","DGRAY":"\033[38;5;240m","BLUE":"\033[38;5;75m","DBLUE":"\033[38;5;25m",
        "WHITE":"\033[38;5;255m","CYAN":"\033[38;5;80m","GREEN":"\033[38;5;78m","YELLOW":"\033[38;5;222m",
        "RED":"\033[38;5;203m","MAGENTA":"\033[38;5;177m",
        "RAINBOW":["\033[38;5;203m","\033[38;5;215m","\033[38;5;222m","\033[38;5;120m","\033[38;5;80m","\033[38;5;75m","\033[38;5;177m"],
    },
    "mono": {k: "\033[37m" for k in ("LGRAY","DGRAY","BLUE","DBLUE","WHITE","CYAN","GREEN","YELLOW","RED","MAGENTA")},
    "none": {k: "" for k in ("LGRAY","DGRAY","BLUE","DBLUE","WHITE","CYAN","GREEN","YELLOW","RED","MAGENTA")},
}
THEME_PRESETS["mono"]["RAINBOW"] = ["\033[37m"] * 7
THEME_PRESETS["none"]["RAINBOW"] = [""] * 7

LGRAY=DGRAY=BLUE=DBLUE=WHITE=CYAN=GREEN=YELLOW=RED=MAGENTA=""
RAINBOW = []


def apply_theme():
    g = globals()
    for k, v in THEME_PRESETS[STATE["theme"]].items():
        g[k] = v


# ============================================================
# STATE / CONFIG
# ============================================================
STATE = {"theme": "default", "rainbow": "auto", "animations": True, "precision": 6}
CONFIG_PATH = os.path.expanduser("~/.nota_config.json")
FIRST_RUN_FLAG = os.path.expanduser("~/.nota_seen")


def load_config():
    try:
        with open(CONFIG_PATH) as f: data = json.load(f)
        for k in ("theme","rainbow","animations","precision"):
            if k in data: STATE[k] = data[k]
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass


def save_config():
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump({k: STATE[k] for k in ("theme","rainbow","animations","precision")}, f, indent=2)
    except OSError:
        pass


def is_first_run(): return not os.path.exists(FIRST_RUN_FLAG)
def mark_seen():
    try: open(FIRST_RUN_FLAG, "w").close()
    except OSError: pass


def _supports_color():
    if os.environ.get("NO_COLOR"): return False
    if os.environ.get("NOTA_NO_COLOR"): return False
    if os.environ.get("NOTA_FORCE_COLOR"): return True
    if _is_wine(): return False
    if not sys.stdout.isatty(): return False
    return True


def _strip_ansi_if_needed():
    if _supports_color(): return
    for preset in THEME_PRESETS.values():
        for k in list(preset.keys()):
            if k == "RAINBOW": preset[k] = [""] * 7
            else: preset[k] = ""


# ============================================================
# LOGO
# ============================================================
def _build_logo():
    return [
 [(WHITE,"\u250c\u2500\u2500\u2500\u2500\u2500\u2510"),(DGRAY,"\u2510"),(LGRAY,"     \u250c"),(WHITE,"\u2500\u2500\u2500\u2510"),(DGRAY,"\u2510"),(LGRAY,"   "),(WHITE,"\u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510"),(DGRAY,"\u2510"),(LGRAY,"   "),(WHITE,"\u250c\u2500\u2500\u2500\u2510"),(DGRAY,"\u2510"),(LGRAY,"  ")],
 [(LGRAY,"\u2502"),(BLUE,"\u2593\u2593\u2593\u2593\u2593"),(WHITE,"\u2514\u2500\u2510"),(DGRAY,"\u2510"),(LGRAY," \u250c"),(WHITE,"\u2500\u2518"),(BLUE,"\u2593\u2593\u2593"),(WHITE,"\u2514\u2500\u2510"),(DGRAY,"\u2510"),(LGRAY," \u2502"),(BLUE,"\u2593\u2593\u2593\u2593\u2593\u2593\u2593"),(WHITE,"\u2502"),(DGRAY,"\u2502"),(LGRAY," \u250c"),(WHITE,"\u2500\u2518"),(BLUE,"\u2593\u2593\u2593"),(WHITE,"\u2514\u2500\u2510"),(DGRAY,"\u2510")],
 [(LGRAY,"\u2502"),(BLUE,"\u2591\u2591"),(WHITE,"\u250c"),(LGRAY,"\u2500\u2510"),(BLUE,"\u2591\u2591"),(WHITE,"\u2502"),(DGRAY,"\u2502"),(LGRAY," \u2502"),(BLUE,"\u2591\u2591"),(WHITE,"\u250c"),(LGRAY,"\u2500\u2510"),(BLUE,"\u2591\u2591"),(WHITE,"\u2502"),(DGRAY,"\u2502"),(LGRAY," \u2514\u2500\u2510"),(BLUE,"\u2591\u2591"),(LGRAY,"\u2500\u2500\u2500"),(WHITE,"\u2518"),(DGRAY,"\u2514"),(LGRAY," \u2502"),(BLUE,"\u2591\u2591"),(WHITE,"\u2510-"),(LGRAY,"\u250c"),(BLUE,"\u2591\u2591"),(WHITE,"\u2502"),(DGRAY,"\u2502")],
 [(LGRAY,"\u2502"),(DGRAY,"\u2593\u2593"),(WHITE,"\u2502"),(DGRAY,"\u2502"),(LGRAY,"\u2502"),(DGRAY,"\u2593\u2593"),(WHITE,"\u2502"),(DGRAY,"\u2502"),(LGRAY," \u2502"),(DGRAY,"\u2593\u2593"),(WHITE,"\u2502"),(DGRAY,"\u2502"),(LGRAY,"\u2502"),(DGRAY,"\u2593\u2593"),(WHITE,"\u2502"),(DGRAY,"\u2502"),(LGRAY,"   \u2502"),(DGRAY,"\u2593\u2593"),(WHITE,"\u2502"),(DGRAY,"\u2502"),(LGRAY,"    \u2502"),(DGRAY,"\u2593\u2593"),(WHITE,"\u2514"),(LGRAY,"\u2500\u2518"),(DGRAY,"\u2593\u2593"),(WHITE,"\u2502"),(DGRAY,"\u2502")],
 [(LGRAY,"\u2502\u2591\u2591"),(WHITE,"\u2502"),(DGRAY,"\u2502"),(LGRAY,"\u2502\u2591\u2591"),(WHITE,"\u2502"),(DGRAY,"\u2502"),(LGRAY," \u2502\u2591\u2591"),(WHITE,"\u2514\u2500"),(LGRAY,"\u2518\u2591\u2591"),(WHITE,"\u2502"),(DGRAY,"\u2502"),(LGRAY,"   \u2502\u2591\u2591"),(WHITE,"\u2502"),(DGRAY,"\u2502"),(LGRAY,"    \u2502\u2591\u2591\u2591\u2591\u2591\u2591\u2591"),(WHITE,"\u2502"),(DGRAY,"\u2502")],
 [(LGRAY,"\u2502"),(DGRAY,"\u2592\u2592"),(WHITE,"\u2502"),(DGRAY,"\u2502"),(LGRAY,"\u2502"),(DGRAY,"\u2592\u2592"),(WHITE,"\u2502"),(DGRAY,"\u2502"),(LGRAY," \u2514\u2500\u2510"),(DGRAY,"\u2592\u2592\u2592"),(WHITE,"\u250c"),(LGRAY,"\u2500"),(WHITE,"\u2518"),(LGRAY,"    \u2502"),(DGRAY,"\u2592\u2592"),(WHITE,"\u2502"),(DGRAY,"\u2502"),(LGRAY,"    \u2502"),(DGRAY,"\u2592\u2592"),(WHITE,"\u250c"),(LGRAY,"\u2500\u2510"),(DGRAY,"\u2592\u2592"),(WHITE,"\u2502"),(DGRAY,"\u2502")],
 [(LGRAY,"\u2514\u2500\u2500"),(WHITE,"\u2518"),(DGRAY,"\u2514"),(LGRAY,"\u2514\u2500\u2500"),(WHITE,"\u2518"),(DGRAY,"\u2514"),(LGRAY,"   \u2514\u2500\u2500\u2500"),(WHITE,"\u2518"),(DGRAY,"\u2514"),(LGRAY,"     \u2514\u2500\u2500"),(WHITE,"\u2518"),(DGRAY,"\u2514"),(LGRAY,"    \u2514\u2500\u2500"),(WHITE,"\u2518"),(DGRAY,"\u2514"),(LGRAY,"\u2514\u2500"),(WHITE,"\u2500\u2518"),(DGRAY,"\u2514")],
    ]


def clear():
    sys.stdout.write("\033[2J\033[H"); sys.stdout.flush()


def logo():
    for line in _build_logo():
        print("".join(c + t for c, t in line) + RESET)


def launch_animation():
    if not STATE["animations"] or not _supports_color():
        logo(); return
    prepared = []
    for line in _build_logo():
        chars = []
        for color, text in line:
            for ch in text: chars.append((color, ch))
        prepared.append(chars)
    n_lines = len(prepared)
    max_width = max((len(c) for c in prepared), default=80)
    term_w = shutil.get_terminal_size((100, 30)).columns
    if term_w < max_width + 4:
        logo(); return
    HIDE = "\033[?25l"; SHOW = "\033[?25h"
    dim = "\033[38;5;238m"
    rainbow = [RED, "\033[33m", YELLOW, GREEN, CYAN, BLUE, MAGENTA]
    n_colors = len(rainbow)
    sys.stdout.write(HIDE); sys.stdout.flush()
    try:
        frames = 22; delay = 0.026; sweep_half = 7
        for frame in range(frames + 1):
            if frame > 0: sys.stdout.write(f"\033[{n_lines}A")
            t = frame / frames
            sweep_pos = -sweep_half + t * (max_width + 2 * sweep_half)
            for chars in prepared:
                buf = []; prev = None
                for col, (target, ch) in enumerate(chars):
                    if ch == " ": buf.append(ch); continue
                    dist = abs(col - sweep_pos)
                    if dist <= sweep_half:
                        c = rainbow[int(col * 1.6 + frame * 0.9) % n_colors]
                    elif col < sweep_pos: c = target
                    else: c = dim
                    if c != prev: buf.append(c); prev = c
                    buf.append(ch)
                buf.append(RESET)
                sys.stdout.write("".join(buf) + "\n")
            sys.stdout.flush(); time.sleep(delay)
    finally:
        sys.stdout.write(SHOW); sys.stdout.flush()


def wordmark_pulse():
    tail = DGRAY + "\u2022 plain-text notebooks \u2022 Python backend" + RESET
    if not STATE["animations"] or not _supports_color():
        print(f"  {BLUE}Nota{RESET} {tail}"); return
    for c in [BLUE, WHITE, BLUE, WHITE, BLUE]:
        sys.stdout.write(f"\r  {c}Nota{RESET} {tail}")
        sys.stdout.flush(); time.sleep(0.06)
    print()


def divider():
    width = min(max(shutil.get_terminal_size((100, 30)).columns - 4, 30), 90)
    color = {"on": GREEN, "auto": BLUE, "off": DGRAY}.get(STATE["rainbow"], BLUE)
    print("  " + color + "\u2500" * width + RESET)


def header(animate=True):
    clear()
    if animate: launch_animation()
    else: logo()
    print(); wordmark_pulse(); print(); divider()
    print(f"  {DGRAY}COMMANDS{RESET}")
    print(f"  {BLUE}:help{RESET}      this menu")
    print(f"  {BLUE}:load{RESET}      load a .nota file")
    print(f"  {BLUE}:run{RESET}       re-run the last file")
    print(f"  {BLUE}:settings{RESET}  theme, animation, precision")
    print(f"  {BLUE}:clear{RESET}     redraw")
    print(f"  {BLUE}:exit{RESET}      quit")
    print()
    print(f"  {DGRAY}Any other input runs as a Python expression.{RESET}")
    print(); divider()


def first_run_intro():
    clear()
    for line in _build_logo():
        print("".join(c + t for c, t in line) + RESET)
        time.sleep(0.04)
    time.sleep(0.15); print()
    user = os.environ.get("USER") or os.environ.get("LOGNAME") or "friend"
    if user.startswith("u0_a"): user = "friend"
    print(f"  {BLUE}Nota{RESET} {DGRAY}\u2022 welcome, {user}{RESET}"); time.sleep(0.3)
    print(f"  {DGRAY}Run a notebook:{RESET} {WHITE}nota file.nota{RESET}")
    print(f"  {DGRAY}Or type {WHITE}:help{RESET}{DGRAY} for the REPL.{RESET}")
    print()
    try: input(f"  {DGRAY}Press Enter to continue\u2026{RESET}")
    except (EOFError, KeyboardInterrupt): pass
    mark_seen()


# ============================================================
# .nota PARSER
# ============================================================
CELL_RE = re.compile(r"^```([A-Za-z0-9_+\-]*)[ \t]*\n(.*?)^```[ \t]*$",
                     re.MULTILINE | re.DOTALL)


def parse_nota(text):
    blocks = []; pos = 0; line = 1
    for m in CELL_RE.finditer(text):
        if m.start() > pos:
            prose = text[pos:m.start()]
            if prose.strip(): blocks.append(("prose", prose, line))
            line += prose.count("\n")
        lang = (m.group(1) or "python").lower()
        body = m.group(2)
        kind = "plot" if lang in ("plot", "nota-plot") else "python"
        blocks.append((kind, body, line))
        line += body.count("\n") + 2
        pos = m.end()
    if pos < len(text):
        tail = text[pos:]
        if tail.strip(): blocks.append(("prose", tail, line))
    return blocks


# ============================================================
# PLOT API
# ============================================================
PLOT_QUEUE = []
PLOT_META = {"title": None, "xlabel": None, "ylabel": None, "xlim": None, "ylim": None}


def reset_plot():
    PLOT_QUEUE.clear()
    for k in PLOT_META: PLOT_META[k] = None


def linspace(a, b, n=200):
    if n < 2: return [float(a)]
    step = (b - a) / (n - 1)
    return [a + i * step for i in range(n)]


def arange(a, b, step=1):
    if step == 0: raise ValueError("arange step must be non-zero")
    out = []; v = a
    if step > 0:
        while v < b: out.append(v); v += step
    else:
        while v > b: out.append(v); v += step
    return out


def _vec(fn):
    def wrapped(x):
        if isinstance(x, (list, tuple)): return [wrapped(v) for v in x]
        return fn(x)
    return wrapped


sin  = _vec(math.sin);  cos  = _vec(math.cos);  tan  = _vec(math.tan)
sqrt = _vec(math.sqrt); exp  = _vec(math.exp);  log  = _vec(math.log)
ln   = _vec(math.log);  abs_ = _vec(abs)


def plot(x, y=None, label=""):
    if y is None: y = list(x); x = list(range(len(y)))
    else: x = list(x); y = list(y)
    if len(x) != len(y): raise ValueError("plot: x and y must have the same length")
    PLOT_QUEUE.append({"kind": "line", "x": x, "y": y, "label": label})


def scatter(x, y=None, label=""):
    if y is None: y = list(x); x = list(range(len(y)))
    else: x = list(x); y = list(y)
    if len(x) != len(y): raise ValueError("scatter: x and y must have the same length")
    PLOT_QUEUE.append({"kind": "scatter", "x": x, "y": y, "label": label})


def set_title(s):  PLOT_META["title"] = s
def xlabel(s):     PLOT_META["xlabel"] = s
def ylabel(s):     PLOT_META["ylabel"] = s
def xlim(a, b):    PLOT_META["xlim"] = (a, b)
def ylim(a, b):    PLOT_META["ylim"] = (a, b)


# ============================================================
# ASCII PLOT
# ============================================================
def _finite(v):
    try: return math.isfinite(float(v))
    except Exception: return False


def _auto_yrange(ys):
    ys = sorted(y for y in ys if _finite(y))
    if not ys: return -1.0, 1.0
    n = len(ys); q1 = ys[n // 4]; q3 = ys[(3 * n) // 4]
    iqr = q3 - q1
    if iqr == 0: lo, hi = ys[0], ys[-1]
    else: lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    inl = [y for y in ys if lo <= y <= hi] or ys
    ymin, ymax = min(inl), max(inl)
    if ymax - ymin < 1e-12: ymax = ymin + 1.0; ymin -= 1.0
    return ymin, ymax


def render_ascii_plot(width=None, height=16):
    if not PLOT_QUEUE: return None
    if width is None:
        width = min(80, max(40, shutil.get_terminal_size((100, 30)).columns - 12))
    markers = ["\u25cf", "\u25c6", "\u25a0", "\u25b2", "\u25bc", "\u2605", "\u271a"]
    xs_all = [x for s in PLOT_QUEUE for x in s["x"]]
    ys_all = [y for s in PLOT_QUEUE for y in s["y"]]
    if not xs_all or not ys_all: return None
    if PLOT_META["xlim"]: xmin, xmax = PLOT_META["xlim"]
    else: xmin, xmax = min(xs_all), max(xs_all)
    if PLOT_META["ylim"]: ymin, ymax = PLOT_META["ylim"]
    else: ymin, ymax = _auto_yrange(ys_all)
    if xmax <= xmin: xmax = xmin + 1.0
    if ymax <= ymin: ymax = ymin + 1.0
    pad = (ymax - ymin) * 0.05
    ymin -= pad; ymax += pad
    grid = [[" "] * width for _ in range(height)]
    if ymin <= 0 <= ymax:
        y0 = max(0, min(height - 1, height - 1 - int((0 - ymin) / (ymax - ymin) * (height - 1))))
        for c in range(width): grid[y0][c] = "\u2500"
    if xmin <= 0 <= xmax:
        x0 = int((0 - xmin) / (xmax - xmin) * (width - 1))
        for r in range(height): grid[r][x0] = "\u2502"
    for si, s in enumerate(PLOT_QUEUE):
        marker = markers[si % len(markers)]
        for x, y in zip(s["x"], s["y"]):
            if not (_finite(x) and _finite(y)): continue
            if y < ymin or y > ymax: continue
            col = max(0, min(width - 1, int((x - xmin) / (xmax - xmin) * (width - 1))))
            row = max(0, min(height - 1, height - 1 - int((y - ymin) / (ymax - ymin) * (height - 1))))
            cur = grid[row][col]
            if cur == " " or cur in "\u2500\u2502": grid[row][col] = marker
            elif cur != marker: grid[row][col] = "\u2573"
    out = []
    if PLOT_META["title"]: out.append(f"  {WHITE}{PLOT_META['title']}{RESET}")
    label_w = 10
    for r in range(height):
        y_val = ymax - (ymax - ymin) * r / (height - 1)
        out.append(f"  {DGRAY}{y_val:>{label_w}.4g} \u2502{RESET} " + "".join(grid[r]))
    out.append(f"  {' ' * label_w} \u2514" + "\u2500" * (width + 2))
    xl = f"{xmin:<10.4g}{(' ' * max(0, width - 20))}{xmax:>10.4g}"
    out.append(f"  {' ' * (label_w + 2)}{xl}")
    if PLOT_META["xlabel"]: out.append(f"  {DGRAY}{' ' * (label_w + 2)}{PLOT_META['xlabel']}{RESET}")
    legend = []
    for si, s in enumerate(PLOT_QUEUE):
        if s.get("label"): legend.append(f"{markers[si % len(markers)]} {s['label']}")
    if legend: out.append(f"  {DGRAY}  " + "   ".join(legend) + RESET)
    return out


def print_ascii_plot():
    lines = render_ascii_plot()
    if not lines: return
    print()
    for ln in lines: print(ln)
    print()


# ============================================================
# SVG PLOT
# ============================================================
def _default_svg_dir():
    for cand in ("/sdcard/Download/Nota", "/storage/emulated/0/Download/Nota"):
        try:
            os.makedirs(cand, exist_ok=True)
            probe = os.path.join(cand, ".nota_probe")
            open(probe, "w").close(); os.remove(probe)
            return cand
        except (OSError, PermissionError): continue
    return os.path.expanduser("~/Downloads/Nota")


SVG_DIR = _default_svg_dir()


def _nice_ticks(lo, hi, count=8):
    rng = hi - lo
    if rng <= 0: return [lo]
    raw = rng / count
    mag = 10 ** math.floor(math.log10(raw))
    step = mag
    for m in (1, 2, 5, 10):
        if rng / (m * mag) <= count * 1.5: step = m * mag; break
    start = math.ceil(lo / step) * step
    out = []; t = start
    while t <= hi + step * 1e-6:
        out.append(round(t, 12)); t += step
    return out


def render_svg_plot(path):
    if not PLOT_QUEUE: return None
    W, H = 900, 600
    ML, MR, MT, MB = 80, 40, 60, 70
    plot_w = W - ML - MR; plot_h = H - MT - MB
    colors = ["#e74c3c", "#3498db", "#2ecc71", "#9b59b6", "#f39c12", "#1abc9c", "#34495e", "#e67e22"]
    xs_all = [x for s in PLOT_QUEUE for x in s["x"]]
    ys_all = [y for s in PLOT_QUEUE for y in s["y"]]
    if not xs_all or not ys_all: return None
    if PLOT_META["xlim"]: xmin, xmax = PLOT_META["xlim"]
    else: xmin, xmax = min(xs_all), max(xs_all)
    if PLOT_META["ylim"]: ymin, ymax = PLOT_META["ylim"]
    else: ymin, ymax = _auto_yrange(ys_all)
    if xmax <= xmin: xmax = xmin + 1
    if ymax <= ymin: ymax = ymin + 1
    def xpx(x): return ML + (x - xmin) / (xmax - xmin) * plot_w
    def ypx(y): return MT + (1 - (y - ymin) / (ymax - ymin)) * plot_h
    xticks = _nice_ticks(xmin, xmax); yticks = _nice_ticks(ymin, ymax)
    L = []
    L.append('<?xml version="1.0" encoding="UTF-8"?>')
    L.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    L.append(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
    if PLOT_META["title"]:
        L.append(f'<text x="{W//2}" y="30" text-anchor="middle" font-family="Georgia,serif" font-size="20" fill="#2c3e50">{PLOT_META["title"]}</text>')
    for xt in xticks:
        px = xpx(xt)
        L.append(f'<line x1="{px:.2f}" y1="{MT}" x2="{px:.2f}" y2="{MT+plot_h}" stroke="#ecf0f1"/>')
    for yt in yticks:
        py = ypx(yt)
        L.append(f'<line x1="{ML}" y1="{py:.2f}" x2="{ML+plot_w}" y2="{py:.2f}" stroke="#ecf0f1"/>')
    if ymin <= 0 <= ymax:
        py0 = ypx(0)
        L.append(f'<line x1="{ML}" y1="{py0:.2f}" x2="{ML+plot_w}" y2="{py0:.2f}" stroke="#2c3e50" stroke-width="1.5"/>')
    if xmin <= 0 <= xmax:
        px0 = xpx(0)
        L.append(f'<line x1="{px0:.2f}" y1="{MT}" x2="{px0:.2f}" y2="{MT+plot_h}" stroke="#2c3e50" stroke-width="1.5"/>')
    L.append(f'<rect x="{ML}" y="{MT}" width="{plot_w}" height="{plot_h}" fill="none" stroke="#bdc3c7"/>')
    for xt in xticks:
        px = xpx(xt)
        L.append(f'<text x="{px:.2f}" y="{MT+plot_h+20}" text-anchor="middle" font-family="Menlo,monospace" font-size="11" fill="#2c3e50">{xt:g}</text>')
    for yt in yticks:
        py = ypx(yt)
        L.append(f'<text x="{ML-10}" y="{py+4:.2f}" text-anchor="end" font-family="Menlo,monospace" font-size="11" fill="#2c3e50">{yt:g}</text>')
    for si, s in enumerate(PLOT_QUEUE):
        color = colors[si % len(colors)]
        pts = [(xpx(x), ypx(y)) for x, y in zip(s["x"], s["y"]) if _finite(x) and _finite(y) and ymin <= y <= ymax]
        if s["kind"] == "line" and len(pts) >= 2:
            d = "M " + " L ".join(f"{a:.2f} {b:.2f}" for a, b in pts)
            L.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round"/>')
        elif s["kind"] == "scatter":
            for a, b in pts:
                L.append(f'<circle cx="{a:.2f}" cy="{b:.2f}" r="3" fill="{color}"/>')
    if PLOT_META["xlabel"]:
        L.append(f'<text x="{ML+plot_w/2}" y="{H-15}" text-anchor="middle" font-family="Menlo,monospace" font-size="12" fill="#2c3e50">{PLOT_META["xlabel"]}</text>')
    if PLOT_META["ylabel"]:
        L.append(f'<text x="20" y="{MT+plot_h/2}" text-anchor="middle" font-family="Menlo,monospace" font-size="12" fill="#2c3e50" transform="rotate(-90 20 {MT+plot_h/2})">{PLOT_META["ylabel"]}</text>')
    lx, ly = ML + 12, MT + 15
    for si, s in enumerate(PLOT_QUEUE):
        if not s.get("label"): continue
        color = colors[si % len(colors)]
        L.append(f'<rect x="{lx}" y="{ly-9}" width="16" height="11" fill="{color}"/>')
        L.append(f'<text x="{lx+22}" y="{ly}" font-family="Menlo,monospace" font-size="12" fill="#2c3e50">{s["label"]}</text>')
        ly += 20
    L.append('</svg>')
    with open(path, "w") as f: f.write("\n".join(L))
    return os.path.abspath(path)


# ============================================================
# MARKDOWN-LITE PROSE RENDERER
# ============================================================
HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITAL_RE = re.compile(r"(?<!\*)\*([^*\n]+?)\*(?!\*)")
CODE_RE = re.compile(r"`([^`\n]+)`")
BULLET_RE = re.compile(r"^(\s*)[-*]\s+(.*)$")
NUM_RE = re.compile(r"^(\s*)(\d+)\.\s+(.*)$")
QUOTE_RE = re.compile(r"^>\s?(.*)$")
HR_RE = re.compile(r"^\s*-{3,}\s*$")


def _inline(s):
    s = BOLD_RE.sub(lambda m: f"{WHITE}{m.group(1)}{RESET}", s)
    s = ITAL_RE.sub(lambda m: f"{LGRAY}{m.group(1)}{RESET}", s)
    s = CODE_RE.sub(lambda m: f"{CYAN}{m.group(1)}{RESET}", s)
    return s


def render_prose(text):
    for line in text.splitlines():
        if HR_RE.match(line): divider(); continue
        m = HEAD_RE.match(line)
        if m:
            level = len(m.group(1)); title = _inline(m.group(2))
            if level == 1: print(); print(f"  {BLUE}{title}{RESET}"); print()
            elif level == 2: print(); print(f"  {WHITE}{title}{RESET}")
            else: print(f"  {LGRAY}{title}{RESET}")
            continue
        m = QUOTE_RE.match(line)
        if m: print(f"  {DGRAY}\u2502 {LGRAY}{_inline(m.group(1))}{RESET}"); continue
        m = BULLET_RE.match(line)
        if m: print(f"  {' ' * len(m.group(1))}{BLUE}\u2022{RESET} {_inline(m.group(2))}"); continue
        m = NUM_RE.match(line)
        if m: print(f"  {' ' * len(m.group(1))}{BLUE}{m.group(2)}.{RESET} {_inline(m.group(3))}"); continue
        if line.strip() == "": print(); continue
        print(f"  {_inline(line)}")


# ============================================================
# CELL EXECUTION
# ============================================================
def make_namespace():
    import builtins
    ns = {"__name__": "__nota__", "__builtins__": builtins}
    ns.update({
        "linspace": linspace, "arange": arange,
        "sin": sin, "cos": cos, "tan": tan,
        "sqrt": sqrt, "exp": exp, "log": log, "ln": ln, "abs": abs_,
        "pi": math.pi, "e": math.e, "tau": 2 * math.pi,
        "plot": plot, "scatter": scatter,
        "title": set_title, "xlabel": xlabel, "ylabel": ylabel,
        "xlim": xlim, "ylim": ylim,
    })
    return ns


def exec_cell(code, ns, filename="<cell>"):
    tree = ast.parse(code, filename=filename, mode="exec")
    if not tree.body: return None
    last = tree.body[-1]
    if isinstance(last, ast.Expr):
        if len(tree.body) > 1:
            head = ast.Module(body=tree.body[:-1], type_ignores=[])
            exec(compile(head, filename, "exec"), ns)
        return eval(compile(ast.Expression(last.value), filename, "eval"), ns)
    exec(compile(tree, filename, "exec"), ns)
    return None


def _show_value(v):
    if v is None: return
    try:
        from reprlib import repr as _r
        print(f"  {DGRAY}\u2192{RESET} {WHITE}{_r(v)}{RESET}")
    except Exception:
        print(f"  {DGRAY}\u2192{RESET} {WHITE}{v!r}{RESET}")


def run_python_cell(code, ns, start_line=1):
    try:
        v = exec_cell(code, ns)
        _show_value(v)
    except Exception as e:
        print(f"  {RED}\u2715{RESET} line {start_line}: {type(e).__name__}: {e}")


def run_plot_cell(code, ns, start_line=1, svg=False):
    reset_plot()
    try:
        v = exec_cell(code, ns)
        _show_value(v)
    except Exception as e:
        print(f"  {RED}\u2715{RESET} line {start_line}: {type(e).__name__}: {e}")
        return
    if not PLOT_QUEUE: return
    print_ascii_plot()
    if svg:
        os.makedirs(SVG_DIR, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.join(SVG_DIR, f"plot_{ts}_{start_line}.svg")
        try:
            out = render_svg_plot(path)
            if out:
                print(f"  {GREEN}\u2713{RESET} {DGRAY}svg \u2192{RESET} {WHITE}{out}{RESET}")
                print()
        except Exception as e:
            print(f"  {RED}\u2715{RESET} svg: {e}")


def run_file(path, svg=False, quiet=False, animate=True):
    with open(path) as f: text = f.read()
    if not quiet:
        header(animate=animate)
        print(f"  {DGRAY}running {WHITE}{path}{RESET}")
        print()
    ns = make_namespace()
    for kind, content, start in parse_nota(text):
        if kind == "prose":
            if not quiet: render_prose(content)
        elif kind == "python":
            run_python_cell(content, ns, start)
        elif kind == "plot":
            run_plot_cell(content, ns, start, svg=svg)
    if not quiet:
        print(); divider()


# ============================================================
# REPL
# ============================================================
def run_repl():
    header(animate=True)
    ns = make_namespace(); last_file = None
    while True:
        print()
        try: line = input(prompt_main())
        except (EOFError, KeyboardInterrupt): _shutdown(); return
        s = line.strip()
        if not s: continue
        if s.startswith(":"):
            parts = s[1:].strip().split(maxsplit=1)
            head = parts[0].lower() if parts else ""
            arg = parts[1] if len(parts) > 1 else ""
            if head in ("exit", "quit", "q"): _shutdown(); return
            if head == "help":   header(animate=False); continue
            if head == "clear":  header(animate=False); continue
            if head == "settings": settings_menu(); header(animate=False); continue
            if head == "load":
                p = os.path.expanduser(arg.strip())
                if not os.path.exists(p):
                    print(f"  {RED}\u2715{RESET} no such file: {p}"); continue
                last_file = p
                try: run_file(p, svg=False, quiet=False, animate=False)
                except Exception as e: print(f"  {RED}\u2715{RESET} {e}")
                ns = make_namespace()
                continue
            if head == "run":
                if not last_file:
                    print(f"  {RED}\u2715{RESET} nothing to run; use :load FILE"); continue
                try: run_file(last_file, svg=False, quiet=False, animate=False)
                except Exception as e: print(f"  {RED}\u2715{RESET} {e}")
                continue
            print(f"  {RED}\u2715{RESET} unknown command: :{head}")
            continue
        reset_plot()
        try:
            v = exec_cell(s, ns)
            _show_value(v)
        except Exception as e:
            print(f"  {RED}\u2715{RESET} {type(e).__name__}: {e}")
        if PLOT_QUEUE: print_ascii_plot()


# ============================================================
# SETTINGS
# ============================================================
def settings_menu():
    while True:
        clear(); logo(); print()
        print(f"  {BLUE}SETTINGS{RESET}"); divider()
        def row(k, label, val):
            print(f"  {WHITE}[{k:>2}]{RESET} {label:<22} {DGRAY}[{val}]{RESET}")
        row(1, "Theme",            STATE["theme"])
        row(2, "Rainbow",          STATE["rainbow"])
        row(3, "Launch animation", "on" if STATE["animations"] else "off")
        row(4, "Precision",        STATE["precision"])
        row(5, "Reset settings",   "\u2014")
        print(f"  {WHITE}[ b]{RESET} Back")
        divider()
        try: choice = input(prompt_choice()).strip().lower()
        except (EOFError, KeyboardInterrupt): save_config(); return
        if choice in ("", "b", "q"): save_config(); return
        if choice == "1":
            order = ["default","dark","mono","none"]
            STATE["theme"] = order[(order.index(STATE["theme"]) + 1) % 4]
            apply_theme()
        elif choice == "2":
            order = ["auto","on","off"]
            STATE["rainbow"] = order[(order.index(STATE["rainbow"]) + 1) % 3]
        elif choice == "3": STATE["animations"] = not STATE["animations"]
        elif choice == "4":
            order = [3, 4, 6, 8, 10, 12]
            try:
                i = order.index(STATE["precision"])
                STATE["precision"] = order[(i + 1) % len(order)]
            except ValueError: STATE["precision"] = 6
        elif choice == "5":
            STATE.update({"theme":"default","rainbow":"auto","animations":True,"precision":6})
            apply_theme()
        save_config()


# ============================================================
# MAIN
# ============================================================
def _shutdown():
    try: print()
    except Exception: pass
    try: print(f"\n  {DGRAY}Goodbye.{RESET}")
    except Exception: pass
    try: save_config()
    except Exception: pass


def _enable_windows_vt():
    if sys.platform != "win32": return
    try:
        import ctypes
        k = ctypes.windll.kernel32
        k.SetConsoleMode(k.GetStdHandle(-11), 7)
    except Exception: pass


def _sigint_handler(sig, frame):
    print(); _shutdown(); sys.exit(0)


def main():
    import signal
    ap = argparse.ArgumentParser(prog="nota",
                                 description="Nota \u2014 plain-text notebooks for the terminal.")
    ap.add_argument("file", nargs="?", help=".nota file to run; omit for REPL")
    ap.add_argument("--svg", action="store_true", help="also export each plot as SVG")
    ap.add_argument("--quiet", action="store_true", help="hide prose, show only outputs")
    ap.add_argument("--check", action="store_true", help="parse only, don't execute")
    ap.add_argument("--no-anim", action="store_true", help="skip launch animation")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()

    load_config()
    _enable_windows_vt()
    if args.no_color: os.environ["NOTA_NO_COLOR"] = "1"
    _strip_ansi_if_needed()
    apply_theme()
    try: signal.signal(signal.SIGINT, _sigint_handler)
    except Exception: pass

    if is_first_run(): first_run_intro()

    if not args.file:
        run_repl(); return

    p = os.path.expanduser(args.file)
    if not os.path.exists(p):
        print(f"  {RED}\u2715{RESET} file not found: {p}"); sys.exit(1)

    with open(p) as f: text = f.read()

    if args.check:
        try:
            blocks = parse_nota(text)
            n_py = sum(1 for k,_,_ in blocks if k == "python")
            n_pl = sum(1 for k,_,_ in blocks if k == "plot")
            n_pr = sum(1 for k,_,_ in blocks if k == "prose")
            print(f"  {GREEN}\u2713{RESET} {p}")
            print(f"  {DGRAY}blocks: {len(blocks)} ({n_pr} prose, {n_py} python, {n_pl} plot){RESET}")
        except Exception as e:
            print(f"  {RED}\u2715{RESET} {e}"); sys.exit(1)
        return

    run_file(p, svg=args.svg, quiet=args.quiet, animate=not args.no_anim)


if __name__ == "__main__":
    main()
