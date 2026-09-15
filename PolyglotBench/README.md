# PolyglotBench

Run the same tiny programs in many languages and compare their output.
Sibling of PYCalc, UnitForge, and Nota.

## What it does

For each problem in `problems/`, PolyglotBench finds every language
implementation, compiles if needed, feeds each test case to stdin, and
compares stdout to the expected value in the problem's `spec.json`. It
prints a per-problem table plus a summary.

Languages whose toolchains are not installed are marked SKIP, not FAIL.

## Quick start

    python3 polyglotbench.py
    python3 polyglotbench.py --list
    python3 polyglotbench.py hello
    python3 polyglotbench.py fib --lang rust

## Layout

    polyglotbench.py           driver
    problems/
      hello/     spec.json + hello.{py,js,go,c,cpp,rs,rb,sh}
      fib/       spec.json + fib.{...}
      wordcount/ spec.json + wordcount.{...}

## Adding a problem

Create `problems/NAME/`. Add `spec.json`:

    {
      "description": "one line description",
      "cases": [
        { "stdin": "input text", "expected": "expected stdout\n" }
      ]
    }

Then drop in one file per language. The filename must be
`NAME` plus the language extension:

    python      .py
    javascript  .js
    go          .go
    c           .c
    cpp         .cpp
    rust        .rs
    ruby        .rb
    bash        .sh

Rerun the bench. PolyglotBench picks it up automatically.

## Output

    ```
      PolyglotBench  same programs, many languages
      ────────────────────────────────────────────────────────────
      available: python, javascript, go, c, cpp, rust, ruby, bash

      hello  Print Hello, World! to stdout
        bash         PASS         1/1        3.2ms
        c            PASS         1/1        1.8ms
        cpp          PASS         1/1        2.1ms
        go           PASS         1/1      180.4ms
        javascript   PASS         1/1       41.0ms
        python       PASS         1/1       12.7ms
        ruby         PASS         1/1       58.3ms
        rust         PASS         1/1       36.1ms
    ```

## CLI

    polyglotbench              run every problem
    polyglotbench NAME         run only NAME
    polyglotbench --lang LANG  run only LANG across all problems
    polyglotbench --list       list problems and available implementations
    polyglotbench --no-color   disable ANSI output

## Notes

The driver does not ship with any language. It shells out to whatever is
on PATH. If `go` is missing, `go` implementations are SKIP, not FAIL.
