#!/usr/bin/env python3
"""PolyglotBench - run the same tiny programs in many languages and compare."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROBLEMS_DIR = os.path.join(HERE, "problems")

RESET = "\033[0m"
LGRAY = "\033[37m"
DGRAY = "\033[90m"
BLUE = "\033[94m"
WHITE = "\033[97m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"


def _supports_color():
    if os.environ.get("NO_COLOR"): return False
    if os.environ.get("POLYGLOTBENCH_NO_COLOR"): return False
    if os.environ.get("POLYGLOTBENCH_FORCE_COLOR"): return True
    if not sys.stdout.isatty(): return False
    return True


def _strip_color():
    global RESET, LGRAY, DGRAY, BLUE, WHITE, CYAN, GREEN, YELLOW, RED, MAGENTA
    RESET = LGRAY = DGRAY = BLUE = WHITE = CYAN = GREEN = YELLOW = RED = MAGENTA = ""




# ============================================================
# LOGO
# ============================================================
def _build_logo():
    L  = "[0;37;49m"      # light gray, default bg
    B  = "[0;94;49m"      # bright blue, default bg
    D  = "[0;34;49m"      # dark blue, default bg
    Bd = "[0;94;44m"      # bright blue on dark blue
    Bl = "[0;94;47m"      # bright blue on light gray
    Dl = "[0;34;47m"      # dark blue on light gray
    Ld = "[0;37;44m"      # light gray on dark blue
    return [
 [(L,"                                  ")],
 [(L,"  "),(B,"▄▄▄▄▄"),(L,"▄     "),(B,"▄▄▄▄▄"),(L,"▄    "),(B,"▄▄▄▄▄▄▄"),(L,"▄   ")],
 [(B,"▄█"),(Bd,"▓▓"),(Bl,"▀"),(B,"▀"),(Bd,"▓▓"),(Bl,"▄"),(L,"▄ "),(B,"▄█"),(Bd,"▓▓"),(Bl,"▀"),(B,"▀▀█"),(Bl,"▄"),(L,"▄  "),(B,"██"),(Bd,"▓▓"),(Bl,"▀"),(B,"█"),(Bd,"▓"),(B,"█"),(Bl,"▄"),(L,"▄ ")],
 [(B,"█"),(Bd,"▓▒"),(Bl,"▄"),(L,"▄ "),(B,"▄"),(Bd,"▒▓"),(L,"█ "),(B,"█"),(Bd,"▓▒"),(L,"█    "),(B,"▀"),(L,"▀  "),(B,"█"),(Bd,"▓▒"),(L,"█   "),(Bd,"▓▒"),(L,"█ ")],
 [(Bd,"▓▒░▓▓▒░"),(Bl,"▀"),(L,"▀  "),(Bd,"▓▒░"),(L,"█ "),(Bd,"░░▒▓"),(Bl,"▌"),(L,"▌ "),(Bd,"▓▒"),(B,"▓"),(Bd,"▒▒▒▓█"),(L,"█  ")],
 [(Bd,"▒░"),(D,"█"),(L,"█       "),(Bd,"▒░"),(D,"█"),(L,"█   "),(Bd,"░▒"),(L,"█  "),(Bd,"▒░"),(D,"█"),(L,"█   "),(Bd,"▓▒"),(Bl,"▄"),(L,"▄")],
 [(Bd,"░"),(D,"██"),(L,"█       "),(Bd,"░"),(D,"██"),(Ld,"▀"),(L,"▄  "),(Bd,"░░"),(L,"█  "),(Bd,"░"),(D,"██"),(Ld,"▀"),(L,"▄▄"),(D,"▄"),(Bd,"░░"),(Bl,"▀"),(L,"▀")],
 [(L," "),(D,"▀█"),(L,"█        "),(D,"▀██████"),(Bd,"░"),(L,"█  "),(D,"███████"),(Ld,"▄"),(L,"▀  ")],
    ]


def logo():
    for line in _build_logo():
        print("".join(c + t for c, t in line) + RESET)


def launch_animation():
    if not sys.stdout.isatty():
        logo(); return
    lines = _build_logo()
    prepared = []
    for line in lines:
        chars = []
        for color, text in line:
            for ch in text:
                chars.append((color, ch))
        prepared.append(chars)
    n_lines = len(prepared)
    max_width = max((len(c) for c in prepared), default=80)
    term_w = shutil.get_terminal_size((100, 30)).columns
    if term_w < max_width + 4:
        logo(); return
    HIDE = "\033[?25l"; SHOW = "\033[?25h"
    dim = "\033[0;38;5;238m"
    reset = "\033[0m"
    rainbow = ["\033[0;91m", "\033[0;93m", "\033[0;92m", "\033[0;96m", "\033[0;94m", "\033[0;95m"]
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
                buf.append(reset)
                sys.stdout.write("".join(buf) + "\n")
            sys.stdout.flush(); time.sleep(delay)
    finally:
        sys.stdout.write(SHOW); sys.stdout.flush()


def header():
    print()
    launch_animation()
    print()
    print(f"  {BLUE}PolyglotBench{RESET}  {DGRAY}same programs, many languages{RESET}")
    print(f"  {DGRAY}" + "\u2500" * 60 + RESET)
    print()


LANGUAGES = {
    "python":     {"ext": ".py",  "run": ["python3"]},
    "javascript": {"ext": ".js",  "run": ["node"]},
    "go":         {"ext": ".go",  "run": ["go", "run"]},
    "c":          {"ext": ".c",   "compile": ["cc", "-O2", "-o", "{out}"],   "run": ["{out}"]},
    "cpp":        {"ext": ".cpp", "compile": ["c++", "-O2", "-o", "{out}"],  "run": ["{out}"]},
    "rust":       {"ext": ".rs",  "compile": ["rustc", "-O", "-o", "{out}"], "run": ["{out}"]},
    "ruby":       {"ext": ".rb",  "run": ["ruby"]},
    "bash":       {"ext": ".sh",  "run": ["bash"]},
}


def toolchain_available(lang):
    info = LANGUAGES[lang]
    prog = info["compile"][0] if "compile" in info else info["run"][0]
    return shutil.which(prog) is not None


def discover_problems():
    if not os.path.isdir(PROBLEMS_DIR): return []
    out = []
    for name in sorted(os.listdir(PROBLEMS_DIR)):
        p = os.path.join(PROBLEMS_DIR, name)
        if not os.path.isdir(p): continue
        spec_path = os.path.join(p, "spec.json")
        if not os.path.exists(spec_path): continue
        try:
            with open(spec_path) as f: spec = json.load(f)
        except Exception as e:
            print(f"  {RED}bad spec:{RESET} {name}: {e}"); continue
        impls = {}
        for lang, info in LANGUAGES.items():
            fp = os.path.join(p, name + info["ext"])
            if os.path.exists(fp): impls[lang] = fp
        out.append((name, spec, impls))
    return out


def run_impl(lang, src, cases, timeout=15):
    info = LANGUAGES[lang]
    results = []
    binpath = None
    tmpdir = None
    if "compile" in info:
        tmpdir = tempfile.mkdtemp(prefix="polyglotbench_")
        binpath = os.path.join(tmpdir, "a.out")
        cmd = [c.replace("{out}", binpath) for c in info["compile"]] + [src]
        t0 = time.time()
        try:
            cp = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            cms = (time.time() - t0) * 1000
            if cp.returncode != 0:
                err = (cp.stderr or cp.stdout or "").strip()[:300]
                return [{"status": "COMPILE_FAIL", "err": err, "ms": cms}]
        except Exception as e:
            return [{"status": "COMPILE_FAIL", "err": str(e)[:300], "ms": 0}]
    for i, case in enumerate(cases):
        stdin = case.get("stdin", "")
        expected = case.get("expected", "")
        if "compile" in info:
            cmd = [c.replace("{out}", binpath) for c in info["run"]]
        else:
            cmd = list(info["run"]) + [src]
        t0 = time.time()
        try:
            cp = subprocess.run(cmd, input=stdin, capture_output=True, text=True, timeout=timeout)
            dt = (time.time() - t0) * 1000
            if cp.returncode != 0:
                err = (cp.stderr or cp.stdout or "").strip()[:200]
                results.append({"status": "RUNTIME_FAIL", "err": err, "ms": dt, "case": i}); continue
            if cp.stdout.rstrip() == expected.rstrip():
                results.append({"status": "PASS", "ms": dt, "case": i})
            else:
                results.append({"status": "WRONG", "got": cp.stdout[:200], "want": expected[:200], "ms": dt, "case": i})
        except subprocess.TimeoutExpired:
            results.append({"status": "TIMEOUT", "ms": timeout * 1000, "case": i})
        except Exception as e:
            results.append({"status": "ERROR", "err": str(e)[:200], "ms": 0, "case": i})
    if tmpdir:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results


def summarize(results):
    statuses = [r["status"] for r in results]
    for s in ("COMPILE_FAIL", "RUNTIME_FAIL", "TIMEOUT", "ERROR", "WRONG"):
        if s in statuses: return s
    return "PASS"


def status_color(s):
    return {"PASS": GREEN, "WRONG": YELLOW, "COMPILE_FAIL": RED, "RUNTIME_FAIL": RED,
            "TIMEOUT": MAGENTA, "ERROR": RED, "SKIP": DGRAY}.get(s, RED)


def banner():
    header()


def cmd_list(problems):
    banner()
    for name, spec, impls in problems:
        desc = spec.get("description", "")
        langs = ", ".join(sorted(impls))
        print(f"  {WHITE}{name:<14}{RESET} {LGRAY}{desc}{RESET}")
        print(f"  {' ':<14} {DGRAY}{langs}{RESET}")
        print()


def cmd_run(problems, lang_filter=None):
    banner()
    present = [l for l in LANGUAGES if toolchain_available(l)]
    missing = [l for l in LANGUAGES if l not in present]
    print(f"  {DGRAY}available:{RESET} {WHITE}{', '.join(present) or '(none)'}{RESET}")
    if missing:
        print(f"  {DGRAY}missing:  {RESET} {DGRAY}{', '.join(missing)}{RESET}")
    print()
    totals = {"PASS": 0, "FAIL": 0, "SKIP": 0}
    per_lang = {}
    for name, spec, impls in problems:
        print(f"  {BLUE}{name}{RESET}  {DGRAY}{spec.get('description', '')}{RESET}")
        for lang in sorted(impls):
            if lang_filter and lang != lang_filter: continue
            per_lang.setdefault(lang, {"PASS": 0, "FAIL": 0, "SKIP": 0})
            if not toolchain_available(lang):
                print(f"    {lang:<12} {DGRAY}SKIP{RESET}")
                totals["SKIP"] += 1; per_lang[lang]["SKIP"] += 1
                continue
            results = run_impl(lang, impls[lang], spec["cases"])
            summary = summarize(results)
            color = status_color(summary)
            n_pass = sum(1 for r in results if r.get("status") == "PASS")
            n_total = len(spec["cases"])
            ms_vals = [r.get("ms", 0) for r in results if "ms" in r]
            avg_ms = sum(ms_vals) / len(ms_vals) if ms_vals else 0.0
            print(f"    {lang:<12} {color}{summary:<12}{RESET} {DGRAY}{n_pass}/{n_total}    {avg_ms:>7.1f}ms{RESET}")
            if summary == "PASS":
                totals["PASS"] += 1; per_lang[lang]["PASS"] += 1
            else:
                totals["FAIL"] += 1; per_lang[lang]["FAIL"] += 1
                for r in results:
                    if r.get("status") != "PASS":
                        msg = r.get("err") or r.get("got") or r.get("status", "")
                        print(f"      {RED}case {r.get('case', '?')}: {r.get('status')}  {str(msg)[:120]}{RESET}")
        print()
    print(f"  {DGRAY}" + "\u2500" * 60 + RESET)
    print(f"  {GREEN}{totals['PASS']} pass{RESET}   {RED}{totals['FAIL']} fail{RESET}   {DGRAY}{totals['SKIP']} skip{RESET}")
    print()
    if per_lang and not lang_filter:
        print(f"  {DGRAY}per language:{RESET}")
        for lang in sorted(per_lang):
            s = per_lang[lang]
            print(f"    {lang:<12} {GREEN}{s['PASS']}{RESET} pass  {RED}{s['FAIL']}{RESET} fail  {DGRAY}{s['SKIP']}{RESET} skip")
        print()


def main():
    ap = argparse.ArgumentParser(prog="polyglotbench",
                                 description="Run the same tiny programs in many languages and compare output.")
    ap.add_argument("problem", nargs="?", help="run only this problem")
    ap.add_argument("--lang", "-l", help="run only this language")
    ap.add_argument("--list", action="store_true", help="list problems and available implementations")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    if args.no_color or not _supports_color(): _strip_color()
    problems = discover_problems()
    if not problems:
        print(f"  {RED}no problems found in {PROBLEMS_DIR}{RESET}"); sys.exit(1)
    if args.problem:
        problems = [p for p in problems if p[0] == args.problem]
        if not problems:
            print(f"  {RED}no such problem: {args.problem}{RESET}"); sys.exit(1)
    if args.list: cmd_list(problems); return
    cmd_run(problems, lang_filter=args.lang)


if __name__ == "__main__":
    main()
