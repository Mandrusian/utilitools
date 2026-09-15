#!/usr/bin/env python3
"""UnitForge — terminal unit & dimensional analysis engine."""

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
    _HISTFILE = os.path.expanduser("~/.unitforge_history")
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
        _HISTFILE = os.path.expanduser("~/.unitforge_history")
        try: readline.read_history_file(_HISTFILE)
        except (FileNotFoundError, OSError): pass
    except ImportError:
        pass

def _paint(s):
    if not READLINE_OK: return s
    return re.sub(r"\x1b\[[0-9;]*m", lambda m: "\001" + m.group() + "\002", s)

def prompt_main():   return _paint(f"  {BLUE}\u276f{RESET} ")
def prompt_choice(): return _paint(f"  {BLUE}\u276f{RESET} ")

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
# UNITS
# ============================================================
# Each entry: name -> (dims_dict, factor_to_SI)
# Base dimensions: M mass, L length, T time, I current, K temp,
#                  N amount, J luminous intensity, $ currency
UNITS = {
    # --- SI base ---
    "m":    ({"L": 1}, 1.0),
    "kg":   ({"M": 1}, 1.0),
    "s":    ({"T": 1}, 1.0),
    "A":    ({"I": 1}, 1.0),
    "K":    ({"K": 1}, 1.0),
    "mol":  ({"N": 1}, 1.0),
    "cd":   ({"J": 1}, 1.0),
    # --- length ---
    "km":   ({"L": 1}, 1000.0),
    "cm":   ({"L": 1}, 0.01),
    "mm":   ({"L": 1}, 0.001),
    "um":   ({"L": 1}, 1e-6),
    "nm":   ({"L": 1}, 1e-9),
    "pm":   ({"L": 1}, 1e-12),
    "mi":   ({"L": 1}, 1609.344),
    "yd":   ({"L": 1}, 0.9144),
    "ft":   ({"L": 1}, 0.3048),
    "in":   ({"L": 1}, 0.0254),
    "nmi":  ({"L": 1}, 1852.0),
    "ly":   ({"L": 1}, 9.4607304725808e15),
    "au":   ({"L": 1}, 1.495978707e11),
    "pc":   ({"L": 1}, 3.0856775814913673e16),
    # --- mass ---
    "g":    ({"M": 1}, 0.001),
    "mg":   ({"M": 1}, 1e-6),
    "ug":   ({"M": 1}, 1e-9),
    "t":    ({"M": 1}, 1000.0),
    "tonne":({"M": 1}, 1000.0),
    "lb":   ({"M": 1}, 0.45359237),
    "oz":   ({"M": 1}, 0.028349523125),
    "st":   ({"M": 1}, 6.35029318),
    # --- time ---
    "ms":   ({"T": 1}, 0.001),
    "us":   ({"T": 1}, 1e-6),
    "ns":   ({"T": 1}, 1e-9),
    "min":  ({"T": 1}, 60.0),
    "h":    ({"T": 1}, 3600.0),
    "hr":   ({"T": 1}, 3600.0),
    "day":  ({"T": 1}, 86400.0),
    "wk":   ({"T": 1}, 604800.0),
    "yr":   ({"T": 1}, 31557600.0),
    # --- volume ---
    "L":    ({"L": 3}, 0.001),
    "l":    ({"L": 3}, 0.001),
    "mL":   ({"L": 3}, 1e-6),
    "ml":   ({"L": 3}, 1e-6),
    "gal":  ({"L": 3}, 0.003785411784),
    "qt":   ({"L": 3}, 0.000946352946),
    "pt":   ({"L": 3}, 0.000473176473),
    "cup":  ({"L": 3}, 0.0002365882365),
    "floz": ({"L": 3}, 2.95735295625e-5),
    "tbsp": ({"L": 3}, 1.47867647813e-5),
    "tsp":  ({"L": 3}, 4.92892159375e-6),
    "bbl":  ({"L": 3}, 0.158987294928),
    # --- derived SI ---
    "N":    ({"M": 1, "L": 1, "T": -2}, 1.0),
    "J":    ({"M": 1, "L": 2, "T": -2}, 1.0),
    "W":    ({"M": 1, "L": 2, "T": -3}, 1.0),
    "Pa":   ({"M": 1, "L": -1, "T": -2}, 1.0),
    "Hz":   ({"T": -1}, 1.0),
    "V":    ({"M": 1, "L": 2, "T": -3, "I": -1}, 1.0),
    "Wb":   ({"M": 1, "L": 2, "T": -2, "I": -1}, 1.0),
    "T":    ({"M": 1, "T": -2, "I": -1}, 1.0),
    "H":    ({"M": 1, "L": 2, "T": -2, "I": -2}, 1.0),
    "S":    ({"M": -1, "L": -2, "T": 3, "I": 2}, 1.0),
    "Bq":   ({"T": -1}, 1.0),
    "Gy":   ({"L": 2, "T": -2}, 1.0),
    "kat":  ({"N": 1, "T": -1}, 1.0),
    "lx":   ({"J": 1, "L": -2}, 1.0),
    # --- angle (dimensionless) ---
    "rad":  ({}, 1.0),
    "deg":  ({}, math.pi / 180.0),
    "grad": ({}, math.pi / 200.0),
    "turn": ({}, 2 * math.pi),
    # --- speed ---
    "mph":  ({"L": 1, "T": -1}, 0.44704),
    "kph":  ({"L": 1, "T": -1}, 1000.0 / 3600.0),
    "knot": ({"L": 1, "T": -1}, 0.5144444444),
    "kn":   ({"L": 1, "T": -1}, 0.5144444444),
    # --- pressure ---
    "atm":  ({"M": 1, "L": -1, "T": -2}, 101325.0),
    "bar":  ({"M": 1, "L": -1, "T": -2}, 100000.0),
    "mbar": ({"M": 1, "L": -1, "T": -2}, 100.0),
    "psi":  ({"M": 1, "L": -1, "T": -2}, 6894.757293168),
    "torr": ({"M": 1, "L": -1, "T": -2}, 133.32236842105),
    "mmHg": ({"M": 1, "L": -1, "T": -2}, 133.322387415),
    # --- energy ---
    "cal":  ({"M": 1, "L": 2, "T": -2}, 4.184),
    "kcal": ({"M": 1, "L": 2, "T": -2}, 4184.0),
    "eV":   ({"M": 1, "L": 2, "T": -2}, 1.602176634e-19),
    "kWh":  ({"M": 1, "L": 2, "T": -2}, 3.6e6),
    "BTU":  ({"M": 1, "L": 2, "T": -2}, 1055.05585262),
    "erg":  ({"M": 1, "L": 2, "T": -2}, 1e-7),
    # --- power ---
    "hp":   ({"M": 1, "L": 2, "T": -3}, 745.6998715823),
    # --- currency (offline placeholder rates against USD) ---
    "USD":  ({"$": 1}, 1.0),
    "EUR":  ({"$": 1}, 1.08),
    "GBP":  ({"$": 1}, 1.27),
    "JPY":  ({"$": 1}, 0.0067),
    "CAD":  ({"$": 1}, 0.73),
    "AUD":  ({"$": 1}, 0.66),
    "CHF":  ({"$": 1}, 1.12),
    "CNY":  ({"$": 1}, 0.14),
    "INR":  ({"$": 1}, 0.012),
    "KRW":  ({"$": 1}, 0.00075),
    "MXN":  ({"$": 1}, 0.058),
    "BRL":  ({"$": 1}, 0.20),
    "ZAR":  ({"$": 1}, 0.055),
    "SEK":  ({"$": 1}, 0.095),
    "NOK":  ({"$": 1}, 0.092),
}

UNIT_ALIASES = {
    "meter":"m","meters":"m","metre":"m","metres":"m",
    "kilometer":"km","kilometers":"km","kilometre":"km","kilometres":"km",
    "centimeter":"cm","centimeters":"cm","centimetre":"cm","centimetres":"cm",
    "millimeter":"mm","millimeters":"mm","millimetre":"mm","millimetres":"mm",
    "mile":"mi","miles":"mi","foot":"ft","feet":"ft","inch":"in","inches":"in",
    "yard":"yd","yards":"yd","kilogram":"kg","kilograms":"kg","kilo":"kg","kilos":"kg",
    "gram":"g","grams":"g","pound":"lb","pounds":"lb","lbs":"lb",
    "ounce":"oz","ounces":"oz","second":"s","seconds":"s","sec":"s","secs":"s",
    "millisecond":"ms","milliseconds":"ms","microsecond":"us","microseconds":"us",
    "minute":"min","minutes":"min","hour":"h","hours":"h","hrs":"h",
    "week":"wk","weeks":"wk","year":"yr","years":"yr",
    "liter":"L","litre":"L","liters":"L","litres":"L",
    "milliliter":"mL","millilitre":"mL","milliliters":"mL","millilitres":"mL",
    "gallon":"gal","gallons":"gal","quart":"qt","quarts":"qt","pint":"pt","pints":"pt",
    "tablespoon":"tbsp","tablespoons":"tbsp","teaspoon":"tsp","teaspoons":"tsp",
    "celsius":"C","centigrade":"C","fahrenheit":"F","kelvin":"K",
    "joule":"J","joules":"J","watt":"W","watts":"W","newton":"N","newtons":"N",
    "pascal":"Pa","pascals":"Pa","hertz":"Hz","volt":"V","volts":"V",
    "amp":"A","amps":"A","ampere":"A","amperes":"A",
    "degree":"deg","degrees":"deg","radian":"rad","radians":"rad",
    "usd":"USD","eur":"EUR","gbp":"GBP","jpy":"JPY",
    "cad":"CAD","aud":"AUD","chf":"CHF","cny":"CNY","inr":"INR",
}

# Temperature handled specially (affine, not linear)
TEMP_UNITS = {"C", "F", "K", "R"}
TEMP_NAMES = {
    "c":"C","celsius":"C","centigrade":"C",
    "f":"F","fahrenheit":"F",
    "k":"K","kelvin":"K",
    "r":"R","rankine":"R",
}

def _canon_unit(u):
    u = u.strip()
    if u in UNITS: return u
    if u in TEMP_UNITS: return u
    lower = u.lower()
    if lower in TEMP_NAMES: return TEMP_NAMES[lower]
    if lower in UNIT_ALIASES: return UNIT_ALIASES[lower]
    return u

# ============================================================
# QUANTITY
# ============================================================
class Quantity:
    __slots__ = ("value", "dims")
    def __init__(self, value, dims):
        self.value = float(value)
        self.dims = {k: v for k, v in dims.items() if v != 0}
    def __mul__(self, other):
        if isinstance(other, Quantity):
            return Quantity(self.value * other.value, _add_dims(self.dims, other.dims))
        return Quantity(self.value * other, dict(self.dims))
    def __rmul__(self, other):
        return Quantity(self.value * other, dict(self.dims))
    def __truediv__(self, other):
        if isinstance(other, Quantity):
            return Quantity(self.value / other.value, _sub_dims(self.dims, other.dims))
        return Quantity(self.value / other, dict(self.dims))
    def __rtruediv__(self, other):
        return Quantity(other / self.value, {k: -v for k, v in self.dims.items()})
    def __add__(self, other):
        if isinstance(other, Quantity):
            if self.dims != other.dims:
                raise ValueError(_dim_mismatch_msg(self.dims, other.dims))
            return Quantity(self.value + other.value, dict(self.dims))
        if self.dims: raise ValueError("cannot add scalar to a unit-bearing quantity")
        return Quantity(self.value + other, {})
    def __radd__(self, other):
        return self.__add__(other)
    def __sub__(self, other):
        if isinstance(other, Quantity):
            if self.dims != other.dims:
                raise ValueError(_dim_mismatch_msg(self.dims, other.dims))
            return Quantity(self.value - other.value, dict(self.dims))
        if self.dims: raise ValueError("cannot subtract scalar from a unit-bearing quantity")
        return Quantity(self.value - other, {})
    def __rsub__(self, other):
        if self.dims: raise ValueError("cannot subtract a unit-bearing quantity from a scalar")
        return Quantity(other - self.value, {})
    def __pow__(self, other):
        if not isinstance(other, (int, float)):
            raise ValueError("exponent must be a number")
        return Quantity(self.value ** other, {k: v * other for k, v in self.dims.items()})
    def __neg__(self): return Quantity(-self.value, dict(self.dims))
    def __pos__(self): return self
    def __repr__(self):
        return f"Quantity({self.value}, {self.dims})"


def _add_dims(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0) + v
        if out[k] == 0: del out[k]
    return out

def _sub_dims(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0) - v
        if out[k] == 0: del out[k]
    return out

BASE_ORDER = ("M", "L", "T", "I", "K", "N", "J", "$")
BASE_NAMES = {"M":"kg","L":"m","T":"s","I":"A","K":"K","N":"mol","J":"cd","$":"$"}

def _dims_str(dims):
    if not dims: return "dimensionless"
    num = []; den = []
    for k in BASE_ORDER:
        e = dims.get(k, 0)
        if e == 0: continue
        u = BASE_NAMES[k]
        if e > 0:
            num.append(u if e == 1 else f"{u}^{_fmt_exp(e)}")
        else:
            den.append(u if e == -1 else f"{u}^{_fmt_exp(-e)}")
    n = "·".join(num) if num else "1"
    if den:
        return f"{n}/{'·'.join(den)}"
    return n

def _fmt_exp(e):
    if isinstance(e, float) and e.is_integer(): return str(int(e))
    return f"{e:g}"

def _dim_mismatch_msg(a, b):
    return f"dimension mismatch: {_dims_str(a)} vs {_dims_str(b)}"

# ============================================================
# PARSING
# ============================================================
_TOK_RE = re.compile(r"""
    (?P<ws>\s+)
  | (?P<num>(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)
  | (?P<id>[A-Za-z_$][A-Za-z_0-9]*)
  | (?P<op>\*\*|[+\-*/^()·×÷])
""", re.X)

def _tokenize(s):
    toks = []
    pos = 0
    while pos < len(s):
        m = _TOK_RE.match(s, pos)
        if not m:
            raise ValueError(f"unexpected character: {s[pos]!r}")
        pos = m.end()
        kind = m.lastgroup
        val = m.group()
        if kind == "ws": continue
        if kind == "op":
            val = {"·":"*", "×":"*", "÷":"/"}.get(val, val)
        toks.append((kind, val))
    return toks

def _ends_value(k, v):
    return k in ("num", "id") or (k == "op" and v == ")")

def _starts_value(k, v):
    return k in ("num", "id") or (k == "op" and v == "(")

def _build_py_expr(tokens):
    out = []
    prev = None
    for k, v in tokens:
        if prev is not None and _ends_value(*prev) and _starts_value(k, v):
            out.append("*")
        if k == "op" and v == "^":
            out.append("**")
        else:
            out.append(v)
        prev = (k, v)
    return " ".join(out)

def _eval_ast(node, ns):
    import ast
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body, ns)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in ns: return ns[node.id]
        raise ValueError(f"unknown unit: '{node.id}'")
    if isinstance(node, ast.BinOp):
        l = _eval_ast(node.left, ns)
        r = _eval_ast(node.right, ns)
        if isinstance(node.op, ast.Add):  return l + r
        if isinstance(node.op, ast.Sub):  return l - r
        if isinstance(node.op, ast.Mult): return l * r
        if isinstance(node.op, ast.Div):  return l / r
        if isinstance(node.op, ast.Pow):  return l ** r
        raise ValueError("unsupported operator")
    if isinstance(node, ast.UnaryOp):
        v = _eval_ast(node.operand, ns)
        if isinstance(node.op, ast.USub): return -v
        if isinstance(node.op, ast.UAdd): return +v
    raise ValueError("unsupported expression")

def _unit_namespace():
    """Build namespace of {unit_name: Quantity(factor, dims)}."""
    ns = {}
    for name, (dims, factor) in UNITS.items():
        if name in TEMP_UNITS: continue   # temps handled separately
        ns[name] = Quantity(factor, dims)
    return ns

_UNIT_NS = _unit_namespace()

def eval_quantity(expr):
    """Parse and evaluate a quantity expression."""
    expr = expr.strip()
    if not expr:
        raise ValueError("empty expression")
    # Simple numeric-only fast path
    try:
        v = float(expr)
        return Quantity(v, {})
    except ValueError:
        pass
    tokens = _tokenize(expr)
    py = _build_py_expr(tokens)
    import ast
    try:
        tree = ast.parse(py, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"could not parse: {e.msg}")
    return _eval_ast(tree, _UNIT_NS)

# ============================================================
# TEMPERATURE
# ============================================================
def _temp_to_celsius(v, unit):
    if unit == "C": return v
    if unit == "F": return (v - 32) * 5.0 / 9.0
    if unit == "K": return v - 273.15
    if unit == "R": return (v - 491.67) * 5.0 / 9.0
    raise ValueError(f"unknown temperature unit: {unit}")

def _celsius_to_temp(c, unit):
    if unit == "C": return c
    if unit == "F": return c * 9.0 / 5.0 + 32
    if unit == "K": return c + 273.15
    if unit == "R": return (c + 273.15) * 9.0 / 5.0
    raise ValueError(f"unknown temperature unit: {unit}")

_TEMP_RE = re.compile(
    r"^\s*(-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*°?\s*([CcFfKkRr])\s*$"
)

def try_temp_side(s):
    m = _TEMP_RE.match(s)
    if not m: return None
    return float(m.group(1)), m.group(2).upper()

# ============================================================
# DISPLAY
# ============================================================
def _fmt_num(v, prec=6):
    if isinstance(v, int): return str(v)
    if not math.isfinite(v): return str(v)
    if v == 0: return "0"
    av = abs(v)
    if av < 1e-4 or av >= 1e7:
        return f"{v:.{prec}g}"
    if v.is_integer() and abs(v) < 1e15:
        return str(int(v))
    return f"{v:.{prec}g}"

def find_named_unit(dims):
    """Prefer exact SI-magnitude units; else any matching factor-1 unit; else None."""
    if not dims:
        return None
    for name, (d, f) in UNITS.items():
        if name in TEMP_UNITS: continue
        if d == dims and f == 1.0:
            return name
    return None

def unit_repr(dims):
    """Human-readable unit string from dims."""
    if not dims: return ""
    named = find_named_unit(dims)
    if named: return named
    return _dims_str(dims)

def format_quantity(q, prec=6, unit_label=None):
    v = q.value
    dims = q.dims
    if not dims:
        return _fmt_num(v, prec)
    if unit_label:
        return f"{_fmt_num(v, prec)} {unit_label}"
    named = find_named_unit(dims)
    if named:
        return f"{_fmt_num(v, prec)} {named}"
    return f"{_fmt_num(v, prec)} {_dims_str(dims)}"

# ============================================================
# STATE / CONFIG
# ============================================================
STATE = {
    "last_ans": None,           # Quantity or None
    "last_expr": "",
    "theme": "default",
    "rainbow": "auto",
    "animations": True,
    "precision": 6,
    "show_steps": False,
    "currency_note": True,
}
CONFIG_PATH = os.path.expanduser("~/.unitforge_config.json")
FIRST_RUN_FLAG = os.path.expanduser("~/.unitforge_seen")

def load_config():
    try:
        with open(CONFIG_PATH) as f: data = json.load(f)
        for k in ("theme","rainbow","animations","precision","show_steps","currency_note"):
            if k in data: STATE[k] = data[k]
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass

def save_config():
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump({k: STATE[k] for k in
                       ("theme","rainbow","animations","precision","show_steps","currency_note")},
                      f, indent=2)
    except OSError:
        pass

def is_first_run(): return not os.path.exists(FIRST_RUN_FLAG)
def mark_seen():
    try: open(FIRST_RUN_FLAG, "w").close()
    except OSError: pass

# ============================================================
# LOGO
# ============================================================
def _build_logo():
    return [
 [(LGRAY,"  "),(DGRAY,"▄▓▒▄▄"),(LGRAY,"         "),(DGRAY,"▄▓▒▄▄"),(LGRAY,"         "),(DGRAY,"▄▓▒▄▄"),(LGRAY,"         "),(DGRAY,"▄▓▒▄▄"),(LGRAY,"         "),(DGRAY,"▄▓▒▄▄"),(LGRAY,"         "),(DGRAY,"▄▓▒▄▄"),(LGRAY,"       ")],
 [(LGRAY," ▄▄"),(BLUE,"▄"),(DGRAY,"▀░▓▒▀▓▒▄"),(LGRAY,"   ▄▄"),(BLUE,"▄"),(LGRAY," "),(DGRAY,"▀▀▀▀▓▒▄"),(LGRAY,"   ▄▄"),(BLUE,"▄"),(LGRAY," "),(DGRAY,"▀▀▀▀▓▒▄"),(LGRAY,"   ▄▄"),(BLUE,"▄"),(LGRAY," "),(DGRAY,"▀▀▀▀▓▒▄"),(LGRAY,"   ▄▄"),(BLUE,"▄"),(LGRAY," "),(DGRAY,"▀▀▀▀▓▒▄"),(LGRAY,"   ▄▄"),(BLUE,"▄"),(LGRAY," "),(DGRAY,"▀▀▀▀▓▒▄"),(LGRAY,"   ▄▄"),(BLUE,"▄"),(LGRAY," "),(DGRAY,"▀▀▀▀▓▒▄"),(LGRAY,"  ")],
 [(LGRAY,"▐"),(BLUE,"███▓"),(DGRAY,"▐▒▌"),(BLUE,"█"),(BLUE,"▄"),(DBLUE,"▄"),(DGRAY,"▀▒"),(LGRAY," ▐"),(BLUE,"███▓████"),(BLUE,"▄"),(DBLUE,"▄"),(DGRAY,"▀▒"),(LGRAY," ▐"),(BLUE,"███▓████"),(BLUE,"▄"),(DBLUE,"▄"),(DGRAY,"▀▒"),(LGRAY," ▐"),(BLUE,"███▓████"),(BLUE,"▄"),(DBLUE,"▄"),(DGRAY,"▀▒"),(LGRAY," ▐"),(BLUE,"███▓████"),(BLUE,"▄"),(DBLUE,"▄"),(DGRAY,"▀▒"),(LGRAY," ▐"),(BLUE,"███▓████"),(BLUE,"▄"),(DBLUE,"▄"),(DGRAY,"▀▒"),(LGRAY," ")],
 [(BLUE,"▐"),(BLUE,"▓▓▒░"),(DGRAY,"▐▓▌"),(BLUE,"▒▒▓"),(DBLUE,"▌"),(DGRAY,"░▌"),(BLUE,"▐"),(BLUE,"▓▓▒░"),(DBLUE,"▀"),(BLUE,"▀▀"),(BLUE,"▒▒▓"),(DBLUE,"▌"),(DGRAY,"░▌"),(BLUE,"▐"),(BLUE,"▓▓▒░"),(DBLUE,"▀"),(BLUE,"▀▀"),(BLUE,"▒▒▓"),(DBLUE,"▌"),(DGRAY,"░▌"),(BLUE,"▐"),(BLUE,"▓▓▒░"),(DBLUE,"▀"),(BLUE,"▀█"),(BLUE,"▒▒▓"),(DBLUE,"▌"),(DGRAY,"░▌"),(BLUE,"▐"),(BLUE,"▓▓▒░"),(DBLUE,"▀"),(BLUE,"▀▀"),(BLUE,"▒▒▓"),(DBLUE,"▌"),(DGRAY,"░▌"),(BLUE,"▐"),(BLUE,"▓▓▒░"),(DBLUE,"▀"),(BLUE,"▀▀"),(BLUE,"▒▒▓"),(DBLUE,"▌"),(DGRAY,"░▌")],
 [(BLUE,"▐"),(BLUE,"▓▒░"),(DBLUE,"█"),(DGRAY,"▐▒▌"),(BLUE,"░░░"),(DBLUE,"▌"),(DGRAY,"▒▌"),(BLUE,"▐"),(BLUE,"▓▒░"),(DBLUE,"█"),(LGRAY," "),(DGRAY,"▀■"),(DBLUE,"▀▀▀"),(LGRAY,"   "),(BLUE,"▐"),(BLUE,"▓▒░"),(DBLUE,"█"),(DGRAY,"▐▒▌"),(BLUE,"░░░"),(DBLUE,"▌"),(DGRAY,"▒▌"),(BLUE,"▐"),(BLUE,"▓▒░"),(DBLUE,"█"),(DGRAY,"▐▌"),(LGRAY," "),(BLUE,"░░"),(DBLUE,"▀"),(LGRAY," "),(DGRAY,"▒▌"),(BLUE,"▐"),(BLUE,"▓▒░"),(DBLUE,"█"),(LGRAY," "),(DGRAY,"▀"),(LGRAY," "),(DBLUE,"▀▀▀"),(LGRAY,"   "),(BLUE,"▐"),(BLUE,"▓▒░"),(DBLUE,"█"),(LGRAY," "),(DGRAY,"▀■"),(DBLUE,"▀▀▀"),(LGRAY,"   ")],
 [(BLUE,"▐"),(DBLUE,"█▓▓█"),(DGRAY,"▐▓▌"),(DBLUE,"█▓█▌"),(DGRAY,"▒▌"),(BLUE,"▐"),(DBLUE,"█▓▓███"),(LGRAY,"  "),(DGRAY,"▄▓▒"),(LGRAY,"  "),(BLUE,"▐"),(DBLUE,"█▓▓█"),(DGRAY,"▐▓▌"),(DBLUE,"█▓█▌"),(DGRAY,"▒▌"),(BLUE,"▐"),(DBLUE,"█▓▓█▄▄██▄"),(LGRAY," "),(DGRAY,"▀▒▌"),(BLUE,"▐"),(DBLUE,"█▓▓█"),(LGRAY," "),(DBLUE,"▒▓██▓█"),(DGRAY,"▐▌"),(BLUE,"▐"),(DBLUE,"█▓▓███"),(LGRAY,"  "),(DGRAY,"▄▓▒▒"),(LGRAY," ")],
 [(DBLUE,"▐▒▒▒█"),(DGRAY,"▐▒▌"),(DBLUE,"█▒▒▌"),(DGRAY,"▓▌"),(DBLUE,"▐▒▒▒█"),(LGRAY," "),(DGRAY,"▄▄░"),(LGRAY,"     "),(DBLUE,"▐▒▒▒█"),(DGRAY,"▐▒▌"),(DBLUE,"█▒▒▌"),(DGRAY,"▓▌"),(DBLUE,"▐▒▒▒█"),(DGRAY,"■▄"),(DBLUE,"▀█▒▒"),(DGRAY,"▐▓▌"),(DBLUE,"▐▒▒▒█"),(DGRAY,"■▄"),(LGRAY," "),(DBLUE,"███▌"),(DGRAY,"▓▌"),(DBLUE,"▐▒▒▒█"),(LGRAY," "),(DGRAY,"▄"),(LGRAY," "),(DBLUE,"▄▄▄"),(LGRAY," "),(DGRAY,"▓▌")],
 [(LGRAY," "),(DBLUE,"░░░█▄▄▄█░░"),(DGRAY,"▐█"),(LGRAY," "),(DBLUE,"▐░░░▓"),(LGRAY," "),(DGRAY,"▓▓░"),(LGRAY,"      "),(DBLUE,"░░░█▄▄▄█░░"),(DGRAY,"▐█"),(LGRAY," "),(DBLUE,"▐░░░█"),(DGRAY,"▐▓▌"),(DBLUE,"█▓▒"),(DGRAY,"▐█▌"),(DBLUE,"▐░░░▓▄▄▄█▒▒▌"),(DGRAY,"▀▌"),(DBLUE,"▐░░░▓▄▄▄█▒▒▌"),(DGRAY,"▀▌")],
    ]


def clear(): sys.stdout.write("\033[2J\033[H"); sys.stdout.flush()

def logo():
    for line in _build_logo():
        print("".join(c + t for c, t in line) + RESET)

def launch_animation():
    if not STATE["animations"] or not _supports_color():
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
    dim = "\033[38;5;238m"
    rainbow = [RED, "\033[33m", YELLOW, GREEN, CYAN, BLUE, MAGENTA]
    n_colors = len(rainbow)
    sys.stdout.write(HIDE); sys.stdout.flush()
    try:
        frames = 22
        delay = 0.028
        sweep_half = 7
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
                    elif col < sweep_pos:
                        c = target
                    else:
                        c = dim
                    if c != prev: buf.append(c); prev = c
                    buf.append(ch)
                buf.append(RESET)
                sys.stdout.write("".join(buf) + "\n")
            sys.stdout.flush(); time.sleep(delay)
    finally:
        sys.stdout.write(SHOW); sys.stdout.flush()

def wordmark_pulse():
    tail = DGRAY + "\u2022 unit & dimensional analysis engine \u2022" + RESET
    if not STATE["animations"] or not _supports_color():
        print(f"  {BLUE}UnitForge{RESET} {tail}")
        return
    for c in [BLUE, WHITE, BLUE, WHITE, BLUE]:
        sys.stdout.write(f"\r  {c}UnitForge{RESET} {tail}")
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
    print(f"  {BLUE}help{RESET}      this menu")
    print(f"  {BLUE}units{RESET}     list all available units")
    print(f"  {BLUE}dims{RESET}      list base dimensions")
    print(f"  {BLUE}consts{RESET}    physical constants")
    print(f"  {BLUE}history{RESET}   recent inputs (!n to recall)")
    print(f"  {BLUE}settings{RESET}  settings menu")
    print(f"  {BLUE}clear{RESET}     redraw")
    print(f"  {BLUE}exit{RESET}      quit")
    print()
    print(f"  {DGRAY}Try:{RESET} {WHITE}5 kg * 9.8 m/s^2{RESET}   {WHITE}100 F to C{RESET}   {WHITE}120 mph to km/h{RESET}")
    print(); divider()

def first_run_intro():
    clear()
    for line in _build_logo():
        print("".join(c + t for c, t in line) + RESET)
        time.sleep(0.035)
    time.sleep(0.15); print()
    user = os.environ.get("USER") or os.environ.get("LOGNAME") or "friend"
    if user.startswith("u0_a"): user = "friend"
    print(f"  {BLUE}UnitForge{RESET} {DGRAY}\u2022 welcome, {user}{RESET}"); time.sleep(0.3)
    print(f"  {DGRAY}Type {WHITE}help{RESET}{DGRAY} for commands, or just start typing conversions.{RESET}"); time.sleep(0.3)
    print(f"  {DGRAY}Examples:{RESET}  {WHITE}100 F to C{RESET}   {WHITE}5 km in mi{RESET}   {WHITE}9.8 m/s^2 * 70 kg{RESET}")
    print()
    try: input(f"  {DGRAY}Press Enter to continue\u2026{RESET}")
    except (EOFError, KeyboardInterrupt): pass
    mark_seen()

# ============================================================
# CONVERSION
# ============================================================
_CONV_RE_ORDER = (r"\s*->\s*", r"\s+to\s+", r"\s+in\s+", r"\s*→\s*")

def split_conversion(s):
    for pat in _CONV_RE_ORDER:
        m = re.search(pat, s)
        if m:
            left = s[:m.start()].strip()
            right = s[m.end():].strip()
            if left and right:
                return left, right
    return None, None

def do_conversion(left, right):
    # temperature special case
    ltemp = try_temp_side(left)
    rtemp = try_temp_side(right)
    if ltemp and rtemp:
        v, su = ltemp
        _, du = rtemp
        c = _temp_to_celsius(v, su)
        result = _celsius_to_temp(c, du)
        return result, du, su
    # one side temperature -> dimension mismatch
    if ltemp or rtemp:
        raise ValueError("temperature conversions require a single number and a single temp unit on both sides")

    lq = eval_quantity(left)
    rq = eval_quantity(right)
    if lq.dims != rq.dims:
        raise ValueError(_dim_mismatch_msg(lq.dims, rq.dims))
    if rq.value == 0:
        raise ValueError("target unit has zero magnitude")
    out = lq.value / rq.value
    return out, right, left

# ============================================================
# STEPS
# ============================================================
def show_steps(expr):
    print()
    print(f"  {BLUE}STEPS{RESET}   {DGRAY}for {WHITE}{expr}{RESET}")
    print()
    try:
        tokens = _tokenize(expr)
        py = _build_py_expr(tokens)
        print(f"  {DGRAY}1. tokens{RESET}      {WHITE}{tokens}{RESET}")
        print(f"  {DGRAY}2. python{RESET}      {WHITE}{py}{RESET}")
        q = eval_quantity(expr)
        print(f"  {DGRAY}3. SI value{RESET}    {WHITE}{q.value} {_dims_str(q.dims)}{RESET}")
        print(f"  {DGRAY}4. result{RESET}      {WHITE}{format_quantity(q, STATE['precision'])}{RESET}")
    except Exception as e:
        print(f"  {RED}\u2715 {e}{RESET}")
    print()

# ============================================================
# INFO SCREENS
# ============================================================
UNIT_CATEGORIES = [
    ("Length",       ["m","km","cm","mm","um","nm","mi","yd","ft","in","nmi","ly","au","pc"]),
    ("Mass",         ["kg","g","mg","lb","oz","st","t","tonne"]),
    ("Time",         ["s","ms","us","ns","min","h","day","wk","yr"]),
    ("Volume",       ["L","mL","gal","qt","pt","cup","floz","tbsp","tsp","bbl"]),
    ("Temperature",  ["C","F","K","R"]),
    ("Speed",        ["mph","kph","knot"]),
    ("Force / Energy / Power",
                     ["N","J","W","cal","kcal","eV","kWh","BTU","erg","hp"]),
    ("Pressure",     ["Pa","atm","bar","mbar","psi","torr","mmHg"]),
    ("Electrical",   ["A","V","Wb","T","H","S"]),
    ("Angle",        ["rad","deg","grad","turn"]),
    ("Currency",     ["USD","EUR","GBP","JPY","CAD","AUD","CHF","CNY","INR","KRW","MXN","BRL","ZAR","SEK","NOK"]),
]

def show_units():
    print()
    print(f"  {BLUE}UNITS{RESET}")
    print()
    for cat, names in UNIT_CATEGORIES:
        print(f"  {LGRAY}{cat}{RESET}")
        line = "    "
        for n in names:
            if len(line) + len(n) + 3 > 76:
                print(f"  {WHITE}{line}{RESET}")
                line = "    "
            line += n + "  "
        if line.strip():
            print(f"  {WHITE}{line}{RESET}")
        print()
    print(f"  {DGRAY}Compound units: {WHITE}m/s{RESET}  {WHITE}kg*m/s^2{RESET}  {WHITE}J/s{RESET}  {WHITE}N*m{RESET}")
    print(f"  {DGRAY}Currency rates are offline placeholders \u2014 edit them in the source.{RESET}")
    print()

def show_dims():
    print()
    print(f"  {BLUE}BASE DIMENSIONS{RESET}")
    print()
    rows = [
        ("M", "mass",              "kg"),
        ("L", "length",            "m"),
        ("T", "time",              "s"),
        ("I", "electric current",  "A"),
        ("K", "temperature",       "K"),
        ("N", "amount",            "mol"),
        ("J", "luminous intensity","cd"),
        ("$", "currency",          "USD"),
    ]
    for sym, name, base in rows:
        print(f"  {WHITE}{sym}{RESET}   {LGRAY}{name:<22}{RESET} {DGRAY}base: {WHITE}{base}{RESET}")
    print()
    print(f"  {DGRAY}Every unit is a combination of these. Example:{RESET}")
    print(f"    {WHITE}N{RESET}   = M\u00b7L/T\u00b2  (kg\u00b7m/s\u00b2)")
    print(f"    {WHITE}J{RESET}   = M\u00b7L\u00b2/T\u00b2 (kg\u00b7m\u00b2/s\u00b2)")
    print(f"    {WHITE}W{RESET}   = M\u00b7L\u00b2/T\u00b3 (kg\u00b7m\u00b2/s\u00b3)")
    print()

CONSTANTS = [
    ("c",        299792458.0,              "m/s",   "speed of light"),
    ("g0",       9.80665,                  "m/s^2", "standard gravity"),
    ("h",        6.62607015e-34,           "J*s",   "Planck's constant"),
    ("hbar",     1.054571817e-34,          "J*s",   "reduced Planck"),
    ("kB",       1.380649e-23,             "J/K",   "Boltzmann constant"),
    ("NA",       6.02214076e23,            "1/mol", "Avogadro number"),
    ("e",        1.602176634e-19,          "C",     "elementary charge"),
    ("me",       9.1093837015e-31,         "kg",    "electron mass"),
    ("mp",       1.67262192369e-27,        "kg",    "proton mass"),
    ("G",        6.67430e-11,              "m^3/(kg*s^2)", "gravitational constant"),
    ("R",        8.314462618,              "J/(mol*K)",    "gas constant"),
    ("sigma",    5.670374419e-8,           "W/(m^2*K^4)",  "Stefan–Boltzmann"),
]

def show_constants():
    print()
    print(f"  {BLUE}PHYSICAL CONSTANTS{RESET}")
    print()
    for name, value, unit, desc in CONSTANTS:
        val_s = _fmt_num(value, 6)
        print(f"  {WHITE}{name:<8}{RESET} {LGRAY}{val_s:<16}{RESET} {CYAN}{unit:<16}{RESET} {DGRAY}{desc}{RESET}")
    print()
    print(f"  {DGRAY}These are shown for reference; they are not part of the unit namespace.{RESET}")
    print()

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

def show_help():
    print()
    print(f"  {BLUE}HELP{RESET}  {DGRAY}\u2014 UnitForge cheat sheet{RESET}")
    print()
    print(f"  {LGRAY}Convert{RESET}")
    print(f"    {WHITE}100 F to C{RESET}                 temperature")
    print(f"    {WHITE}5 km in mi{RESET}                 length")
    print(f"    {WHITE}120 mph -> km/h{RESET}            speed")
    print(f"    {WHITE}3 tbsp to ml{RESET}               volume")
    print(f"    {WHITE}1 atm to psi{RESET}               pressure")
    print(f"    {WHITE}60 USD to EUR{RESET}              currency (placeholder rates)")
    print()
    print(f"  {LGRAY}Calculate with units{RESET}")
    print(f"    {WHITE}5 kg * 9.8 m/s^2{RESET}          \u2192 force")
    print(f"    {WHITE}100 W * 3 h{RESET}                \u2192 energy")
    print(f"    {WHITE}60 km/h / 4 s{RESET}              \u2192 acceleration")
    print(f"    {WHITE}10 m / 2 s{RESET}                 \u2192 speed")
    print(f"    {WHITE}2 m * 3 m{RESET}                  \u2192 area")
    print()
    print(f"  {LGRAY}Input rules{RESET}")
    print(f"    {DGRAY}* implicit multiplication: 5 kg means 5*kg, m/s means m/s{RESET}")
    print(f"    {DGRAY}* powers with ^ : m/s^2, kg*m^2/s^3{RESET}")
    print(f"    {DGRAY}* use · or × for multiplication, ÷ for division{RESET}")
    print(f"    {DGRAY}* 'ans' refers to the previous result{RESET}")
    print()
    print(f"  {LGRAY}Commands{RESET}")
    print(f"    {WHITE}help{RESET}      this screen")
    print(f"    {WHITE}units{RESET}     all available units")
    print(f"    {WHITE}dims{RESET}      base dimensions")
    print(f"    {WHITE}consts{RESET}    physical constants")
    print(f"    {WHITE}history{RESET}   recent inputs ({WHITE}!n{RESET} to rerun)")
    print(f"    {WHITE}settings{RESET}  settings")
    print(f"    {WHITE}?expr{RESET}     parse + eval steps")
    print(f"    {WHITE}clear{RESET}     redraw")
    print(f"    {WHITE}exit{RESET}      quit")
    print()

# ============================================================
# SETTINGS
# ============================================================
def settings_menu():
    while True:
        clear(); logo(); print()
        print(f"  {BLUE}SETTINGS{RESET}"); divider()
        def row(k, label, val):
            print(f"  {WHITE}[{k:>2}]{RESET} {label:<24} {DGRAY}[{val}]{RESET}")
        row(1, "Theme",              STATE["theme"])
        row(2, "Rainbow",            STATE["rainbow"])
        row(3, "Launch animation",   "on" if STATE["animations"] else "off")
        row(4, "Precision (sig figs)", STATE["precision"])
        row(5, "Show steps on eval", "on" if STATE["show_steps"] else "off")
        row(6, "Currency note",      "on" if STATE["currency_note"] else "off")
        row(7, "Reset settings",     "\u2014")
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
            except ValueError:
                STATE["precision"] = 6
        elif choice == "5": STATE["show_steps"] = not STATE["show_steps"]
        elif choice == "6": STATE["currency_note"] = not STATE["currency_note"]
        elif choice == "7":
            STATE.update({"theme":"default","rainbow":"auto","animations":True,
                          "precision":6,"show_steps":False,"currency_note":True})
            apply_theme()
        save_config()

# ============================================================
# TAB COMPLETION
# ============================================================
def setup_completer():
    if not READLINE_OK: return
    base = ["help","units","dims","consts","constants","history","settings","clear","exit","quit"]
    def completer(text, state):
        names = base + list(UNITS) + list(UNIT_ALIASES)
        opts = [n for n in names if n.startswith(text)]
        if state < len(opts): return opts[state]
        return None
    readline.set_completer(completer)
    try: readline.parse_and_set_complete("tab: complete")
    except Exception:
        try: readline.parse_and_bind("tab: complete")
        except Exception: pass

# ============================================================
# INPUT PROCESSING
# ============================================================
def _supports_color():
    if os.environ.get("NO_COLOR"): return False
    if os.environ.get("UNITFORGE_NO_COLOR"): return False
    if os.environ.get("UNITFORGE_FORCE_COLOR"): return True
    if _is_wine(): return False
    if not sys.stdout.isatty(): return False
    return True

def _strip_ansi_if_needed():
    if _supports_color(): return
    for preset in THEME_PRESETS.values():
        for k in list(preset.keys()):
            if k == "RAINBOW": preset[k] = [""] * 7
            else: preset[k] = ""

def _print_result(text, animate=True):
    ctx = "result"
    if not animate or not _supports_color() or STATE["rainbow"] == "off":
        print(f"  {GREEN}\u2713{RESET} {WHITE}{text}{RESET}")
        return
    if STATE["rainbow"] == "off":
        print(f"  {GREEN}\u2713{RESET} {WHITE}{text}{RESET}")
        return
    sys.stdout.write(f"  {DGRAY}calculating\u2026{RESET}"); sys.stdout.flush()
    time.sleep(0.06); sys.stdout.write("\r" + " " * 40 + "\r"); sys.stdout.flush()
    for c in RAINBOW:
        sys.stdout.write(f"\r  {c}\u2713 {text}{RESET}")
        sys.stdout.flush(); time.sleep(0.035)
    sys.stdout.write(f"\r  {GREEN}\u2713{RESET} {WHITE}{text}{RESET}\n"); sys.stdout.flush()

def process_input(raw):
    cleaned = raw.strip()
    if not cleaned: return
    cmd = cleaned.lower()

    if cmd in ("exit", "quit"): raise SystemExit
    if cmd == "help":      show_help(); return
    if cmd == "units":     show_units(); return
    if cmd == "dims":      show_dims(); return
    if cmd in ("consts","constants"): show_constants(); return
    if cmd == "history":   show_history(); return
    if cmd == "clear":     header(animate=False); return
    if cmd == "settings":
        settings_menu(); header(animate=False); return

    m = re.fullmatch(r"!(\d+)", cleaned)
    if m:
        cleaned = recall_history(int(m.group(1)))
        print(f"  {DGRAY}\u21b3 rerunning: {WHITE}{cleaned}{RESET}")

    if cleaned.startswith("?"):
        show_steps(cleaned[1:].strip()); return

    # ans substitution
    if STATE["last_ans"] is not None:
        cleaned = re.sub(r"\bans\b", f"({STATE['last_ans'].value})", cleaned)

    left, right = split_conversion(cleaned)
    if left and right:
        value, target_unit, source = do_conversion(left, right)
        text = f"{_fmt_num(value, STATE['precision'])} {target_unit}"
        _print_result(text)
        STATE["last_expr"] = cleaned
        # store last_ans as SI Quantity when possible
        try:
            if target_unit.upper() in TEMP_UNITS or (len(target_unit) == 1 and target_unit.upper() in TEMP_UNITS):
                STATE["last_ans"] = Quantity(value, {"K": 1})   # rough placeholder
            else:
                rq = eval_quantity(right)
                STATE["last_ans"] = Quantity(value * rq.value, rq.dims)
        except Exception:
            STATE["last_ans"] = None
        return

    # plain quantity expression
    q = eval_quantity(cleaned)
    text = format_quantity(q, STATE["precision"])
    _print_result(text)
    STATE["last_ans"] = q
    STATE["last_expr"] = cleaned

    if STATE["show_steps"]:
        show_steps(cleaned)

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
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

def _sigint_handler(sig, frame):
    print()
    _shutdown()
    sys.exit(0)

def main():
    import signal
    load_config()
    _enable_windows_vt()
    _strip_ansi_if_needed()
    apply_theme()
    try: signal.signal(signal.SIGINT, _sigint_handler)
    except Exception: pass
    if is_first_run(): first_run_intro()
    setup_completer()
    header(animate=True)
    while True:
        print()
        try:
            user_input = input(prompt_main())
        except (EOFError, KeyboardInterrupt):
            _shutdown(); return
        try:
            process_input(user_input)
        except SystemExit:
            _shutdown(); return
        except Exception as exc:
            try:
                print(f"\n  {RED}\u2715{RESET} {exc}")
            except Exception:
                pass

if __name__ == "__main__":
    main()
