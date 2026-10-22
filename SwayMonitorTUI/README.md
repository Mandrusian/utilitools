# SwayMonitorTUI

A small keyboard-driven TUI for configuring external monitors in Sway/SwayFX.

## Features

- Lists external outputs and excludes built-in eDP/LVDS/DSI laptop panels.
- Change each external monitor's resolution/refresh rate, scale factor, and position independently.
- Save output settings to `~/.config/sway/monitors.conf` and automatically add an include to the main Sway config when needed.
- Uses `swaymsg`; no root privileges or third-party Python packages required.

## Requirements

- Sway or SwayFX running
- Python 3
- `swaymsg` available in PATH

## Install

From this repository checkout:

```sh
chmod +x SwayMonitorTUI/install.sh
SwayMonitorTUI/install.sh
```

The installer places the executable at `~/.local/bin/sway-monitor-tui` (or `$XDG_BIN_HOME/sway-monitor-tui` if set). Ensure that directory is on your `PATH`.

Run it inside your Sway/SwayFX session:

```sh
sway-monitor-tui
```

Use the arrow keys or `j`/`k` to navigate, Enter to select, and `q` or Escape to go back. Changes apply immediately; choose **Save these settings for future logins** for persistence.
