#!/usr/bin/env python3
"""External monitor settings TUI for Sway and SwayFX.

Only external outputs are listed; internal eDP/LVDS/DSI panels are excluded.
Requires Python 3, curses (standard library), and swaymsg. No root required.
"""
import curses
import json
import shutil
import subprocess
import sys
from pathlib import Path

CONFIG_DIR = Path.home() / ".config/sway"
CONFIG_FILE = CONFIG_DIR / "monitors.conf"
MAIN_CONFIG = CONFIG_DIR / "config"
INTERNAL_PREFIXES = ("eDP-", "LVDS-", "DSI-")
SCALE_OPTIONS = ("0.5", "0.75", "1", "1.25", "1.5", "1.75", "2", "2.5", "3")


def command(*args, check=True):
    proc = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and proc.returncode:
        raise RuntimeError(proc.stderr.strip() or f"Command failed: {' '.join(args)}")
    return proc.stdout.strip()


def get_outputs():
    return json.loads(command("swaymsg", "-t", "get_outputs", "-r"))


def external_outputs():
    return [o for o in get_outputs() if o.get("name") and not o["name"].startswith(INTERNAL_PREFIXES)]


def mode_label(mode):
    hz = mode.get("refresh", 0) / 1000
    return f'{mode.get("width", "?")}x{mode.get("height", "?")} @ {hz:.3g} Hz'


def choose(stdscr, title, options, selected=0):
    if not options:
        return None
    idx = max(0, min(selected, len(options) - 1))
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        stdscr.addnstr(0, 2, title, max(1, w - 4), curses.A_BOLD)
        stdscr.addnstr(1, 2, "↑/↓ or j/k move · Enter select · q/Esc back", max(1, w - 4))
        visible = max(1, h - 4)
        start = max(0, min(idx - visible + 1, len(options) - visible))
        for row, i in enumerate(range(start, min(len(options), start + visible)), 3):
            attr = curses.A_REVERSE if i == idx else curses.A_NORMAL
            stdscr.addnstr(row, 2, ("➤ " if i == idx else "  ") + str(options[i]), max(1, w - 4), attr)
        stdscr.refresh()
        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")):
            idx = (idx - 1) % len(options)
        elif key in (curses.KEY_DOWN, ord("j")):
            idx = (idx + 1) % len(options)
        elif key in (curses.KEY_ENTER, 10, 13):
            return idx
        elif key in (ord("q"), 27):
            return None


def message(stdscr, lines):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    for i, line in enumerate(lines[:max(0, h - 2)], 1):
        stdscr.addnstr(i, 2, line, max(1, w - 4))
    stdscr.addnstr(h - 1, 2, "Press any key to return", max(1, w - 4))
    stdscr.refresh()
    stdscr.getch()


def save_output_settings(name, settings):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    old = CONFIG_FILE.read_text() if CONFIG_FILE.exists() else ""
    prefix = f"output {name} "
    lines = [line for line in old.splitlines() if not line.strip().startswith(prefix)]
    for key in ("mode", "scale", "position"):
        if settings.get(key):
            lines.append(f"output {name} {key} {settings[key]}")
    CONFIG_FILE.write_text("\n".join(lines).strip() + "\n")

    include_line = "include ~/.config/sway/monitors.conf"
    if MAIN_CONFIG.exists():
        main_text = MAIN_CONFIG.read_text()
        if include_line not in main_text and "include ~/.config/sway/*" not in main_text:
            with MAIN_CONFIG.open("a") as f:
                f.write("\n# Monitor settings managed by sway-monitor-tui\n" + include_line + "\n")
    command("swaymsg", "reload", check=False)


def setting_from_output(out):
    mode = out.get("current_mode") or {}
    rect = out.get("rect") or {}
    return {
        "mode": (f'{mode["width"]}x{mode["height"]}@{mode.get("refresh", 0) / 1000:.3f}Hz'
                 if mode.get("width") and mode.get("height") else ""),
        "scale": str(out.get("scale", 1)),
        "position": f'{rect.get("x", 0)} {rect.get("y", 0)}',
    }


def apply_setting(name, key, value):
    if key == "mode":
        command("swaymsg", "output", name, "mode", value)
    elif key == "scale":
        command("swaymsg", "output", name, "scale", value)
    elif key == "position":
        x, y = value.split()
        command("swaymsg", "output", name, "position", x, y)


def edit_output(stdscr, out):
    name = out["name"]
    settings = setting_from_output(out)
    while True:
        labels = [
            f'Resolution / refresh: {mode_label(out.get("current_mode") or {})}',
            f'Scale factor: {settings["scale"]}x',
            f'Position: {settings["position"]}',
            "Save these settings for future logins",
            "Back to output list",
        ]
        pick = choose(stdscr, f"Settings for {name}", labels)
        if pick is None or pick == 4:
            return
        try:
            if pick == 0:
                modes = out.get("modes", [])
                mode_names = [mode_label(m) for m in modes]
                mi = choose(stdscr, f"Resolution / refresh for {name}", mode_names)
                if mi is None:
                    continue
                mode = modes[mi]
                hz = mode.get("refresh", 0) / 1000
                value = f'{mode["width"]}x{mode["height"]}@{hz:.3f}Hz'
                apply_setting(name, "mode", value)
                settings["mode"] = value
            elif pick == 1:
                options = list(SCALE_OPTIONS)
                if settings["scale"] not in options:
                    options.insert(0, settings["scale"] + " (current/custom)")
                si = choose(stdscr, f"Scale factor for {name}", options,
                            options.index(settings["scale"]) if settings["scale"] in options else 0)
                if si is None:
                    continue
                value = options[si].split()[0]
                apply_setting(name, "scale", value)
                settings["scale"] = value
            elif pick == 2:
                choices = ["Right of another monitor", "Left of another monitor", "Keep current position"]
                pi = choose(stdscr, f"Position {name}", choices)
                if pi is None:
                    continue
                # Include internal panels as positioning anchors, even though the TUI
                # only offers external outputs for editing.
                fresh = get_outputs()
                current = next((o for o in fresh if o["name"] == name), out)
                others = [o for o in fresh if o["name"] != name and o.get("active", True)]
                if pi == 2:
                    pos = settings["position"]
                elif not others:
                    message(stdscr, ["No other active external monitor was found.",
                                     "Connect or enable another external monitor first."])
                    continue
                else:
                    anchor_labels = [
                        f'{o["name"]} — {o.get("rect", {}).get("width", "?")}x{o.get("rect", {}).get("height", "?")} at '
                        f'{o.get("rect", {}).get("x", 0)} {o.get("rect", {}).get("y", 0)}'
                        for o in others
                    ]
                    ai = choose(stdscr, f"Position {name} relative to…", anchor_labels)
                    if ai is None:
                        continue
                    anchor = others[ai]
                    rect = anchor.get("rect", {})
                    current_rect = current.get("rect", {})
                    anchor_w = rect.get("width", 0)
                    current_w = current_rect.get("width", 0)
                    if not current_w:
                        scale = float(settings["scale"] or 1)
                        current_w = round((current.get("current_mode") or {}).get("width", 0) / scale)
                    # Normalize the chosen pair to a shared origin before placing
                    # them side-by-side. Moving only the target can leave it far
                    # away from the anchor after a previous layout/order change.
                    if pi == 0:  # target to the right of anchor
                        apply_setting(anchor["name"], "position", "0 0")
                        pos = f"{anchor_w} 0"
                    else:  # target to the left of anchor
                        pos = "0 0"
                        apply_setting(anchor["name"], "position", f"{current_w} 0")
                apply_setting(name, "position", pos)
                settings["position"] = pos
            elif pick == 3:
                save_output_settings(name, settings)
                message(stdscr, [f"Saved settings for {name}.", f"Config: {CONFIG_FILE}"])
                continue
            message(stdscr, [f"Applied to {name}.", f"Mode: {settings['mode'] or 'unchanged'}",
                              f"Scale: {settings['scale']}x", f"Position: {settings['position']}",
                              "The built-in laptop panel is excluded from this tool."])
            out = next((o for o in external_outputs() if o["name"] == name), out)
        except Exception as exc:
            message(stdscr, [f"Couldn't update {name}:", str(exc)])


def main(stdscr):
    curses.curs_set(0)
    while True:
        try:
            outs = external_outputs()
        except Exception as exc:
            message(stdscr, ["Couldn't query Sway outputs.", str(exc), "Run inside a Sway/SwayFX session."])
            return
        labels = [
            f'{o["name"]} — {mode_label(o.get("current_mode") or {})} · scale {o.get("scale", 1)}x'
            for o in outs
        ] + ["Refresh output list", "Quit"]
        pick = choose(stdscr, "SwayFX external monitor settings", labels)
        if pick is None or pick == len(labels) - 1:
            return
        if pick == len(outs):
            continue
        edit_output(stdscr, outs[pick])


if __name__ == "__main__":
    if not shutil.which("swaymsg"):
        print("swaymsg not found. Run this from inside Sway/SwayFX.", file=sys.stderr)
        sys.exit(1)
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
