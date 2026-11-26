# utilitools

A suite of zero-dependency, Python stdlib terminal utilities under `pymisctools/`,
unified by the `pyinit` launcher.

## Tools (`pymisctools/`)

| Tool | Description | Entry point |
| --- | --- | --- |
| [**PYCalc**](pymisctools/PYCalc/README.md) | Terminal mathematics engine with equation variables, unit/base conversion, ASCII & SVG graphing, user functions, and sessions | `pymisctools/PYCalc/PYCalc.py` |
| [**UnitForge**](pymisctools/UnitForge/README.md) | Unit & dimensional analysis engine with compound expressions, temperature offsets, and SI/imperial/currency units | `pymisctools/UnitForge/unitforge.py` |
| [**Nota**](pymisctools/Nota/README.md) | Plain-text notebooks (`.nota`) combining Markdown-lite prose, shared-state Python cells, and ASCII/SVG plots | `pymisctools/Nota/nota.py` |
| [**PolyglotBench**](pymisctools/PolyglotBench/README.md) | Multi-language micro-benchmark runner comparing Python, JS, Go, C, C++, Rust, Ruby, and Bash against shared specs | `pymisctools/PolyglotBench/polyglotbench.py` |
| [**GitViz**](pymisctools/GitViz/README.md) | Git commit history renderer as an ASCII branch graph or standalone SVG | `pymisctools/GitViz/gitviz.py` |
| [**pyinit**](pymisctools/pyinit/README.md) | Interactive menu & CLI launcher that discovers tools in `pymisctools/` | `pymisctools/pyinit/pyinit.py` |

## Quick start

Run the launcher menu or invoke any tool directly with Python 3:

```sh
python3 pymisctools/pyinit/pyinit.py
python3 pymisctools/pyinit/pyinit.py --list
python3 pymisctools/pyinit/pyinit.py PYCalc
```

Or run individual tools standalone:

```sh
python3 pymisctools/PYCalc/PYCalc.py -e "sin(30°) + 2^10"
python3 pymisctools/UnitForge/unitforge.py "100 F to C"
python3 pymisctools/Nota/nota.py pymisctools/Nota/example.nota --no-anim
python3 pymisctools/PolyglotBench/polyglotbench.py --list
python3 pymisctools/GitViz/gitviz.py . --limit 20
```

## Install

### macOS / Linux / Termux

```sh
bash pymisctools/install.sh
```

Or install `pyinit` directly from an existing clone:

```sh
python3 pymisctools/pyinit/install_pyinit.py
```

### Windows

Run [`install.bat`](install.bat) from Command Prompt, or run the per-tool installers:

```bat
install.bat
```

Each tool in `pymisctools/` also includes its own `install_<tool>.py` script
(`--uninstall` supported; `--build` / PyInstaller supported where applicable).

## Tests

Run the full test suite from the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 pymisctools/PYCalc/test_pycalc.py
```

## License

[MIT](LICENSE)
