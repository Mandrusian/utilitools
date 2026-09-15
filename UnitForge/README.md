# UnitForge

Terminal unit & dimensional analysis engine. Sibling of PYCalc.

UnitForge converts between units of the same dimension, calculates with
units attached, and checks dimensional consistency as it goes. It handles
temperature offsets correctly, knows SI base and derived units plus a wide
set of imperial, US customary, currency, angle, energy, and pressure units,
and prints everything in the terminal with the same look and feel as PYCalc.

## Quick start

    python3 unitforge.py

Then type any of these at the prompt:

    100 F to C
    5 km in mi
    5 kg * 9.8 m/s^2
    60 km/h / 4 s
    1 atm to psi

## Install

    python3 install_unitforge.py            # copy to a stable location + launcher
    python3 install_unitforge.py --build    # also build a native bundle (PyInstaller)
    python3 install_unitforge.py --uninstall

Install locations per platform:

    macOS    ~/Library/Application Support/UnitForge/
             launcher: /usr/local/bin/unitforge or ~/.local/bin/unitforge

    Linux    ~/.local/share/unitforge/
             launcher: ~/.local/bin/unitforge

    Termux   ~/.local/share/unitforge/
             launcher: ~/.local/bin/unitforge

    Windows  %LOCALAPPDATA%\UnitForge\
             launcher: unitforge.bat in the same folder

Add ~/.local/bin (or %LOCALAPPDATA%\UnitForge) to PATH if it isn't already
there.

## Input rules

Implicit multiplication works everywhere: 5 kg is 5 * kg, m/s is m / s,
kg*m/s^2 is fine. Powers use ^, and ** also works. The characters ·, ×, and
÷ are accepted as aliases for *, *, and /. Temperature conversions only work
in the form NUMBER UNIT to UNIT, because offsets don't compose inside
compound expressions.

ans refers to the previous result.

## Commands

    help      cheat sheet
    units     list every available unit, grouped by category
    dims      show the base dimensions and how derived units are built
    consts    physical constants for reference
    history   recent inputs; use !n to rerun entry n
    settings  theme, precision, animation, currency note
    ?expr     show tokenization and evaluation steps
    clear     redraw the interface
    exit      quit

## Files

    unitforge.py                 the app
    install_unitforge.py         universal installer
    ~/.unitforge_config.json     persisted settings
    ~/.unitforge_history         readline input history

## Notes

Currency rates are offline placeholders stored in the UNITS table of
unitforge.py. Edit them there if you want different values. Live rates
are not fetched.

Temperature is handled as an affine scale. 100 F to C, 0 C to K, and
300 K to F all work. Temperature units are not allowed inside compound
expressions like kg*K/s, because mixing offsets with multiplicative units
is ambiguous.

## License

MIT.
