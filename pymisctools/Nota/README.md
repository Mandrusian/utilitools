# Nota

Plain-text notebooks for the terminal with shared Python state, Markdown-lite
prose rendering, ASCII plotting, and SVG export. Sibling of PYCalc, UnitForge,
PolyglotBench, and GitViz.

## Quick start

    python3 nota.py                  # interactive REPL
    python3 nota.py example.nota     # run a notebook
    python3 nota.py example.nota --svg
    python3 nota.py example.nota --check
    python3 nota.py example.nota --quiet --no-color

## Notebook format (`.nota`)

`.nota` files are plain text combining Markdown-lite prose with fenced code
cells:

- **Prose**: headings (`#`, `##`), **bold**, *italic*, `` `code` ``, lists,
  blockquotes (`>`), and horizontal rules (`---`).
- **Python cells** (```` ```python ```` or unlabeled ```` ``` ````): executed in
  a shared namespace across the notebook; the last expression value is printed.
- **Plot cells** (```` ```plot ```` or ```` ```nota-plot ````): executed in the
  same shared namespace, then rendered as an ASCII chart (and optionally saved
  as SVG when `--svg` is passed).

### Plot helpers

Built into every notebook and REPL namespace:

    linspace(a, b, n=200)    arange(a, b, step=1)
    sin  cos  tan  sqrt  exp  log  ln  abs    (vectorized over lists/tuples)
    pi   e   tau
    plot(x, y=None, label="")
    scatter(x, y=None, label="")
    title(s)   xlabel(s)   ylabel(s)   xlim(a, b)   ylim(a, b)

## Install

    python3 install_nota.py
    python3 install_nota.py --build
    python3 install_nota.py --uninstall

## CLI

    nota [file] [--svg] [--quiet] [--check] [--no-anim] [--no-color]

## REPL commands

    :help       show commands
    :load FILE  run a .nota file in a fresh namespace
    :run        re-run the last loaded file
    :settings   theme, rainbow, launch animation, precision
    :clear      redraw interface
    :exit       quit

## License

MIT.
