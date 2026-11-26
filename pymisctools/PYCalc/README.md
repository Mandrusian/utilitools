# PYCalc

Terminal mathematics engine with symbolic equation solving, unit & base
conversions, ASCII & SVG graphing, user-defined functions, and session
persistence. Sibling of UnitForge, Nota, PolyglotBench, and GitViz.

## Quick start

    python3 PYCalc.py
    python3 PYCalc.py -e "sin(30°) + 2^10"
    python3 PYCalc.py --no-anim --no-color

Then type expressions, equations, or commands at the prompt:

    2 + 3 * 4
    y = 3x + 2
    plot(sin(x); cos(x), -6.28, 6.28)
    svg(x^2, -3, 3, 0, 9, parabola)
    5 km to mi
    0xff to dec
    255 to hex

## Install

    python3 install_pycalc.py              # build & install for current OS
    python3 install_pycalc.py --dry-run    # preview actions
    python3 install_pycalc.py --uninstall  # remove installed binary/launcher

## Features

- Implicit multiplication (`2x`, `xy`, `2(3+4)`, `2sin(x)`), powers (`^`), roots (`√16`), degrees (`30°`), and percentages (`20% of 80`).
- Interactive equation variables (`y = 3x + 2`), variable caching, and formula replay (`ans`, `ans-q`, `ans-q = x`).
- Complex numbers (`sqrt(-1)` -> `i`), number base literals & conversions (`0xff`, `0b1010`, `0o17`, `255 to hex`, `0xff to dec`).
- Unit conversions for length, mass, time, volume, and temperature (`C`, `F`, `K`).
- Multi-curve ASCII terminal plots (`plot(...)`) and SVG export (`svg(...)`, `svg-list`, `svg-open N`).
- User-defined functions (`f(x) = x^2 + 1` in advanced mode), step-by-step evaluation (`?expr`), readline history (`!n`), and named sessions (`save` / `load`).

## CLI

    pycalc [-e EXPR] [--no-anim] [--no-color]

## Tests

    python3 test_pycalc.py

## License

MIT.
