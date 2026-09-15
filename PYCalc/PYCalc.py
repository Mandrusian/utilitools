#!/usr/bin/env python3
"""PYCalc — terminal mathematics engine (all features)."""

import ast, atexit, cmath, json, math, operator, os, re, shutil, sys, time

# ============================================================
# READLINE
# ============================================================
def _is_wine():
    """Detect Wine / CrossOver (returns True if running under either)."""
    if os.environ.get("WINEPREFIX") or os.environ.get("WINEDLLPATH"):
        return True
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        ntdll = ctypes.windll.ntdll
        ntdll.wine_get_version.restype = ctypes.c_char_p
        ver = ntdll.wine_get_version()
        return bool(ver)
    except Exception:
        return False


def _color_supported():
    """False if we should strip ANSI entirely."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("PYCALC_NO_COLOR"):
        return False
    if os.environ.get("PYCALC_FORCE_COLOR"):
        return True
    if _is_wine():
        return False   # Wine's console can't render ANSI
    return True


def _strip_ansi_if_needed():
    if _color_supported():
        return
    for preset in THEME_PRESETS.values():
        for k in list(preset.keys()):
            if k == "RAINBOW":
                preset[k] = [""] * 7
            else:
                preset[k] = ""


READLINE_OK = False
try:
    import readline
    READLINE_OK = True
    _HISTFILE = os.path.expanduser("~/.pycalc_history")
    try: readline.read_history_file(_HISTFILE)
    except (FileNotFoundError, OSError): pass
    readline.set_history_length(2000)
    def _save_history():
        try: readline.write_history_file(_HISTFILE)
        except OSError: pass
    atexit.register(_save_history)
except ImportError:
    try:
        import pyreadline3 as readline  # Windows fallback
        READLINE_OK = True
        _HISTFILE = os.path.expanduser("~/.pycalc_history")
        try: readline.read_history_file(_HISTFILE)
        except (FileNotFoundError, OSError): pass
    except ImportError:
        pass


def _paint(s):
    if not READLINE_OK: return s
    return re.sub(r"\x1b\[[0-9;]*m", lambda m: "\001" + m.group() + "\002", s)


def prompt_main():   return _paint(f"  {BLUE}❯{RESET} ")
def prompt_var(n):   return _paint(f"  {BLUE}◆{RESET} {WHITE}{n}{RESET} {DGRAY}={RESET} ")
def prompt_choice(): return _paint(f"  {BLUE}❯{RESET} ")

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
# MATH CONSTANTS
# ============================================================
LIGHT_SPEED = 299792458.0
EULER = math.e

CONSTANTS = {
    "pi": math.pi, "e": math.e, "i": 1j, "j": 1j,
    "LIGHT_SPEED": LIGHT_SPEED, "EULER": EULER,
}
CONSTANT_NAMES = set(CONSTANTS)


def _dispatch(mathfn, cmathfn, x, deg_in=False, deg_out=False):
    if deg_in and not isinstance(x, complex):
        x = math.radians(x)
    try:
        r = mathfn(x)
    except (ValueError, TypeError):
        try: r = cmathfn(x)
        except Exception: raise ValueError("invalid input for function")
    if deg_out and not isinstance(r, complex):
        r = math.degrees(r)
    return r


def _mk_sin():  return lambda x: _dispatch(math.sin, cmath.sin, x, deg_in=(STATE["angle"] == "deg"))
def _mk_cos():  return lambda x: _dispatch(math.cos, cmath.cos, x, deg_in=(STATE["angle"] == "deg"))
def _mk_tan():  return lambda x: _dispatch(math.tan, cmath.tan, x, deg_in=(STATE["angle"] == "deg"))
def _mk_asin(): return lambda x: _dispatch(math.asin, cmath.asin, x, deg_out=(STATE["angle"] == "deg"))
def _mk_acos(): return lambda x: _dispatch(math.acos, cmath.acos, x, deg_out=(STATE["angle"] == "deg"))
def _mk_atan(): return lambda x: _dispatch(math.atan, cmath.atan, x, deg_out=(STATE["angle"] == "deg"))


BASIC_FUNCTIONS = {
    "sqrt": lambda x: _dispatch(math.sqrt, cmath.sqrt, x),
    "abs": abs, "round": round,
    "floor": lambda x: math.floor(x.real if isinstance(x, complex) else x),
    "ceil":  lambda x: math.ceil(x.real if isinstance(x, complex) else x),
    "sin": _mk_sin, "cos": _mk_cos, "tan": _mk_tan,
    "radians": math.radians, "degrees": math.degrees,
}
ADVANCED_FUNCTIONS = {
    "asin": _mk_asin, "acos": _mk_acos, "atan": _mk_atan,
    "sinh": lambda x: _dispatch(math.sinh, cmath.sinh, x),
    "cosh": lambda x: _dispatch(math.cosh, cmath.cosh, x),
    "tanh": lambda x: _dispatch(math.tanh, cmath.tanh, x),
    "log":  lambda x: _dispatch(math.log10, lambda z: cmath.log(z)/cmath.log(10), x),
    "ln":   lambda x: _dispatch(math.log, cmath.log, x),
    "exp":  lambda x: _dispatch(math.exp, cmath.exp, x),
}
ALL_FUNC_NAMES = set(BASIC_FUNCTIONS) | set(ADVANCED_FUNCTIONS)


def resolve_fn(name, args):
    fn = BASIC_FUNCTIONS.get(name) or ADVANCED_FUNCTIONS.get(name)
    if fn is None: return None
    # factories need to be called to build per-call lambdas
    if name in ("sin","cos","tan","asin","acos","atan"):
        fn = fn()
    return fn(*args)


BINARY_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
              ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod}
UNARY_OPS  = {ast.UAdd: operator.pos, ast.USub: operator.neg}

# ============================================================
# STATE
# ============================================================
STATE = {
    "last_ans": 0.0, "last_expr": "",
    "var_cache": {}, "forced_prompts": set(),
    "rainbow": "auto", "theme": "default",
    "advanced": False, "status_line": True, "animations": True,
    "angle": "rad", "user_funcs": {}, "fractions": False,
}
CONFIG_PATH = os.path.expanduser("~/.pycalc_config.json")
FIRST_RUN_FLAG = os.path.expanduser("~/.pycalc_seen")
SESSION_DIR = os.path.expanduser("~/.pycalc_sessions")


def load_config():
    try:
        with open(CONFIG_PATH) as f: data = json.load(f)
        for k in ("rainbow","theme","advanced","status_line","animations","angle","user_funcs","fractions"):
            if k in data: STATE[k] = data[k]
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass


def save_config():
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump({k: STATE[k] for k in
                       ("rainbow","theme","advanced","status_line","animations","angle","user_funcs","fractions")},
                      f, indent=2)
    except OSError:
        pass


def is_first_run(): return not os.path.exists(FIRST_RUN_FLAG)
def mark_seen():
    try: open(FIRST_RUN_FLAG, "w").close()
    except OSError: pass


def reserved_names():
    return ALL_FUNC_NAMES | CONSTANT_NAMES | {"ans"} | set(STATE["user_funcs"])

# ============================================================
# LOGO
# ============================================================
def _build_logo():
    return [
 [(DGRAY,"  ▄▓▒▄▄"),(LGRAY,"         "),(DGRAY,"▄▓▒▄"),(LGRAY,"          "),
  (DGRAY,"▄▓▒▄▄"),(LGRAY,"         "),(DGRAY,"▄▓▒▄▄"),(LGRAY,"         "),
  (DGRAY,"▄▓▒▄"),(LGRAY,"          "),(DGRAY,"▄▓▒▄▄"),(LGRAY,"       ")],
 [(LGRAY," ▄▄"),(BLUE,"▄"),(LGRAY," "),(DGRAY,"▀▀▀▀▓▒▄"),(LGRAY,"  ▐▄▄"),(BLUE,"▄"),
  (LGRAY," "),(DGRAY,"▀▒"),(LGRAY,"  "),(DGRAY,"■▒▄"),(LGRAY,"   ▄▄"),(BLUE,"▄"),
  (LGRAY," "),(DGRAY,"▀▀▀▀▓▒▄"),(LGRAY,"  ▐▄▄"),(BLUE,"▄"),(LGRAY," "),
  (DGRAY,"▀▀▀▀▓▒▄"),(LGRAY,"   ▄▄"),(BLUE,"▄"),(LGRAY," "),(DGRAY,"█▒▄"),
  (LGRAY,"       ▄▄"),(BLUE,"▄"),(LGRAY," "),(DGRAY,"▀▀▀▀▓▒▄"),(LGRAY,"  ")],
 [(LGRAY,"▐"),(BLUE,"███▓████"),(BLUE,"▄"),(DBLUE,"▄"),(DGRAY,"▀▒"),(LGRAY," ▐"),
  (BLUE,"███▓"),(LGRAY," "),(DGRAY,"▓▌"),(BLUE,"█"),(BLUE,"▄"),(DBLUE,"▄"),
  (DGRAY,"▀▒"),(LGRAY," ▐"),(BLUE,"███▓████"),(BLUE,"▄"),(DBLUE,"▄"),
  (DGRAY,"▀▒"),(LGRAY," ▐"),(BLUE,"███▓████"),(BLUE,"▄"),(DBLUE,"▄"),
  (DGRAY,"▀▒"),(LGRAY," ▐"),(BLUE,"███▓"),(DGRAY,"▐▒▌"),(LGRAY,"      ▐"),
  (BLUE,"███▓████"),(BLUE,"▄"),(DBLUE,"▄"),(DGRAY,"▀▒"),(LGRAY," ")],
 [(BLUE,"▐"),(BLUE,"▓▓▒░"),(DBLUE,"▀"),(BLUE,"▀█"),(BLUE,"▒▒▓"),(DBLUE,"▌"),
  (DGRAY,"░▌"),(BLUE,"▐"),(BLUE,"▓▓▒░"),(LGRAY," "),(DGRAY,"▓▌"),(BLUE,"▒▒▓"),
  (DBLUE,"▌"),(DGRAY,"░▌"),(BLUE,"▐"),(BLUE,"▓▓▒░"),(DBLUE,"▀"),(BLUE,"▀▀"),
  (BLUE,"▒▒▓"),(DBLUE,"▌"),(DGRAY,"░▌"),(BLUE,"▐"),(BLUE,"▓▓▒░"),(DBLUE,"▀"),
  (BLUE,"▀▀"),(BLUE,"▒▒▓"),(DBLUE,"▌"),(DGRAY,"░▌"),(BLUE,"▐"),(BLUE,"▓▓▒░"),
  (DGRAY,"▐▓▌"),(LGRAY,"      "),(BLUE,"▐"),(BLUE,"▓▓▒░"),(DBLUE,"▀"),
  (BLUE,"▀▀"),(BLUE,"▒▒▓"),(DBLUE,"▌"),(DGRAY,"░▌")],
 [(BLUE,"▐"),(BLUE,"▓▒░"),(DBLUE,"█"),(DGRAY,"▐▌"),(LGRAY," "),(BLUE,"░░"),
  (DBLUE,"▀"),(LGRAY," "),(DGRAY,"▒▌"),(BLUE,"▐"),(BLUE,"▓▒░"),(DBLUE,"█"),
  (LGRAY," "),(DGRAY,"▀"),(LGRAY," "),(BLUE,"░░░"),(DBLUE,"▌"),(DGRAY,"▒▌"),
  (BLUE,"▐"),(BLUE,"▓▒░"),(DBLUE,"█"),(DGRAY,"▐▓"),(LGRAY," "),(DBLUE,"▀▀▀"),
  (LGRAY,"   "),(BLUE,"▐"),(BLUE,"▓▒░"),(DBLUE,"█"),(LGRAY," "),(DGRAY,"▀"),
  (LGRAY," "),(BLUE,"░░░"),(DBLUE,"▌"),(DGRAY,"▒▌"),(BLUE,"▐"),(BLUE,"▓▒░"),
  (DBLUE,"█"),(DGRAY,"▐▓▌"),(LGRAY,"      "),(BLUE,"▐"),(BLUE,"▓▒░"),
  (DBLUE,"█"),(DGRAY,"▐▓"),(LGRAY," "),(DBLUE,"▀▀▀"),(LGRAY,"   ")],
 [(BLUE,"▐"),(DBLUE,"█▓▓█▄▄█▀"),(LGRAY," "),(DGRAY,"■▀"),(LGRAY,"   "),
  (DBLUE,"▀▀▀▀▀▀▀█▓█▌"),(DGRAY,"▒▌"),(BLUE,"▐"),(DBLUE,"█▓▓█"),(DGRAY,"▐▒"),
  (LGRAY,"  "),(DGRAY,"▄▓▒▒▌"),(BLUE,"▐"),(DBLUE,"█▓▓█▀▀▀█▓█▌"),(DGRAY,"▒▌"),
  (BLUE,"▐"),(DBLUE,"█▓▓█"),(DGRAY,"▐▒▌"),(LGRAY," "),(DGRAY,"▄▓▒▒"),
  (LGRAY," "),(BLUE,"▐"),(DBLUE,"█▓▓█"),(DGRAY,"▐▒"),(LGRAY,"  "),(DGRAY,"▄▓▒▒▌")],
 [(DBLUE,"▐▒▒▒█"),(DGRAY,"■▄▄"),(LGRAY,"      "),(DBLUE,"▐████"),(DGRAY,"▐▒▌"),
  (DBLUE,"█▒▒▌"),(DGRAY,"▓▌"),(DBLUE,"▐▒▒▒█"),(DGRAY,"▐░"),(LGRAY," "),
  (DBLUE,"▄▄▄"),(LGRAY," "),(DGRAY,"▓▌"),(DBLUE,"▐▒▒▒█"),(DGRAY,"▐▒▌"),
  (DBLUE,"█▒▒▌"),(DGRAY,"▓▌"),(DBLUE,"▐▒▒▒█"),(DGRAY,"▐░"),(LGRAY," "),
  (DBLUE,"▄▄▄"),(LGRAY," "),(DGRAY,"▓▌"),(DBLUE,"▐▒▒▒█"),(DGRAY,"▐░"),
  (LGRAY," "),(DBLUE,"▄▄▄"),(LGRAY," "),(DGRAY,"▓▌")],
 [(DBLUE,"▐░░░█"),(DGRAY,"▐▓▓"),(LGRAY,"      "),(DBLUE,"▐░░░▐▄▄▄█░░"),
  (LGRAY," "),(DGRAY,"█"),(LGRAY," "),(DBLUE,"▐░░░▓▄▄▄█▒▒▌"),(DGRAY,"▀▌"),
  (DBLUE,"▐░░░▐"),(LGRAY," "),(DGRAY,"▀"),(LGRAY," "),(DBLUE,"█░░▌"),
  (DGRAY,"▀▌"),(DBLUE,"▐░░░▓▄▄▄█▒▒▌"),(DGRAY,"▀▌"),(DBLUE,"▐░░░▓▄▄▄█▒▒▌"),
  (DGRAY,"▀▌")],
    ]


def clear(): sys.stdout.write("\033[2J\033[H"); sys.stdout.flush()

def logo():
    for line in _build_logo():
        print("".join(c + t for c, t in line) + RESET)

def launch_animation():
    """Rainbow sweeps across the logo (left -> right), then settles on real colors."""
    if not STATE["animations"]:
        logo()
        return

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
        logo()
        return

    HIDE = "\033[?25l"
    SHOW = "\033[?25h"
    ERASE_DOWN = "\033[J"
    dim = "\033[38;5;238m"
    rainbow = [RED, "\033[33m", YELLOW, GREEN, CYAN, BLUE, MAGENTA]
    n_colors = len(rainbow)

    sys.stdout.write(HIDE)
    sys.stdout.flush()

    try:
        # Brief symbolic form: N = P(256), the polynomial whose base-256
        # expansion is the exact byte sequence of the colored logo.
        print(f"  {DGRAY}P(x) = c\u2080\u00b7x\u207f\u207b\u00b9 + \u2026 + c\u2099\u208b\u2081     N = P(256){RESET}")
        sys.stdout.flush()
        time.sleep(0.45)

        sys.stdout.write(f"\033[1A{ERASE_DOWN}")
        sys.stdout.flush()

        frames = 30
        delay = 0.032
        sweep_half = 9

        for frame in range(frames + 1):
            if frame > 0:
                sys.stdout.write(f"\033[{n_lines}A")

            t = frame / frames
            sweep_pos = -sweep_half + t * (max_width + 2 * sweep_half)

            for chars in prepared:
                buf = []
                prev = None
                for col, (target, ch) in enumerate(chars):
                    if ch == " ":
                        buf.append(ch)
                        continue
                    dist = abs(col - sweep_pos)
                    if dist <= sweep_half:
                        c = rainbow[int(col * 1.6 + frame * 0.9) % n_colors]
                    elif col < sweep_pos:
                        c = target
                    else:
                        c = dim
                    if c != prev:
                        buf.append(c)
                        prev = c
                    buf.append(ch)
                buf.append(RESET)
                sys.stdout.write("".join(buf) + "\n")

            sys.stdout.flush()
            time.sleep(delay)
    finally:
        sys.stdout.write(SHOW)
        sys.stdout.flush()


def divider():
    width = min(max(shutil.get_terminal_size((100, 30)).columns - 4, 30), 90)
    color = {"on": GREEN, "auto": BLUE, "off": DGRAY}.get(STATE["rainbow"], BLUE)
    print("  " + color + "─" * width + RESET)

def wordmark_pulse():
    tail = DGRAY + "• terminal mathematics engine • Python backend" + RESET
    if not STATE["animations"]:
        print(f"  {BLUE}PYCalc{RESET} {tail}")
        return
    for c in [BLUE, WHITE, BLUE, WHITE, BLUE]:
        sys.stdout.write(f"\r  {c}PYCalc{RESET} {tail}")
        sys.stdout.flush(); time.sleep(0.07)
    print()

def first_run_intro():
    clear()
    for line in _build_logo():
        print("".join(c + t for c, t in line) + RESET)
        time.sleep(0.035)
    time.sleep(0.15); print()
    user = os.environ.get("USER", "friend")
    print(f"  {BLUE}PYCalc{RESET} {DGRAY}• welcome, {user}{RESET}"); time.sleep(0.35)
    print(f"  {DGRAY}Type {WHITE}help{RESET}{DGRAY} to see what's possible.{RESET}"); time.sleep(0.4)
    print(f"  {DGRAY}Type {WHITE}guide{RESET}{DGRAY} for a beginner's tour.{RESET}"); time.sleep(0.4)
    print(f"  {DGRAY}Type {WHITE}settings{RESET}{DGRAY} to customise.{RESET}"); time.sleep(0.5)
    print()
    try: input(f"  {DGRAY}Press Enter to continue…{RESET}")
    except (EOFError, KeyboardInterrupt): pass
    mark_seen()

def header(animate=False):
    clear()
    if animate:
        launch_animation()
    else:
        logo()
    print(); wordmark_pulse(); print(); divider()
    print(f"  {DGRAY}COMMANDS{RESET}")
    print(f"  {BLUE}help{RESET}        context-sensitive help")
    print(f"  {BLUE}guide{RESET}       beginner's tour")
    print(f"  {BLUE}functions{RESET}   available functions")
    print(f"  {BLUE}constants{RESET}   mathematical constants")
    print(f"  {BLUE}vars{RESET}        cached variables & user functions")
    print(f"  {BLUE}settings{RESET}    settings menu")
    print(f"  {BLUE}history{RESET}     recent inputs (!n to recall)")
    print(f"  {BLUE}save{RESET}/{BLUE}load{RESET}   named session persistence")
    print(f"  {BLUE}plot{RESET}        {DGRAY}plot(expr[; expr...], xmin, xmax[, ymin, ymax]){RESET}")
    print(f"  {BLUE}svg{RESET}         {DGRAY}svg(expr[; expr...], xmin, xmax[, ymin, ymax][, name]){RESET}")
    print(f"  {BLUE}svg-list{RESET}    browse recent SVGs   {BLUE}svg-open{RESET}  open one in an app")
    print(f"  {BLUE}clear{RESET}       redraw interface")
    print(f"  {BLUE}exit{RESET}        quit")
    print()
    adv = f"{GREEN}on{RESET}" if STATE["advanced"] else f"{DGRAY}off{RESET}"
    ang = STATE["angle"]
    frac = f"{GREEN}on{RESET}" if STATE["fractions"] else f"{DGRAY}off{RESET}"
    print(f"  {DGRAY}Advanced:{RESET} {adv}    {DGRAY}Angle:{RESET} {ang}    {DGRAY}Fractions:{RESET} {frac}    {DGRAY}Answer reuse:{RESET} {LGRAY}ans  ans-q{RESET}")
    print(); divider()

# ============================================================
# PARSE / EVAL
# ============================================================
def normalize(expr):
    expr = expr.strip().replace("`", "").replace("π", "pi")
    expr = re.sub(r"\b0x([0-9a-fA-F]+)\b", lambda m: str(int(m.group(1), 16)), expr)
    expr = re.sub(r"\b0b([01]+)\b",        lambda m: str(int(m.group(1), 2)),  expr)
    expr = re.sub(r"\b0o([0-7]+)\b",       lambda m: str(int(m.group(1), 8)),  expr)
    expr = re.sub(r"~[cC]", "LIGHT_SPEED", expr)
    expr = re.sub(r"~[eE]", "EULER", expr)
    # √16 -> sqrt(16), √(x+1) -> sqrt(x+1), √x -> sqrt(x)
    expr = re.sub(r"√\s*\(", "sqrt(", expr)
    expr = re.sub(r"√\s*(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)", r"sqrt(\1)", expr)
    expr = re.sub(r"√\s*([A-Za-z_][A-Za-z_0-9]*)", r"sqrt(\1)", expr)
    # degrees: 30° -> radians(30)
    expr = re.sub(r"(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*°", r"radians(\1)", expr)
    # percent of: 20% of 80 -> (20/100)*(80)
    expr = re.sub(r"(\d+(?:\.\d+)?)\s*%\s*of\s+(\S+)", r"(\1/100)*(\2)", expr)
    return (expr.replace("×", "*").replace("÷", "/")
                .replace("−", "-").replace("^", "**"))


def tokenize(expr):
    pat = r"""
        (?P<number>(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)
        |(?P<identifier>[A-Za-z_][A-Za-z_0-9]*)
        |(?P<operator>\*\*|[+\-*/%(),])
    """
    toks = []; pos = 0
    for m in re.finditer(pat, expr, re.X):
        if m.start() != pos and expr[pos:m.start()].strip():
            raise ValueError(f"unexpected character: {expr[pos:m.start()]!r}")
        toks.append(m.group()); pos = m.end()
    if expr[pos:].strip(): raise ValueError(f"unexpected character: {expr[pos:]!r}")
    return toks


def split_identifier(tok):
    if not re.fullmatch(r"[A-Za-z]+", tok): return [tok]
    if tok in reserved_names(): return [tok]
    if len(tok) == 1: return [tok]
    return list(tok)


def expand_ids(toks):
    out = []
    for t in toks: out.extend(split_identifier(t))
    return out


def is_num(t):  return bool(re.fullmatch(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", t))
def is_id(t):   return bool(re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", t))
def is_func(t): return t in ALL_FUNC_NAMES or t in STATE["user_funcs"]

def ends_val(t):   return t == ")" or is_num(t) or (is_id(t) and not is_func(t))
def starts_val(t): return t == "(" or is_num(t) or is_id(t)


def insert_implicit_mul(toks):
    out = []
    for t in toks:
        if out and ends_val(out[-1]) and starts_val(t):
            out.append("*")
        out.append(t)
    return out


def prepare(expr):
    return " ".join(insert_implicit_mul(expand_ids(tokenize(normalize(expr)))))


def _as_num(x):
    if isinstance(x, bool): raise ValueError("invalid number")
    if isinstance(x, complex): return x
    if isinstance(x, int): return x
    return float(x)


def safe_eval(expr, variables, _depth=0):
    if _depth > 20: raise ValueError("expression too deeply nested")
    merged = {**STATE["var_cache"], **variables}
    tree = ast.parse(prepare(expr), mode="eval")

    def ev(node):
        if isinstance(node, ast.Expression): return ev(node.body)
        if isinstance(node, ast.Constant): return _as_num(node.value)
        if isinstance(node, ast.Name):
            if node.id == "ans": return STATE["last_ans"]
            if node.id in merged: return _as_num(merged[node.id])
            if node.id in CONSTANTS: return CONSTANTS[node.id]
            raise ValueError(f"unknown variable '{node.id}'")
        if isinstance(node, ast.BinOp):
            op = BINARY_OPS.get(type(node.op))
            if op is None: raise ValueError("operator not allowed")
            try: return op(ev(node.left), ev(node.right))
            except ZeroDivisionError: raise ValueError("division by zero")
            except OverflowError:     raise ValueError("result overflow")
            except (ValueError, TypeError) as e: raise ValueError(str(e))
        if isinstance(node, ast.UnaryOp):
            op = UNARY_OPS.get(type(node.op))
            if op is None: raise ValueError("operator not allowed")
            return op(ev(node.operand))
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name): raise ValueError("invalid function")
            name = node.func.id
            if node.keywords: raise ValueError("keyword arguments are not supported")
            if name in STATE["user_funcs"]:
                spec = STATE["user_funcs"][name]
                params = spec["params"]
                if len(node.args) != len(params):
                    raise ValueError(f"{name}() expects {len(params)} argument(s)")
                args = [ev(a) for a in node.args]
                local = dict(zip(params, args))
                return safe_eval(spec["body"], {**merged, **local}, _depth + 1)
            if name in ADVANCED_FUNCTIONS and not STATE["advanced"]:
                raise ValueError(f"'{name}' needs advanced mode — type 'settings'")
            if name not in ALL_FUNC_NAMES:
                raise ValueError(f"unknown function '{name}'")
            try: return resolve_fn(name, [ev(a) for a in node.args])
            except TypeError:
                raise ValueError(f"{name}() has an invalid number of arguments")
            except ValueError as e: raise ValueError(str(e))
            except OverflowError: raise ValueError("result overflow")
        raise ValueError("unsupported expression")

    return ev(tree)


def format_number(v, _no_fraction=False):
    base = _format_base(v)
    if _no_fraction or not STATE.get("fractions"):
        return base
    if not isinstance(v, float) or not math.isfinite(v):
        return base
    if v.is_integer() or abs(v) > 1e15:
        return base
    try:
        from fractions import Fraction
        frac = Fraction(v).limit_denominator(1000)
        if frac.denominator != 1 and abs(float(frac) - v) < 1e-9:
            return f"{base}  ({frac.numerator}/{frac.denominator})"
    except (ValueError, OverflowError):
        pass
    return base


def _format_base(v):
    if isinstance(v, complex):
        if abs(v.imag) < 1e-14: v = v.real
        else:
            r, im = v.real, v.imag
            if abs(r) < 1e-14:
                if abs(im - 1) < 1e-14:  return "i"
                if abs(im + 1) < 1e-14:  return "-i"
                return _format_base(im) + "i"
            sign = "+" if im >= 0 else "-"
            ai = abs(im)
            if abs(ai - 1) < 1e-14: return f"{_format_base(r)} {sign} i"
            return f"{_format_base(r)} {sign} {_format_base(ai)}i"
    if not isinstance(v, (int, float)): v = float(v)
    if not math.isfinite(v): return str(v)
    if abs(v) < 1e-14: v = 0.0
    if isinstance(v, float) and v.is_integer() and abs(v) < 1e15: return str(int(v))
    if isinstance(v, int): return str(v)
    return f"{v:.14g}"


def extract_variables(expr):
    tree = ast.parse(prepare(expr), mode="eval")
    names = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and n.id not in reserved_names() and n.id != "ans":
            names.add(n.id)
    return names

# ============================================================
# ANIMATION
# ============================================================
def should_anim(ctx):
    m = STATE["rainbow"]
    if m == "on": return True
    if m == "off": return False
    return ctx in ("equation", "constant")

def rainbow_result(prefix, result, ctx="result"):
    if not should_anim(ctx):
        print(f"  {prefix}{WHITE}{result}{RESET}"); return
    sys.stdout.write(f"  {DGRAY}Calculating...{RESET}"); sys.stdout.flush()
    time.sleep(0.10); sys.stdout.write("\r" + " " * 70 + "\r"); sys.stdout.flush()
    for c in RAINBOW:
        sys.stdout.write(f"\r  {prefix}{c}{result}{RESET}")
        sys.stdout.flush(); time.sleep(0.055)
    sys.stdout.write(f"\r  {prefix}{WHITE}{result}{RESET}\n"); sys.stdout.flush()

def reveal_constant(label, value_str):
    print(); prefix = f"➔ {label} = "
    sys.stdout.write(f"  {DGRAY}Calculating...{RESET}"); sys.stdout.flush()
    time.sleep(0.15); sys.stdout.write("\r" + " " * 70 + "\r"); sys.stdout.flush()
    for c in RAINBOW:
        sys.stdout.write(f"\r  {prefix}{c}{value_str}{RESET}")
        sys.stdout.flush(); time.sleep(0.075)
    sys.stdout.write(f"\r  {prefix}{WHITE}{value_str}{RESET}\n"); sys.stdout.flush(); print()

# ============================================================
# PROMPTING
# ============================================================
def ask_variable(name):
    forced = STATE["forced_prompts"]
    if name not in forced and name in STATE["var_cache"]:
        v = STATE["var_cache"][name]
        print(f"  {DGRAY}◆ Using cached {name} = {format_number(v)}{RESET}")
        return v
    while True:
        try: value = input(prompt_var(name)).strip()
        except (EOFError, KeyboardInterrupt): print(); raise SystemExit
        if not value: continue
        try:
            r = safe_eval(value, {})
            print(f"  {DGRAY}↳{RESET} {GREEN}{format_number(r)}{RESET}")
            STATE["var_cache"][name] = r
            return r
        except Exception as exc:
            print(f"  {RED}✕{RESET} {exc}")


def calculate_equation(left, right):
    left, right = left.strip(), right.strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", left):
        raise ValueError("left side must be a single result variable")
    target = left
    variables = sorted(extract_variables(right) - {target})
    values = {n: ask_variable(n) for n in variables}
    result = safe_eval(right, values)
    STATE["last_ans"] = result
    STATE["last_expr"] = right
    STATE["var_cache"][target] = result
    print()
    rainbow_result(f"{target} = ", format_number(result), ctx="equation")
    print(f"  {DGRAY}{right} = {format_number(result)}{RESET}")
    return result

# ============================================================
# UNITS
# ============================================================
UNITS = {
    "length":  {"m":1, "km":1000, "cm":0.01, "mm":0.001, "mi":1609.344,
                "ft":0.3048, "in":0.0254, "yd":0.9144, "nmi":1852},
    "mass":    {"kg":1, "g":0.001, "mg":1e-6, "lb":0.45359237,
                "oz":0.028349523125, "t":1000, "tonne":1000},
    "time":    {"s":1, "sec":1, "min":60, "h":3600, "hr":3600,
                "day":86400, "wk":604800, "yr":31536000},
    "volume":  {"l":1, "ml":0.001, "gal":3.785411784, "qt":0.946352946,
                "pt":0.473176473, "cup":0.2365882365, "floz":0.0295735295625},
}

UNIT_ALIASES = {
    "meter":"m","metre":"m","meters":"m","metres":"m",
    "kilometer":"km","kilometre":"km","kilometers":"km","kilometres":"km",
    "mile":"mi","miles":"mi","foot":"ft","feet":"ft","inch":"in","inches":"in",
    "yard":"yd","yards":"yd","kilogram":"kg","kilograms":"kg","kilos":"kg",
    "gram":"g","grams":"g","pound":"lb","pounds":"lb","lbs":"lb",
    "ounce":"oz","ounces":"oz","second":"s","seconds":"s","secs":"s",
    "minute":"min","minutes":"min","hour":"h","hours":"h","hrs":"h",
    "day":"day","days":"day","week":"wk","weeks":"wk","year":"yr","years":"yr",
    "liter":"l","litre":"l","liters":"l","litres":"l","celsius":"c",
    "fahrenheit":"f","kelvin":"k",
}

def _canon_unit(u):
    u = u.strip().lower()
    return UNIT_ALIASES.get(u, u)

def convert_units(value, from_u, to_u):
    f, t = _canon_unit(from_u), _canon_unit(to_u)
    # temperature
    if f in ("c","f","k") and t in ("c","f","k"):
        if f == "c": c = value
        elif f == "f": c = (value - 32) * 5/9
        else: c = value - 273.15
        if t == "c": return c
        if t == "f": return c * 9/5 + 32
        return c + 273.15
    for table in UNITS.values():
        if f in table and t in table:
            return value * table[f] / table[t]
    raise ValueError(f"cannot convert '{from_u}' to '{to_u}'")

# ============================================================
# BASE CONVERSION
# ============================================================
BASE_TARGETS = {
    "hex":"hexadecimal","hexadecimal":"hexadecimal",
    "bin":"binary","binary":"binary",
    "oct":"octal","octal":"octal",
    "dec":"decimal","decimal":"decimal",
}

def format_base(value, target):
    n = int(value)
    if target == "hexadecimal": return hex(n)
    if target == "binary":      return bin(n)
    if target == "octal":       return oct(n)
    return str(n)

# ============================================================
# PLOT
# ============================================================
def split_top_commas(s):
    parts=[]; depth=0; cur=""
    for ch in s:
        if ch == "(": depth += 1; cur += ch
        elif ch == ")": depth -= 1; cur += ch
        elif ch == "," and depth == 0: parts.append(cur.strip()); cur = ""
        else: cur += ch
    if cur: parts.append(cur.strip())
    return parts

def split_top(s, sep):
    parts = []; depth = 0; cur = ""
    for ch in s:
        if ch == "(": depth += 1; cur += ch
        elif ch == ")": depth -= 1; cur += ch
        elif ch == sep and depth == 0: parts.append(cur.strip()); cur = ""
        else: cur += ch
    if cur.strip(): parts.append(cur.strip())
    return parts


def _sample_curve(expr, xmin, xmax, n):
    out = []
    for i in range(n):
        x = xmin + (xmax - xmin) * i / (n - 1)
        try:
            y = safe_eval(expr, {"x": x})
            if isinstance(y, complex): y = y.real
            y = float(y)
            if not math.isfinite(y): y = None
        except Exception:
            y = None
        out.append((x, y))
    return out


def _auto_range(all_valid, ymin, ymax):
    if ymin is not None and ymax is not None:
        return ymin, ymax
    ys = sorted(all_valid); n = len(ys)
    q1 = ys[n // 4]; q3 = ys[(3 * n) // 4]
    iqr = q3 - q1
    if iqr == 0:
        lo, hi = min(all_valid), max(all_valid)
    else:
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    inliers = [y for y in all_valid if lo <= y <= hi] or all_valid
    if ymin is None: ymin = min(inliers)
    if ymax is None: ymax = max(inliers)
    if ymax - ymin < 1e-9:
        ymax = ymin + 1; ymin -= 1
    return ymin, ymax


def do_plot(exprs, xmin, xmax, ymin=None, ymax=None):
    width = min(80, max(40, shutil.get_terminal_size((100, 30)).columns - 10))
    height = 15
    markers = ["\u25cf", "\u25c6", "\u25a0", "\u25b2", "\u25bc", "\u2605", "\u271a"]

    all_samples = [_sample_curve(e, xmin, xmax, width) for e in exprs]
    all_valid = [y for s in all_samples for _, y in s if y is not None]
    if not all_valid: raise ValueError("no valid points to plot")
    ymin, ymax = _auto_range(all_valid, ymin, ymax)
    if ymax <= ymin: raise ValueError("ymax must be > ymin")
    pad = (ymax - ymin) * 0.05
    ymin -= pad; ymax += pad

    grid = [[" "] * width for _ in range(height)]

    y0 = None
    if ymin <= 0 <= ymax:
        y0 = height - 1 - int((0 - ymin) / (ymax - ymin) * (height - 1))
        y0 = max(0, min(height - 1, y0))
        for c in range(width): grid[y0][c] = "\u2500"
    x0 = None
    if xmin <= 0 <= xmax:
        x0 = int((0 - xmin) / (xmax - xmin) * (width - 1))
        for r in range(height): grid[r][x0] = "\u2502"

    for ci, samples in enumerate(all_samples):
        marker = markers[ci % len(markers)]
        for i, (x, y) in enumerate(samples):
            if y is None: continue
            if y < ymin or y > ymax: continue
            row = height - 1 - int((y - ymin) / (ymax - ymin) * (height - 1))
            row = max(0, min(height - 1, row))
            cur = grid[row][i]
            if cur == " " or cur in "\u2500\u2502":
                grid[row][i] = marker
            elif cur != marker:
                grid[row][i] = "\u2573"

    print()
    label_w = 10
    for r in range(height):
        y_val = ymax - (ymax - ymin) * r / (height - 1)
        label = f"{y_val:>{label_w}.4g}"
        print(f"  {DGRAY}{label} \u2502{RESET} " + "".join(grid[r]))
    print(f"  {' ' * label_w} \u2514" + "\u2500" * (width + 2))
    xlabel = f"{xmin:<10.4g}{(' ' * max(0, width - 20))}{xmax:>10.4g}"
    print(f"  {' ' * (label_w + 2)}{xlabel}")

    if len(exprs) == 1:
        print(f"  {DGRAY}  y = {exprs[0]}   over x \u2208 [{xmin:g}, {xmax:g}]{RESET}")
    else:
        parts = [f"{markers[i]} {e}" for i, e in enumerate(exprs)]
        print(f"  {DGRAY}  " + "   ".join(parts) + f"   over x \u2208 [{xmin:g}, {xmax:g}]{RESET}")
    print()


SVG_DIR = os.path.expanduser("~/Downloads/PYCalc")

APP_SHORTCUTS = {
    "default":     None,
    "preview":     "Preview",
    "gapplin":     "Gapplin",
    "quicklook":   None,
    "illustrator": "Adobe Illustrator",
    "ai":          "Adobe Illustrator",
    "photoshop":   "Adobe Photoshop 2024",
    "figma":       "Figma",
    "inkscape":    "Inkscape",
    "chrome":      "Google Chrome",
    "safari":      "Safari",
    "firefox":     "Firefox",
    "edge":        "Microsoft Edge",
    "vscode":      "Visual Studio Code",
    "code":        "Visual Studio Code",
    "sublime":     "Sublime Text",
    "browser":     "Safari",
}


def _ensure_svg_dir():
    os.makedirs(SVG_DIR, exist_ok=True)
    return SVG_DIR


def list_svgs(limit=30):
    d = _ensure_svg_dir()
    entries = []
    for f in os.listdir(d):
        if f.lower().endswith(".svg"):
            full = os.path.join(d, f)
            try: entries.append((os.path.getmtime(full), full))
            except OSError: pass
    entries.sort(reverse=True)
    return entries[:limit]


def open_svg(path, app=None):
    import subprocess
    sysname = sys.platform
    if app is None or app.lower() in ("default", "quicklook"):
        if sysname == "darwin":
            subprocess.run(["open", path], check=False)
        elif sysname.startswith("win"):
            try:
                os.startfile(path)  # type: ignore[attr-defined]
            except Exception as e:
                raise ValueError(f"could not open: {e}")
        else:
            subprocess.run(["xdg-open", path], check=False)
        return
    name = APP_SHORTCUTS.get(app.lower(), app)
    if name is None:
        open_svg(path, None)
        return
    if sysname == "darwin":
        r = subprocess.run(["open", "-a", name, path], check=False,
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise ValueError(f"could not open with '{name}': {r.stderr.strip() or 'app not found'}")
    else:
        open_svg(path, None)


def generate_svg(exprs, xmin, xmax, ymin, ymax, filename):
    W, H = 900, 600
    ML, MR, MT, MB = 80, 40, 60, 70
    plot_w = W - ML - MR
    plot_h = H - MT - MB
    COLORS = ["#e74c3c", "#3498db", "#2ecc71", "#9b59b6", "#f39c12",
              "#1abc9c", "#34495e", "#e67e22"]

    samples_per = [_sample_curve(e, xmin, xmax, 600) for e in exprs]
    all_valid = [y for s in samples_per for _, y in s if y is not None]
    if not all_valid: raise ValueError("no valid points to plot")
    ymin, ymax = _auto_range(all_valid, ymin, ymax)
    if ymax <= ymin: ymax = ymin + 1

    def nice_ticks(lo, hi, count=8):
        rng = hi - lo
        if rng <= 0: return [lo]
        raw = rng / count
        mag = 10 ** math.floor(math.log10(raw))
        step = mag
        for m in (1, 2, 5, 10):
            if rng / (m * mag) <= count * 1.5:
                step = m * mag; break
        start = math.ceil(lo / step) * step
        ticks = []; t = start
        while t <= hi + step * 1e-6:
            ticks.append(round(t, 12)); t += step
        return ticks

    xticks = nice_ticks(xmin, xmax)
    yticks = nice_ticks(ymin, ymax)
    def xpx(x): return ML + (x - xmin) / (xmax - xmin) * plot_w
    def ypx(y): return MT + (1 - (y - ymin) / (ymax - ymin)) * plot_h

    L = []
    L.append('<?xml version="1.0" encoding="UTF-8"?>')
    L.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    L.append(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
    L.append(f'<text x="{W//2}" y="30" text-anchor="middle" font-family="Georgia,serif" font-size="20" fill="#2c3e50">PYCalc plot</text>')

    for xt in xticks:
        px = xpx(xt)
        L.append(f'<line x1="{px:.2f}" y1="{MT}" x2="{px:.2f}" y2="{MT+plot_h}" stroke="#ecf0f1" stroke-width="1"/>')
    for yt in yticks:
        py = ypx(yt)
        L.append(f'<line x1="{ML}" y1="{py:.2f}" x2="{ML+plot_w}" y2="{py:.2f}" stroke="#ecf0f1" stroke-width="1"/>')

    if ymin <= 0 <= ymax:
        py0 = ypx(0)
        L.append(f'<line x1="{ML}" y1="{py0:.2f}" x2="{ML+plot_w}" y2="{py0:.2f}" stroke="#2c3e50" stroke-width="1.5"/>')
    if xmin <= 0 <= xmax:
        px0 = xpx(0)
        L.append(f'<line x1="{px0:.2f}" y1="{MT}" x2="{px0:.2f}" y2="{MT+plot_h}" stroke="#2c3e50" stroke-width="1.5"/>')

    L.append(f'<rect x="{ML}" y="{MT}" width="{plot_w}" height="{plot_h}" fill="none" stroke="#bdc3c7" stroke-width="1"/>')

    for xt in xticks:
        px = xpx(xt)
        L.append(f'<line x1="{px:.2f}" y1="{MT+plot_h}" x2="{px:.2f}" y2="{MT+plot_h+5}" stroke="#2c3e50"/>')
        L.append(f'<text x="{px:.2f}" y="{MT+plot_h+20}" text-anchor="middle" font-family="Menlo,monospace" font-size="11" fill="#2c3e50">{xt:g}</text>')
    for yt in yticks:
        py = ypx(yt)
        L.append(f'<line x1="{ML-5}" y1="{py:.2f}" x2="{ML}" y2="{py:.2f}" stroke="#2c3e50"/>')
        L.append(f'<text x="{ML-10}" y="{py+4:.2f}" text-anchor="end" font-family="Menlo,monospace" font-size="11" fill="#2c3e50">{yt:g}</text>')

    for ci, samples in enumerate(samples_per):
        color = COLORS[ci % len(COLORS)]
        segs = []; cur = []
        for x, y in samples:
            if y is None or y < ymin or y > ymax:
                if len(cur) >= 2: segs.append(cur)
                cur = []
            else:
                cur.append((xpx(x), ypx(y)))
        if len(cur) >= 2: segs.append(cur)
        for seg in segs:
            d = "M " + " L ".join(f"{a:.2f} {b:.2f}" for a, b in seg)
            L.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round"/>')

    lx, ly = ML + 12, MT + 15
    for ci, expr in enumerate(exprs):
        color = COLORS[ci % len(COLORS)]
        L.append(f'<rect x="{lx}" y="{ly-9}" width="16" height="11" fill="{color}"/>')
        L.append(f'<text x="{lx+22}" y="{ly}" font-family="Menlo,monospace" font-size="12" fill="#2c3e50">{expr}</text>')
        ly += 20

    L.append('</svg>')
    with open(filename, "w") as f:
        f.write("\n".join(L))
    return os.path.abspath(filename)

# ============================================================
# STEPS
# ============================================================
def show_steps(expr):
    print()
    print(f"  {BLUE}STEPS{RESET}   {DGRAY}for {WHITE}{expr}{RESET}")
    print()
    norm = normalize(expr)
    print(f"  {DGRAY}1. Input{RESET}        {WHITE}{expr}{RESET}")
    if norm != expr:
        print(f"  {DGRAY}2. Normalize{RESET}    {WHITE}{norm}{RESET}")
    try: prep = prepare(expr)
    except Exception as e:
        print(f"  {RED}✕ parse failed: {e}{RESET}"); print(); return
    print(f"  {DGRAY}3. Parse{RESET}        {WHITE}{prep}{RESET}")
    try:
        result = safe_eval(expr, {})
        print(f"  {DGRAY}4. Evaluate{RESET}     {WHITE}{format_number(result)}{RESET}")
    except Exception as e:
        print(f"  {RED}4. Error: {e}{RESET}")
    print()

# ============================================================
# HISTORY / SESSIONS
# ============================================================
def show_history():
    print(); print(f"  {BLUE}HISTORY{RESET}"); print()
    if not READLINE_OK:
        print(f"  {DGRAY}(readline not available){RESET}"); print(); return
    n = readline.get_current_history_length()
    start = max(1, n - 19)
    for i in range(start, n + 1):
        item = readline.get_history_item(i)
        if item is None: continue
        print(f"  {DGRAY}{i:>3}{RESET}  {WHITE}{item}{RESET}")
    print()
    print(f"  {DGRAY}Use {WHITE}!n{DGRAY} to rerun entry n.{RESET}")
    print()

def recall_history(n):
    if not READLINE_OK: raise ValueError("history not available")
    total = readline.get_current_history_length()
    if not (1 <= n <= total): raise ValueError(f"no history entry {n}")
    return readline.get_history_item(n)


def save_session(name):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9\-]*", name):
        raise ValueError("invalid session name")
    os.makedirs(SESSION_DIR, exist_ok=True)
    path = os.path.join(SESSION_DIR, name + ".json")
    with open(path, "w") as f:
        json.dump({"vars": {k: (v if not isinstance(v, complex) else [v.real, v.imag])
                            for k, v in STATE["var_cache"].items()},
                   "user_funcs": STATE["user_funcs"]}, f, indent=2)
    print(f"  {GREEN}✓{RESET} saved session → {WHITE}{path}{RESET}")

def load_session(name):
    path = os.path.join(SESSION_DIR, name + ".json")
    if not os.path.exists(path): raise ValueError(f"no session '{name}'")
    with open(path) as f: data = json.load(f)
    for k, v in data.get("vars", {}).items():
        if isinstance(v, list) and len(v) == 2: v = complex(v[0], v[1])
        STATE["var_cache"][k] = v
    STATE["user_funcs"].update(data.get("user_funcs", {}))
    print(f"  {GREEN}✓{RESET} loaded session ← {WHITE}{path}{RESET}")

def list_sessions():
    if not os.path.isdir(SESSION_DIR): return []
    return sorted(f[:-5] for f in os.listdir(SESSION_DIR) if f.endswith(".json"))

# ============================================================
# INFO SCREENS
# ============================================================
def _help_essentials():
    return [
        f"{LGRAY}Just type maths.{RESET}",
        f"  {WHITE}2 + 3{RESET}        add",
        f"  {WHITE}10 - 4{RESET}       subtract",
        f"  {WHITE}6 * 7{RESET}        multiply",
        f"  {WHITE}20 / 5{RESET}       divide",
        f"  {WHITE}2 ^ 10{RESET}       powers  (2^10 = 1024)",
        f"  {WHITE}17 % 5{RESET}       remainder (2)",
        "",
        f"{LGRAY}Multiplication shortcuts{RESET}",
        f"  {WHITE}2x{RESET}           means 2 * x",
        f"  {WHITE}2(3+1){RESET}       means 2 * (3+1)",
        f"  {WHITE}xy{RESET}           means x * y",
        "",
        f"{LGRAY}Equations{RESET}",
        f"  {WHITE}y = 3x + 2{RESET}   you'll be asked for x",
        "",
        f"{LGRAY}Constants{RESET}",
        f"  {WHITE}pi{RESET}  or  {WHITE}π{RESET}      3.14159…",
        f"  {WHITE}e{RESET}               2.71828…",
        f"  {WHITE}~c{RESET}              speed of light (rainbow reveal)",
        f"  {WHITE}~e{RESET}              Euler's number (rainbow reveal)",
        "",
        f"{LGRAY}Answer reuse{RESET}",
        f"  {WHITE}ans{RESET}             previous result",
        f"  {WHITE}ans-q{RESET}           rerun the previous formula",
        f"  {WHITE}ans-q = x{RESET}       rerun, re-prompt only x",
    ]


def _help_advanced(advanced):
    if advanced:
        return [
            f"{LGRAY}Operators{RESET}",
            f"  {WHITE}+  -  *  /  %  ^{RESET}      ^ is right-assoc (2^3^2 = 512)",
            f"  {WHITE}unary -{RESET}               -5, -(3+2)",
            "",
            f"{LGRAY}Implicit multiplication{RESET}",
            f"  {WHITE}2x   xy   2(x+1)   x(y+1)   2sin(x)   (x+1)(x-1){RESET}",
            "",
            f"{LGRAY}Advanced functions{RESET}  {DGRAY}(you have access){RESET}",
            f"  {WHITE}asin  acos  atan  sinh  cosh  tanh  log  ln  exp{RESET}",
            f"  {DGRAY}log is base-10; ln is natural. Angle mode set in settings.{RESET}",
            "",
            f"{LGRAY}Complex numbers{RESET}",
            f"  {WHITE}sqrt(-1){RESET}              → i",
            f"  {WHITE}(1 + i) * (1 - i){RESET}     → 2",
            f"  {WHITE}i^2{RESET}                   → -1",
            "",
            f"{LGRAY}Number bases{RESET}",
            f"  {WHITE}0xff  0b1010  0o17{RESET}    hex / bin / oct literals",
            f"  {WHITE}255 to hex{RESET}   {WHITE}255 to bin{RESET}   convert",
            f"  {WHITE}0xff to dec{RESET}           convert back",
            "",
            f"{LGRAY}Unit conversion{RESET}",
            f"  {WHITE}5 km to mi{RESET}    {WHITE}100 F to C{RESET}    {WHITE}2.5 kg to lb{RESET}",
            f"  {DGRAY}length · mass · time · volume · temperature (C/F/K){RESET}",
            "",
            f"{LGRAY}User functions{RESET}",
            f"  {WHITE}f(x) = x^2 + 1{RESET}           define",
            f"  {WHITE}g(x, y) = x^2 + y^2{RESET}      multi-arg",
            f"  {WHITE}f(3){RESET}                     call → 10",
            "",
            f"{LGRAY}Steps{RESET}",
            f"  {WHITE}?sqrt(16) + 3{RESET}            parse + eval stages",
            "",
            f"{LGRAY}History{RESET}",
            f"  {WHITE}history{RESET}                  list recent inputs",
            f"  {WHITE}!n{RESET}                       rerun entry n (e.g. {WHITE}!4{RESET})",
            "",
            f"{LGRAY}Sessions{RESET}",
            f"  {WHITE}save mylab{RESET}               save vars + user funcs",
            f"  {WHITE}load mylab{RESET}               restore them",
            f"  {DGRAY}stored in ~/.pycalc_sessions/{RESET}",
        ]
    return [
        f"{LGRAY}CLI tips{RESET}",
        f"  {WHITE}↑ / ↓{RESET}        browse previous inputs",
        f"  {WHITE}Ctrl-R{RESET}       search your history",
        f"  {WHITE}Tab{RESET}          autocomplete commands & functions",
        f"  {WHITE}Ctrl-C{RESET}       cancel current input",
        f"  {WHITE}Ctrl-D{RESET}       exit",
        "",
        f"{LGRAY}Handy extras{RESET}",
        f"  {WHITE}?expr{RESET}        show step-by-step parse + eval",
        f"  {WHITE}history{RESET}      list recent inputs, then !n to rerun",
        f"  {WHITE}save mylab{RESET}   remember variables for later",
        f"  {WHITE}load mylab{RESET}   bring them back",
        "",
        f"{LGRAY}Customise{RESET}",
        f"  {WHITE}settings{RESET}     colours · angle mode · animations · advanced mode",
        "",
        f"{DGRAY}Enable advanced mode in settings for the full reference.{RESET}",
    ]


def _help_graphing():
    return [
        f"{LGRAY}Single curve{RESET}",
        f"  {WHITE}plot(x, -5, 5){RESET}",
        f"  {WHITE}plot(x^2, -3, 3){RESET}",
        f"  {WHITE}plot(sin(x), -6.28, 6.28){RESET}",
        f"  {WHITE}plot(1/x, -5, 5){RESET}               auto-clips the asymptote",
        "",
        f"{LGRAY}Multiple curves{RESET}  {DGRAY}(separate with ;){RESET}",
        f"  {WHITE}plot(x; x^2; sin(x), -5, 5){RESET}",
        f"  {WHITE}plot(sin(x); cos(x), -6.28, 6.28){RESET}",
        f"  {DGRAY}Markers cycle: ● ◆ ■ ▲ ▼ ★ ✚   intersections show as ╳{RESET}",
        "",
        f"{LGRAY}Manual y-range{RESET}  {DGRAY}(4th and 5th args){RESET}",
        f"  {WHITE}plot(x^2, -3, 3, 0, 5){RESET}",
        f"  {WHITE}plot(sin(x), -6.28, 6.28, -2, 2){RESET}",
        "",
        f"{LGRAY}SVG export{RESET}",
        f"  {WHITE}svg(sin(x); cos(x), -6.28, 6.28){RESET}     to ~/Downloads/PYCalc/",
        f"  {WHITE}svg(x^2, -3, 3, 0, 5, parabola){RESET}       custom filename",
        f"  {WHITE}svg-list{RESET}                              browse recent 30",
        f"  {WHITE}svg-open 1{RESET}                            open #1 (system default)",
        f"  {WHITE}svg-open 1 -preview{RESET}                  open #1 with Preview",
        f"  {WHITE}svg-open 1 -illustrator{RESET}              open #1 with Illustrator",
        f"  {WHITE}svg 2 -gapplin{RESET}                       shorthand, with app",
        "",
        f"{LGRAY}Try these{RESET}",
        f"  {WHITE}plot(x, -5, 5){RESET}                diagonal",
        f"  {WHITE}plot(2x + 1, -5, 5){RESET}           line, slope 2",
        f"  {WHITE}plot(x^2, -3, 3){RESET}              parabola",
        f"  {WHITE}plot(sin(x), -6.28, 6.28){RESET}     one sine wave",
        f"  {WHITE}plot(1/x, -5, 5){RESET}              hyperbola",
        f"  {WHITE}plot(x^3 - 3x, -3, 3){RESET}         cubic",
        f"  {WHITE}plot(e^x, -2, 3){RESET}              exponential",
        f"  {WHITE}plot(x; -x; x^2/4, -5, 5){RESET}     three on one grid",
    ]


def _help_commands():
    return [
        f"  {WHITE}help{RESET}         this menu",
        f"  {WHITE}guide{RESET}        beginner's tour",
        f"  {WHITE}functions{RESET}    available functions",
        f"  {WHITE}constants{RESET}    mathematical constants",
        f"  {WHITE}vars{RESET}         cached variables & user functions",
        f"  {WHITE}settings{RESET}     settings menu",
        f"  {WHITE}history{RESET}      recent inputs (then {WHITE}!n{RESET} to rerun)",
        f"  {WHITE}save NAME{RESET}    save variables + user functions",
        f"  {WHITE}load NAME{RESET}    restore a saved session",
        f"  {WHITE}plot(...){RESET}    ASCII graph",
        f"  {WHITE}svg(...){RESET}     export an SVG",
        f"  {WHITE}svg-list{RESET}     browse recent SVGs",
        f"  {WHITE}svg-open N{RESET}   open SVG #N (add {WHITE}-app{RESET} to choose)",
        f"  {WHITE}?expr{RESET}        step-by-step breakdown",
        f"  {WHITE}clear{RESET}        redraw screen",
        f"  {WHITE}exit{RESET}         quit",
    ]


def _help_sections(advanced):
    return [
        ("essentials", "Essentials", _help_essentials()),
        ("advanced", "Advanced", _help_advanced(advanced)),
        ("graphing", "Graphing", _help_graphing()),
        ("commands", "Commands", _help_commands()),
    ]


def interactive_help(advanced):
    sections = _help_sections(advanced)
    all_keys = [k for k, _, _ in sections]
    expanded = set()

    while True:
        clear()
        logo()
        print()
        mode = "advanced" if advanced else "basic"
        print(f"  {BLUE}PYCalc help{RESET}   {DGRAY}• {mode} mode •{RESET}")
        print()
        divider()
        for i, (key, title, lines) in enumerate(sections, 1):
            marker = "▼" if key in expanded else "▶"
            print(f"  {BLUE}[{i}]{RESET} {marker} {WHITE}{title}{RESET}")
            if key in expanded:
                for line in lines:
                    print("       " + line)
                print()
        divider()
        print(f"  {DGRAY}[1-{len(sections)}] toggle section   [a] expand all   [c] collapse all   [b] back{RESET}")
        print()
        try:
            choice = input(prompt_choice()).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if choice in ("", "b", "q", "back"):
            return
        if choice == "a":
            expanded = set(all_keys); continue
        if choice == "c":
            expanded = set(); continue
        if choice.isdigit():
            n = int(choice)
            if 1 <= n <= len(sections):
                k = sections[n - 1][0]
                if k in expanded:
                    expanded.discard(k)
                else:
                    expanded.add(k)


def show_help():
    interactive_help(STATE["advanced"])


def show_guide():
    print()
    print(f"  {BLUE}Beginner's guide to PYCalc{RESET}")
    print()
    print(f"  {LGRAY}What is this?{RESET}")
    print("    PYCalc is a calculator that runs in your terminal.")
    print("    You type an expression, press Enter, and it calculates.")
    print()
    print(f"  {LGRAY}Your first calculation{RESET}")
    print("    At the blue ❯ prompt, type:")
    print(f"        {WHITE}2 + 3{RESET}")
    print("    and press Enter. You'll see:")
    print(f"        {WHITE}➔ Result: 5{RESET}")
    print()
    print(f"  {LGRAY}Using the result again{RESET}")
    print("    Type:")
    print(f"        {WHITE}ans * 4{RESET}")
    print("    and you'll get 20. 'ans' is your last answer.")
    print()
    print(f"  {LGRAY}Variables{RESET}")
    print("    To work with a variable, just use its name:")
    print(f"        {WHITE}y = 3x + 2{RESET}")
    print("    PYCalc will ask what x is. Enter a number,")
    print("    and it calculates y and remembers both.")
    print()
    print(f"  {LGRAY}Reusing formulas{RESET}")
    print("    After the last step, type:")
    print(f"        {WHITE}ans-q{RESET}")
    print("    and it runs the same formula again with the same variables.")
    print("    To change just x, type:")
    print(f"        {WHITE}ans-q = x{RESET}")
    print()
    print(f"  {LGRAY}CLI basics{RESET}")
    print("    ↑ / ↓       scroll through what you've typed before")
    print("    Tab         autocomplete commands (try typing 'he' + Tab)")
    print("    Ctrl-R      search your history")
    print("    Ctrl-C      cancel the current line")
    print("    Ctrl-D      exit PYCalc")
    print()
    print(f"  {LGRAY}Getting help inside PYCalc{RESET}")
    print(f"    {WHITE}help{RESET}        this reference (or advanced, if enabled)")
    print(f"    {WHITE}guide{RESET}       this beginner's tour")
    print(f"    {WHITE}functions{RESET}   list of functions you can use")
    print(f"    {WHITE}settings{RESET}    change colours, angle mode, advanced mode")
    print(f"    {WHITE}exit{RESET}        leave PYCalc")
    print()
    print(f"  {LGRAY}Common mistakes{RESET}")
    print("    * Don't type an '=' unless it's an equation (y = ...).")
    print("    * For powers use ^ (2^10), not **.")
    print("    * Multiplication needs no symbol: 2x, 3(4+1), xy all work.")
    print()

def show_constants():
    print(); print(f"  {BLUE}CONSTANTS{RESET}"); print()
    print(f"  {LGRAY}π{RESET}    {format_number(math.pi)}")
    print(f"  {LGRAY}e{RESET}    {format_number(EULER)}")
    print(f"  {LGRAY}~c{RESET}   {format_number(LIGHT_SPEED)} m/s")
    print(f"  {LGRAY}~e{RESET}   {format_number(EULER)} (with rainbow reveal)")
    print(f"  {LGRAY}i{RESET}    imaginary unit")
    print(f"  {LGRAY}ans{RESET}  {format_number(STATE['last_ans'])}")
    print()

def show_functions():
    print(); print(f"  {BLUE}FUNCTIONS{RESET}"); print()
    print(f"  {LGRAY}Basic{RESET}     " + "   ".join(sorted(BASIC_FUNCTIONS)))
    if STATE["advanced"]:
        print(f"  {LGRAY}Advanced{RESET}  " + "   ".join(sorted(ADVANCED_FUNCTIONS)))
    else:
        print(f"  {DGRAY}Advanced{RESET}  {DGRAY}(hidden — enable in settings){RESET}")
    if STATE["user_funcs"]:
        print(f"  {LGRAY}Yours{RESET}     " + "   ".join(sorted(STATE["user_funcs"])))
    print()
    print(f"  {DGRAY}Angle mode: {STATE['angle']} — change in settings.{RESET}")
    print()

def show_vars():
    print(); print(f"  {BLUE}VARIABLES{RESET}"); print()
    if not STATE["var_cache"]:
        print(f"  {DGRAY}(empty){RESET}")
    else:
        for k in sorted(STATE["var_cache"]):
            print(f"  {LGRAY}{k}{RESET} = {format_number(STATE['var_cache'][k])}")
    if STATE["user_funcs"]:
        print(); print(f"  {BLUE}USER FUNCTIONS{RESET}"); print()
        for n, s in sorted(STATE["user_funcs"].items()):
            print(f"  {LGRAY}{n}({', '.join(s['params'])}){RESET} = {WHITE}{s['body']}{RESET}")
    print()

# ============================================================
# SETTINGS
# ============================================================
def settings_menu():
    while True:
        clear(); logo(); print()
        print(f"  {BLUE}SETTINGS{RESET}"); divider()
        def row(key, label, val):
            print(f"  {WHITE}[{key:>2}]{RESET} {label:<26} {DGRAY}[{val}]{RESET}")
        row(1,  "Rainbow animation",  STATE["rainbow"])
        row(2,  "Theme",              STATE["theme"])
        row(3,  "Angle mode",         STATE["angle"])
        row(4,  "Advanced mode",      "on" if STATE["advanced"] else "off")
        row(5,  "Status line",        "on" if STATE["status_line"] else "off")
        row(6,  "Launch animation",   "on" if STATE["animations"] else "off")
        row(7,  "Show fractions",     "on" if STATE["fractions"] else "off")
        row(8,  "Clear variable cache", f"{len(STATE['var_cache'])} var(s)")
        row(9,  "Clear user functions", f"{len(STATE['user_funcs'])} func(s)")
        row(10, "List saved sessions", f"{len(list_sessions())} found")
        row(11, "Reset all settings", "—")
        print(f"  {WHITE}[ b]{RESET} Back")
        divider()
        try: choice = input(prompt_choice()).strip().lower()
        except (EOFError, KeyboardInterrupt): save_config(); return
        if choice in ("", "b", "q"): save_config(); return
        if choice == "1":
            order = ["auto", "on", "off"]
            STATE["rainbow"] = order[(order.index(STATE["rainbow"]) + 1) % 3]
        elif choice == "2":
            order = ["default", "dark", "mono", "none"]
            STATE["theme"] = order[(order.index(STATE["theme"]) + 1) % 4]
            apply_theme()
        elif choice == "3":
            STATE["angle"] = "deg" if STATE["angle"] == "rad" else "rad"
        elif choice == "4": STATE["advanced"] = not STATE["advanced"]
        elif choice == "5": STATE["status_line"] = not STATE["status_line"]
        elif choice == "6": STATE["animations"] = not STATE["animations"]
        elif choice == "7": STATE["fractions"] = not STATE["fractions"]
        elif choice == "8": STATE["var_cache"].clear()
        elif choice == "9": STATE["user_funcs"].clear()
        elif choice == "10":
            ss = list_sessions()
            print()
            if not ss: print(f"  {DGRAY}(no saved sessions){RESET}")
            else:
                for s in ss: print(f"  {LGRAY}•{RESET} {s}")
            input(f"  {DGRAY}Press Enter to continue…{RESET}")
        elif choice == "11":
            STATE.update({"rainbow":"auto","theme":"default","angle":"rad",
                          "advanced":False,"status_line":True,"animations":True,
                          "fractions":False})
            STATE["var_cache"].clear(); STATE["user_funcs"].clear()
            apply_theme()
        save_config()

# ============================================================
# STATUS LINE
# ============================================================
def print_status():
    if not STATE["status_line"]: return
    parts = [f"ans={format_number(STATE['last_ans'], _no_fraction=True)}", f"rainbow={STATE['rainbow']}"]
    if STATE["angle"] != "rad": parts.append(f"angle={STATE['angle']}")
    if STATE["advanced"]: parts.append("adv=on")
    if STATE["var_cache"]:
        vs = ", ".join(f"{k}={format_number(v)}" for k, v in list(STATE["var_cache"].items())[:4])
        parts.append(f"vars: {vs}")
    if STATE["user_funcs"]:
        parts.append("fns: " + ",".join(sorted(STATE["user_funcs"])))
    print(f"  {DGRAY}{' · '.join(parts)}{RESET}")

# ============================================================
# TAB COMPLETION
# ============================================================
def setup_completer():
    if not READLINE_OK: return
    base = ["help","guide","functions","constants","vars","settings","history",
            "save","load","plot","clear","exit","quit","rad","deg"]
    def completer(text, state):
        names = base + list(ALL_FUNC_NAMES) + list(CONSTANT_NAMES) + list(STATE["user_funcs"])
        opts = [n for n in names if n.startswith(text)]
        if state < len(opts): return opts[state]
        return None
    readline.set_completer(completer)
    try: readline.parse_and_bind("tab: complete")
    except Exception: pass

# ============================================================
# INPUT PROCESSING
# ============================================================
def process_input(raw):
    cleaned = raw.strip().replace("`", "")
    if not cleaned: return
    cmd = cleaned.lower()

    if cmd in ("exit", "quit"): raise SystemExit
    if cmd == "help":      show_help(); return
    if cmd == "guide":     show_guide(); return
    if cmd == "constants": show_constants(); return
    if cmd == "functions": show_functions(); return
    if cmd == "vars":      show_vars(); return
    if cmd == "clear":     header(); return
    if cmd == "settings":  settings_menu(); header(); return
    if cmd == "history":   show_history(); return

    if cmd == "deg":
        STATE["angle"] = "deg"; save_config()
        print(f"  {GREEN}✓{RESET} angle mode: {WHITE}deg{RESET}")
        return
    if cmd == "rad":
        STATE["angle"] = "rad"; save_config()
        print(f"  {GREEN}✓{RESET} angle mode: {WHITE}rad{RESET}")
        return

    m = re.fullmatch(r"save\s+(.+)", cmd)
    if m: save_session(m.group(1).strip()); return
    m = re.fullmatch(r"load\s+(.+)", cmd)
    if m: load_session(m.group(1).strip()); return

    m = re.fullmatch(r"!(\d+)", cleaned)
    if m:
        cleaned = recall_history(int(m.group(1)))
        print(f"  {DGRAY}↳ rerunning: {WHITE}{cleaned}{RESET}")

    if cleaned.startswith("?"):
        show_steps(cleaned[1:].strip()); return

    # plot(...) — multi-curve via ";"
    m = re.fullmatch(r"\s*plot\s*\(\s*(.+)\s*\)\s*", cleaned, re.DOTALL)
    if m:
        parts = split_top(m.group(1), ",")
        if len(parts) not in (3, 5):
            raise ValueError("usage: plot(expr[; expr...], xmin, xmax[, ymin, ymax])")
        exprs = split_top(parts[0], ";")
        try:
            xmin = float(safe_eval(parts[1], {}))
            xmax = float(safe_eval(parts[2], {}))
            ymin = float(safe_eval(parts[3], {})) if len(parts) == 5 else None
            ymax = float(safe_eval(parts[4], {})) if len(parts) == 5 else None
        except Exception as e:
            raise ValueError(f"invalid range: {e}")
        if xmax <= xmin: raise ValueError("xmax must be > xmin")
        do_plot(exprs, xmin, xmax, ymin, ymax)
        return

    # svg-list — list recent SVGs
    if cmd == "svg-list" or cmd == "svg list":
        entries = list_svgs(30)
        print()
        if not entries:
            print(f"  {DGRAY}No SVGs yet. Try: {WHITE}svg(sin(x), -3.14, 3.14){RESET}")
            print()
            return
        print(f"  {BLUE}RECENT SVGs{RESET}  {DGRAY}in ~/Downloads/PYCalc/{RESET}")
        print()
        for i, (mt, path) in enumerate(entries, 1):
            when = time.strftime("%Y-%m-%d %H:%M", time.localtime(mt))
            size = os.path.getsize(path)
            name = os.path.basename(path)
            print(f"  {DGRAY}{i:>3}{RESET}  {WHITE}{name:<32}{RESET} {DGRAY}{when}  {size:>7} B{RESET}")
        print()
        print(f"  {DGRAY}Open one:  {WHITE}svg-open N{RESET}  {DGRAY}or with a specific app:  {WHITE}svg-open N -illustrator{RESET}")
        print()
        return

    # svg-open N [app] — open a recent SVG
    m = re.fullmatch(r"\s*svg-open\s+(\d+)(?:\s+-?(\S+))?\s*", cleaned)
    if m:
        n = int(m.group(1))
        app = m.group(2) if m.group(2) else None
        entries = list_svgs(30)
        if not entries:
            raise ValueError("no SVGs to open")
        if n < 1 or n > len(entries):
            raise ValueError(f"choose a number between 1 and {len(entries)}")
        path = entries[n - 1][1]
        try:
            open_svg(path, app)
        except Exception as e:
            raise ValueError(str(e))
        app_label = app if app else "default"
        print(f"  {GREEN}\u2713{RESET} opening {WHITE}{os.path.basename(path)}{RESET} {DGRAY}with {app_label}{RESET}")
        return

    # shorthand: svg N [app]
    m = re.fullmatch(r"\s*svg\s+(\d+)(?:\s+-?(\S+))?\s*", cleaned)
    if m:
        n = int(m.group(1))
        app = m.group(2) if m.group(2) else None
        entries = list_svgs(30)
        if not entries:
            raise ValueError("no SVGs to open")
        if n < 1 or n > len(entries):
            raise ValueError(f"choose a number between 1 and {len(entries)}")
        path = entries[n - 1][1]
        open_svg(path, app)
        app_label = app if app else "default"
        print(f"  {GREEN}\u2713{RESET} opening {WHITE}{os.path.basename(path)}{RESET} {DGRAY}with {app_label}{RESET}")
        return

    # svg(...) — export SVG
    m = re.fullmatch(r"\s*svg\s*\(\s*(.+)\s*\)\s*", cleaned, re.DOTALL)
    if m:
        parts = split_top(m.group(1), ",")
        if len(parts) not in (3, 4, 5, 6):
            raise ValueError("usage: svg(expr[; expr...], xmin, xmax[, ymin, ymax][, filename])")
        exprs = split_top(parts[0], ";")
        try:
            xmin = float(safe_eval(parts[1], {}))
            xmax = float(safe_eval(parts[2], {}))
        except Exception as e:
            raise ValueError(f"invalid range: {e}")
        if xmax <= xmin: raise ValueError("xmax must be > xmin")
        ymin = ymax = None
        filename = None
        if len(parts) == 4:
            filename = parts[3]
        elif len(parts) == 5:
            ymin = float(safe_eval(parts[3], {}))
            ymax = float(safe_eval(parts[4], {}))
        elif len(parts) == 6:
            ymin = float(safe_eval(parts[3], {}))
            ymax = float(safe_eval(parts[4], {}))
            filename = parts[5]
        if filename is None:
            ts = time.strftime("%Y%m%d_%H%M%S")
            filename = f"plot_{ts}.svg"
        if not filename.lower().endswith(".svg"):
            filename += ".svg"
        if not os.path.isabs(filename) and os.sep not in filename and "/" not in filename:
            filename = os.path.join(_ensure_svg_dir(), filename)
        path = generate_svg(exprs, xmin, xmax, ymin, ymax, filename)
        print()
        print(f"  {GREEN}\u2713{RESET} saved {WHITE}{path}{RESET}")
        print(f"  {DGRAY}browse: {WHITE}svg-list{RESET}{DGRAY}   open last: {WHITE}svg-open 1{RESET}{DGRAY}   with app: {WHITE}svg-open 1 -illustrator{RESET}")
        print()
        return

    # standalone ~c / ~e reveals
    if re.fullmatch(r"~\s*[cC]", cleaned):
        reveal_constant("Speed of Light", f"{format_number(LIGHT_SPEED)} m / s"); return
    if re.fullmatch(r"~\s*[eE]", cleaned):
        reveal_constant("Euler's Number", format_number(EULER)); return

    # user function definition  f(x) = expr
    m = re.fullmatch(
        r"\s*([A-Za-z_][A-Za-z_0-9]*)\s*\(\s*([A-Za-z_][A-Za-z_0-9]*(?:\s*,\s*[A-Za-z_][A-Za-z_0-9]*)*)\s*\)\s*=\s*(.+)",
        cleaned)
    if m:
        if not STATE["advanced"]:
            raise ValueError("function definitions need advanced mode — type 'settings'")
        name = m.group(1)
        if name in ALL_FUNC_NAMES or name in CONSTANT_NAMES or name == "ans":
            raise ValueError(f"'{name}' is reserved")
        params = [p.strip() for p in m.group(2).split(",")]
        if len(set(params)) != len(params):
            raise ValueError("duplicate parameter names")
        body = m.group(3).strip()
        probe = {p: 1.0 for p in params}
        try: safe_eval(body, probe)
        except Exception as exc: raise ValueError(f"invalid body: {exc}")
        STATE["user_funcs"][name] = {"params": params, "body": body}
        save_config()
        print(f"  {GREEN}✓{RESET} {WHITE}{name}({', '.join(params)}){RESET} {DGRAY}defined{RESET}")
        return

    # unit conversion / base conversion via "to|in|->"
    m = re.fullmatch(
        r"\s*([\d\.\+\-\*/\(\)\s]+?)\s*([a-zA-Z]+)\s*(?:->|to|in)\s*([a-zA-Z0-9]+)\s*",
        cleaned)
    if m:
        left_str, from_u, target = m.group(1).strip(), m.group(2), m.group(3).lower()
        if target in BASE_TARGETS:
            val = safe_eval(left_str, {})
            if isinstance(val, complex) and abs(val.imag) > 1e-12:
                raise ValueError("cannot convert complex numbers between bases")
            n = int(val.real if isinstance(val, complex) else val)
            print()
            rainbow_result(f"➔ {n} → {BASE_TARGETS[target]}: ", format_base(n, BASE_TARGETS[target]), ctx="result")
            return
        try:
            val = float(safe_eval(left_str, {}))
        except Exception:
            val = None
        if val is not None:
            out = convert_units(val, from_u, target)
            print()
            rainbow_result(f"➔ {format_number(val, _no_fraction=True)} {from_u} = ", f"{format_number(out, _no_fraction=True)} {target}", ctx="result")
            return

    # ans-q
    forced = set()
    if re.fullmatch(r"\s*ans-q\s*", cleaned):
        if not STATE["last_expr"]: raise ValueError("no previous expression to replay")
        cleaned = STATE["last_expr"]
    else:
        m = re.fullmatch(r"\s*ans-q\s*=\s*(.+)", cleaned)
        if m:
            if not STATE["last_expr"]: raise ValueError("no previous expression to replay")
            for v in m.group(1).split(","):
                v = v.strip()
                if not v: continue
                if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", v):
                    raise ValueError(f"invalid variable name: {v}")
                forced.add(v)
            cleaned = STATE["last_expr"]

    STATE["forced_prompts"] = forced
    try:
        if "=" in cleaned:
            left, right = cleaned.split("=", 1)
            if not left.strip() or not right.strip():
                raise ValueError("incomplete equation")
            calculate_equation(left, right); return
        result = safe_eval(cleaned, {})
        STATE["last_ans"] = result
        STATE["last_expr"] = cleaned
        print()
        rainbow_result("➔ Result: ", format_number(result), ctx="result")
    finally:
        STATE["forced_prompts"] = set()

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


def _shutdown():
    import signal
    # Ignore any further SIGINT/SIGTERM so Ctrl-C during shutdown is a no-op
    try:
        signal.signal(signal.SIGINT,  signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    except Exception:
        pass
    try:
        print()
    except Exception:
        pass
    try:
        print("\n  " + DGRAY + "Goodbye." + RESET)
    except Exception:
        pass
    try:
        save_config()
    except Exception:
        pass


def _enable_windows_vt():
    """Enable ANSI escape sequence handling on Windows consoles."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # -11 = STD_OUTPUT_HANDLE, 7 = PROCESSED | WRAP_AT_EOL | VIRTUAL_TERMINAL
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


def _color_supported():
    """Return False if we should strip ANSI (env var or unsupported console)."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("PYCALC_NO_COLOR"):
        return False
    return True


def _strip_ansi_if_needed():
    if _color_supported():
        return
    # Override every theme with empty strings so nothing prints escape codes
    for preset in THEME_PRESETS.values():
        for k in list(preset.keys()):
            if k == "RAINBOW":
                preset[k] = [""] * 7
            else:
                preset[k] = ""


def main():
    load_config()
    _enable_windows_vt()
    _strip_ansi_if_needed()
    apply_theme()
    if is_first_run():
        first_run_intro()
    setup_completer()
    header(animate=True)
    while True:
        if STATE["status_line"]:
            print_status()
        print()
        try:
            user_input = input(prompt_main())
        except (EOFError, KeyboardInterrupt):
            _shutdown()
            return
        try:
            process_input(user_input)
        except SystemExit:
            _shutdown()
            return
        except Exception as exc:
            try:
                print("\n  " + RED + "\u2715" + RESET + " " + str(exc))
            except Exception:
                pass


if __name__ == "__main__":
    main()
