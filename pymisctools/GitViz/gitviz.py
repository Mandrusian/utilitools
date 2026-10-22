#!/usr/bin/env python3
"""GitViz — render git history as an ASCII / SVG branch graph."""

import argparse
import math
import os
import re
import shutil
import subprocess
import sys
import time


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

LANE_COLORS = [CYAN, GREEN, YELLOW, MAGENTA, BLUE, RED, LGRAY, WHITE]


def _supports_color():
    if os.environ.get("NO_COLOR"): return False
    if os.environ.get("GITVIZ_NO_COLOR"): return False
    if os.environ.get("GITVIZ_FORCE_COLOR"): return True
    if not sys.stdout.isatty(): return False
    return True


def _strip_color():
    global RESET, LGRAY, DGRAY, BLUE, DBLUE, WHITE, CYAN, GREEN, YELLOW, RED, MAGENTA
    RESET = LGRAY = DGRAY = BLUE = DBLUE = WHITE = CYAN = GREEN = YELLOW = RED = MAGENTA = ""
    global LANE_COLORS
    LANE_COLORS = [""] * 8


def lane_color(i): return LANE_COLORS[i % len(LANE_COLORS)]


# ============================================================
# LOGO
# ============================================================
def _build_logo():
    E = chr(27)
    return [
        f"{E}[0;37;40m                                                    {E}[0;94;40m\u2584{E}[0;37;40m\u2584       {E}[0m",
        f"{E}[0;37;40m  {E}[0;94;40m\u2584\u2584\u2584\u2584\u2584{E}[0;37;40m\u2584    {E}[0;94;40m\u2584\u2588\u2588{E}[0;94;47m\u2584{E}[0;37;40m\u2584 {E}[0;34;40m\u2584{E}[0;94;40m\u2584\u2584\u2584\u2584\u2584\u2584\u2584\u2584\u2584\u2584\u2584{E}[0;37;40m\u2584   {E}[0;94;40m\u2584{E}[0;37;40m\u2584  {E}[0;94;40m\u2584{E}[0;37;40m\u2584    {E}[0;94;40m\u2584\u2588\u2588{E}[0;94;47m\u2584{E}[0;37;40m\u2584  {E}[0;94;40m\u2588\u2588\u2588{E}[0;94;47m\u2584{E}[0;37;40m\u2584\u2584\u2584\u2584  {E}[0m",
        f"{E}[0;94;40m\u2584\u2588{E}[0;94;44m\u2593\u2593{E}[0;94;47m\u2580{E}[0;94;40m\u2580\u2580\u2588{E}[0;94;47m\u2584{E}[0;37;40m\u2584  {E}[0;94;40m\u2580\u2588{E}[0;94;44m\u2593{E}[0;94;47m\u2580{E}[0;37;40m\u2580 {E}[0;94;44m\u2591\u2592{E}[0;94;40m\u2580\u2588\u2588{E}[0;94;44m\u2593\u2593{E}[0;94;47m\u2580{E}[0;94;40m\u2580\u2580\u2588\u2588{E}[0;37;40m\u2588 {E}[0;94;40m\u2584\u2588{E}[0;94;44m\u2593{E}[0;37;40m\u2588  {E}[0;94;44m\u2593{E}[0;94;40m\u2588{E}[0;94;47m\u2584{E}[0;37;40m\u2584  {E}[0;94;40m\u2580\u2588{E}[0;94;44m\u2593{E}[0;94;47m\u2580{E}[0;37;40m\u2580  {E}[0;94;40m\u2590\u2588\u2588{E}[0;94;47m\u2580{E}[0;94;40m\u2580\u2588\u2588\u2588{E}[0;94;47m\u2584{E}[0;37;40m\u2584{E}[0m",
        f"{E}[0;94;40m\u2588{E}[0;94;44m\u2593\u2592{E}[0;37;40m\u2588    {E}[0;94;40m\u2580{E}[0;37;40m\u2580           {E}[0;94;40m\u2588{E}[0;94;44m\u2593\u2592{E}[0;37;40m\u2588    {E}[0;94;40m\u2580{E}[0;37;40m\u2580 {E}[0;94;40m\u2588{E}[0;94;44m\u2593\u2592{E}[0;37;40m\u2588   {E}[0;94;44m\u2591\u2592{E}[0;94;47m\u2584{E}[0;37;40m\u2584         {E}[0;94;40m\u2584\u2584\u2584\u2584\u2584\u2588\u2588{E}[0;94;47m\u2580{E}[0;37;40m\u2580{E}[0m",
        f"{E}[0;94;44m\u2593\u2592\u2591{E}[0;37;40m\u2588 {E}[0;94;44m\u2591\u2591\u2592\u2593{E}[0;94;47m\u258c{E}[0;37;40m\u258c    {E}[0;34;40m\u2584{E}[0;37;40m\u2584    {E}[0;94;44m\u2593\u2592\u2591{E}[0;37;40m\u2588       {E}[0;94;44m\u2593\u2592\u2591{E}[0;37;40m\u2588   {E}[0;34;40m\u2591{E}[0;94;44m\u2591\u2593{E}[0;37;40m\u2588    {E}[0;34;40m\u2584{E}[0;37;40m\u2584 {E}[0;94;40m\u2590{E}[0;94;44m\u2593\u2593{E}[0;94;47m\u2580{E}[0;37;40m\u2580\u2580\u2580\u2580\u2580  {E}[0m",
        f"{E}[0;94;44m\u2592\u2591{E}[0;34;40m\u2588{E}[0;37;40m\u2588   {E}[0;94;44m\u2591\u2592{E}[0;37;40m\u2588   {E}[0;34;40m\u2584\u2588\u2588{E}[0;37;40m\u2588    {E}[0;94;44m\u2592\u2591{E}[0;34;40m\u2588{E}[0;37;40m\u2588       {E}[0;94;44m\u2592\u2591{E}[0;34;40m\u2588{E}[0;37;40m\u2588   {E}[0;34;40m\u2593{E}[0;94;44m\u2592\u2593{E}[0;37;40m\u2588  {E}[0;34;40m\u2584\u2588\u2588{E}[0;37;40m\u2588 {E}[0;94;40m\u2588{E}[0;94;44m\u2592\u2591{E}[0;37;40m\u2588       {E}[0m",
        f"{E}[0;94;44m\u2591{E}[0;34;40m\u2588\u2588{E}[0;37;44m\u2580{E}[0;37;40m\u2584  {E}[0;94;44m\u2591\u2591{E}[0;37;40m\u2588   {E}[0;34;40m\u2588\u2588{E}[0;37;44m\u2590{E}[0;37;40m\u258c    {E}[0;94;44m\u2591{E}[0;34;40m\u2588\u2588{E}[0;37;40m\u2588       {E}[0;94;44m\u2591{E}[0;34;40m\u2588\u2588{E}[0;94;44m\u2580\u2584\u2584\u2580\u2591\u2591{E}[0;37;40m\u2588   {E}[0;34;40m\u2588\u2588{E}[0;37;44m\u2590{E}[0;37;40m\u258c  {E}[0;94;40m\u2593{E}[0;94;44m\u2591\u2591{E}[0;37;44m\u2580{E}[0;37;40m\u2584\u2584\u2584\u2584{E}[0;37;44m\u2580{E}[0;37;40m\u2588{E}[0m",
        f"{E}[0;37;40m {E}[0;34;40m\u2580\u2588\u2588\u2588\u2588\u2588\u2588{E}[0;94;44m\u2591{E}[0;37;40m\u2588   {E}[0;34;40m\u2590\u2588{E}[0;37;40m\u2588     {E}[0;34;40m\u2580\u2588\u2588{E}[0;37;40m\u2588        {E}[0;34;40m\u2580\u2588\u2588\u2588\u2588\u2588{E}[0;37;44m\u2584{E}[0;37;40m\u2580    {E}[0;34;40m\u2590\u2588{E}[0;37;40m\u2588    {E}[0;94;40m\u2580\u2592{E}[0;94;44m\u2591{E}[0;34;40m\u2588\u2588\u2588\u2588\u2588{E}[0;37;40m\u2588{E}[0m",
        f"{E}[0;37;40m                       \u2580                                  {E}[0;34;40m\u2580\u2588{E}[0;37;40m\u2588{E}[0m",
    ]


def logo():
    for line in _build_logo():
        print(line)
    print()


def wordmark():
    print(f"  {BLUE}GitViz{RESET} {DGRAY}\u2022 branch graph renderer for git{RESET}")
    print()


def divider():
    width = min(max(shutil.get_terminal_size((100, 30)).columns - 4, 40), 100)
    print("  " + DGRAY + "\u2500" * width + RESET)


def header():
    print()
    logo()
    print()
    wordmark()
    divider()


# ============================================================
# GIT
# ============================================================
def run_git(args, cwd=None):
    r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, check=False)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def is_repo(path="."):
    r = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=path,
                       capture_output=True, text=True)
    return r.returncode == 0


def repo_root(path="."):
    return run_git(["rev-parse", "--show-toplevel"], cwd=path).strip()


def current_branch(path="."):
    try:
        return run_git(["symbolic-ref", "--short", "HEAD"], cwd=path).strip()
    except Exception:
        return "(detached)"


SEP = "\x1f"


def load_commits(path, ref="--all", limit=200):
    fmt = SEP.join(["%H", "%P", "%an", "%ar", "%D", "%s"])
    out = run_git(["log", ref, "--date-order", f"-n{limit}", f"--pretty=format:{fmt}"], cwd=path)
    commits = []
    for line in out.split("\n"):
        if not line.strip(): continue
        parts = line.split(SEP)
        if len(parts) < 6: continue
        h, parents, an, ar, refs, subj = parts[:6]
        commits.append({
            "hash": h,
            "parents": [p for p in parents.split() if p],
            "author": an,
            "when": ar,
            "refs": refs,
            "subject": subj,
        })
    return commits


# ============================================================
# LANE ASSIGNMENT
# ============================================================
def assign_lanes(commits):
    """Return list of dicts: {commit, lane, lanes_before, lanes_after}."""
    lanes = []
    rows = []
    for c in commits:
        h = c["hash"]
        if h in lanes:
            lane = lanes.index(h)
        else:
            if None in lanes:
                lane = lanes.index(None)
            else:
                lane = len(lanes)
                lanes.append(None)
        lanes_before = list(lanes)
        parents = c["parents"]
        if parents:
            lanes[lane] = parents[0]
            for p in parents[1:]:
                if p in lanes: continue
                if None in lanes:
                    lanes[lanes.index(None)] = p
                else:
                    lanes.append(p)
        else:
            lanes[lane] = None
        while lanes and lanes[-1] is None:
            lanes.pop()
        rows.append({"commit": c, "lane": lane, "before": lanes_before, "after": list(lanes)})
    return rows


# ============================================================
# ASCII RENDER
# ============================================================
def _short(h): return h[:7]


def render_ascii(commits, max_rows=None):
    if not commits:
        print(f"  {DGRAY}(no commits){RESET}"); return
    rows = assign_lanes(commits)
    max_lanes = max((max(len(r["before"]), r["lane"] + 1) for r in rows), default=1)
    lane_w = 2

    for r in rows:
        c = r["commit"]; lane = r["lane"]; before = r["before"]
        cells = []
        for i in range(max_lanes):
            active = i < len(before) and before[i] is not None
            if i == lane:
                marker = "\u25c9" if len(c["parents"]) > 1 else "\u25cf"
                cells.append(f"{lane_color(i)}{marker}{RESET} ")
            elif active:
                cells.append(f"{DGRAY}\u2502{RESET} ")
            else:
                cells.append("  ")
        prefix = "".join(cells)

        refs = ""
        if c["refs"]:
            refs = f"  {YELLOW}{c['refs']}{RESET}"
        suffix = f"  {DGRAY}{_short(c['hash'])}{RESET}  {WHITE}{c['subject']}{RESET}{refs}"
        meta = f"  {DGRAY}{c['author']}, {c['when']}{RESET}"
        print(f"  {prefix}{suffix}{meta}")

    print()
    print(f"  {DGRAY}{len(rows)} commit(s), up to {max_lanes} lanes{RESET}")


# ============================================================
# SVG RENDER
# ============================================================
def _default_svg_dir():
    for cand in ("/sdcard/Download/GitViz", "/storage/emulated/0/Download/GitViz"):
        try:
            os.makedirs(cand, exist_ok=True)
            probe = os.path.join(cand, ".gitviz_probe")
            open(probe, "w").close(); os.remove(probe)
            return cand
        except (OSError, PermissionError): continue
    return os.path.expanduser("~/Downloads/GitViz")


SVG_DIR = _default_svg_dir()
SVG_LANE_COLORS = ["#1abc9c", "#2ecc71", "#f1c40f", "#9b59b6", "#3498db",
                   "#e74c3c", "#95a5a6", "#ecf0f1"]


def render_svg(commits, path, title=None):
    if not commits: raise ValueError("no commits to render")
    rows = assign_lanes(commits)
    max_lanes = max((max(len(r["before"]), r["lane"] + 1) for r in rows), default=1)

    ROW_H = 28
    LANE_W = 26
    LEFT = 40
    TOP  = 60
    TEXT_PAD = 20

    subject_max_chars = max((len(c["subject"]) for c in commits), default=0)
    text_w = min(720, 12 * (subject_max_chars + 12))
    W = LEFT + max_lanes * LANE_W + TEXT_PAD + text_w + 40
    H = TOP + len(rows) * ROW_H + 40

    def lane_x(i): return LEFT + i * LANE_W + LANE_W // 2
    def row_y(i):  return TOP + i * ROW_H + ROW_H // 2

    hash_to_row = {r["commit"]["hash"]: idx for idx, r in enumerate(rows)}

    L = []
    L.append('<?xml version="1.0" encoding="UTF-8"?>')
    L.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Menlo,Consolas,monospace">')
    L.append(f'<rect width="{W}" height="{H}" fill="#1e1e24"/>')
    if title:
        L.append(f'<text x="{LEFT}" y="30" font-size="18" fill="#ffffff" font-family="Georgia,serif">{_esc(title)}</text>')

    # edges (parent -> child) as curved paths
    for ri, r in enumerate(rows):
        c = r["commit"]
        for pi, ph in enumerate(c["parents"]):
            if ph not in hash_to_row: continue
            pr = hash_to_row[ph]
            x1 = lane_x(r["lane"]); y1 = row_y(ri)
            x2 = lane_x(rows[pr]["lane"]); y2 = row_y(pr)
            color = SVG_LANE_COLORS[r["lane"] % len(SVG_LANE_COLORS)]
            if x1 == x2:
                L.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2"/>')
            else:
                mid_y = (y1 + y2) / 2
                L.append(f'<path d="M {x1} {y1} C {x1} {mid_y}, {x2} {mid_y}, {x2} {y2}" fill="none" stroke="{color}" stroke-width="2"/>')

    # nodes + text
    for ri, r in enumerate(rows):
        c = r["commit"]
        x = lane_x(r["lane"]); y = row_y(ri)
        color = SVG_LANE_COLORS[r["lane"] % len(SVG_LANE_COLORS)]
        if len(c["parents"]) > 1:
            L.append(f'<circle cx="{x}" cy="{y}" r="8" fill="#1e1e24" stroke="{color}" stroke-width="2.5"/>')
        else:
            L.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{color}"/>')
        tx = LEFT + max_lanes * LANE_W + TEXT_PAD
        L.append(f'<text x="{tx}" y="{y+5}" font-size="12" fill="#dddddd">{_esc(_short(c["hash"]))}</text>')
        L.append(f'<text x="{tx+70}" y="{y+5}" font-size="12" fill="#ffffff">{_esc(c["subject"])}</text>')
        if c["refs"]:
            L.append(f'<text x="{tx+70+12*(len(c["subject"])+2)}" y="{y+5}" font-size="11" fill="#f1c40f">{_esc(c["refs"])}</text>')

    L.append('</svg>')
    with open(path, "w") as f: f.write("\n".join(L))
    return os.path.abspath(path)


def _esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


# ============================================================
# CLI
# ============================================================
def cmd_show(path, ref, limit, svg, no_color):
    global SVG_DIR
    if no_color or not _supports_color(): _strip_color()
    try:
        root = repo_root(path)
    except Exception as e:
        print(f"  {RED}not a git repo:{RESET} {path}"); sys.exit(1)
    try:
        commits = load_commits(path, ref=ref, limit=limit)
    except Exception as e:
        print(f"  {RED}git error:{RESET} {e}"); sys.exit(1)
    header()
    branch = current_branch(path)
    print(f"  {DGRAY}repo:{RESET} {WHITE}{root}{RESET}   {DGRAY}branch:{RESET} {CYAN}{branch}{RESET}")
    print()
    render_ascii(commits)
    print()
    if svg:
        os.makedirs(SVG_DIR, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        out = os.path.join(SVG_DIR, f"graph_{ts}.svg")
        try:
            p = render_svg(commits, out, title=f"{os.path.basename(root)} ({branch})")
            print(f"  {GREEN}\u2713{RESET} {DGRAY}svg \u2192{RESET} {WHITE}{p}{RESET}")
        except Exception as e:
            print(f"  {RED}\u2715{RESET} svg: {e}")
        print()


def main():
    ap = argparse.ArgumentParser(prog="gitviz",
                                 description="Render git history as an ASCII / SVG branch graph.")
    ap.add_argument("path", nargs="?", default=".", help="repo path (default: .)")
    ap.add_argument("--ref", default="--all", help="ref to log (default: --all)")
    ap.add_argument("--limit", "-n", type=int, default=200, help="max commits (default 200)")
    ap.add_argument("--svg", action="store_true", help="also export an SVG graph")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    cmd_show(args.path, args.ref, args.limit, args.svg, args.no_color)


if __name__ == "__main__":
    main()
