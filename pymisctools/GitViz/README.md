# GitViz

Render git history as an ASCII branch graph in the terminal, or export it
as an SVG. Sibling of PYCalc, UnitForge, Nota, and PolyglotBench.

## What it does

Reads `git log` for a repo, assigns each commit to a lane, and prints the
history as a colored lane graph. Optionally renders the same graph as a
standalone SVG you can open in any viewer.

No external dependencies. Stdlib only. Shells out to whatever `git` you
have on PATH.

## Quick start

    gitviz                    # current dir
    gitviz ~/utilitools/PYCalc
    gitviz --svg              # also export an SVG graph
    gitviz --limit 50         # cap at 50 commits
    gitviz --ref main         # log a single ref instead of --all

## Output

    ```
      repo: /Users/xavi/utilitools/PYCalc   branch: main

      ●  a1b2c3d  add units parser              xavi, 2 hours ago
      │
      ●  d4e5f6a  fix parser edge case           xavi, 3 hours ago
      │
      ◉  g7h8i9j  merge branch 'feature/help'    xavi, yesterday (HEAD -> main)
      │
      ●  j0k1l2m  help screen                    xavi, yesterday
      │
      ●  m3n4o5p  initial commit                 xavi, 3 days ago
    ```

    Node markers: ● linear commit, ◉ merge commit.

## SVG export

`gitviz --svg` writes to `~/Downloads/GitViz/graph_<timestamp>.svg` (or
`/sdcard/Download/GitViz/` on Termux). Curves connect parents to children,
each lane gets its own color, and merge commits are drawn with a hollow
node.

## Install

    python3 install_gitviz.py
    python3 install_gitviz.py --build
    python3 install_gitviz.py --uninstall

Install locations:

    macOS    ~/Library/Application Support/GitViz/
             launcher: /usr/local/bin/gitviz or ~/.local/bin/gitviz

    Linux    ~/.local/share/gitviz/
             launcher: ~/.local/bin/gitviz

    Termux   ~/.local/share/gitviz/
             launcher: ~/.local/bin/gitviz

    Windows  %LOCALAPPDATA%\GitViz\
             launcher: gitviz.bat in the same folder

## CLI

    gitviz [path] [--ref REF] [--limit N] [--svg] [--no-color]

## Notes

Lane coloring is deterministic — a commit keeps the same lane color
regardless of how many times you run GitViz on the repo.

Commits are loaded with `git log --all --date-order`, so all branches and
tags appear in the graph by default. Use `--ref main` (or any ref) to
restrict to a single line of history.

## License

MIT.
