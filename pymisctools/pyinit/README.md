# pyinit

Launcher for the utilitools suite. Discovers every tool folder under
`~/utilitools/` and presents a menu. Pick a number, it runs that tool.

## Quick start

    python3 pyinit.py           # menu
    python3 pyinit.py PYCalc    # launch by name
    python3 pyinit.py Nota example.nota   # launch with args

## Install

    python3 install_pyinit.py               # put pyinit on PATH
    python3 install_pyinit.py --uninstall

After install:

    pyinit                                  # menu
    pyinit PYCalc
    pyinit GitViz ~/utilitools/PYCalc

## Discovery

`pyinit` looks at every folder inside the utilitools root (default:
`~/utilitools/`). For each one it finds the entry-point .py file:

1. If a `pyinit.json` exists in the folder, use `entry` from it.
2. Otherwise try `<Folder>.py`, `<folder>.py`, `<folderlower>.py`.
3. Otherwise the first `.py` file that isn't `install_*.py` or `_*.py`.

The tool's description comes from `pyinit.json` if present, else the first
non-heading line of its `README.md`.

To override:

    {
      "name": "PYCalc",
      "entry": "PYCalc.py",
      "description": "terminal mathematics engine"
    }

## Menu

    ```
      ❯ pyinit  • utilitools launcher
      /Users/xavi/utilitools

      [1] PYCalc         PYCalc — terminal mathematics engine
      [2] UnitForge      UnitForge terminal unit & dimensional analysis engine
      [3] Nota           Nota plain-text notebooks for the terminal
      [4] PolyglotBench  PolyglotBench run the same tiny programs in many languages
      [5] GitViz         GitViz render git history as an ASCII branch graph

      [r] refresh   [q] quit
    ```

Number keys launch. `r` rediscovers tools (useful after you add a new
folder). `q` quits.

## Environment

    UTILITOOLS_ROOT     override the root folder (default: ~/utilitools)
    PYINIT_NO_COLOR     strip ANSI output
    PYINIT_FORCE_COLOR  force ANSI even if stdout isn't a tty

## Files

    pyinit.py             the launcher
    install_pyinit.py     installer
    ~/.local/bin/pyinit   launcher on PATH (after install)

## License

MIT.
