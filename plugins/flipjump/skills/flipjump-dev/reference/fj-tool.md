# The `fj` tool — reference

The `fj` script ships with the `flipjump` Python package and is the only command you need to write, run, and debug FlipJump programs.

## Contents

- [Install](#install)
- [Assemble + run (the main workflow)](#assemble--run-the-main-workflow)
- [Assemble only, run later](#assemble-only-run-later)
- [Useful flags](#useful-flags)
- [Feeding stdin](#feeding-stdin)
- [Debug flags](#debug-flags-when-output-is-wrong-or-the-program-doesnt-halt)
- [Reading errors](#reading-errors)
- [Contributing to flipjump and its testing infrastructure](#contributing-to-flipjump-and-its-testing-infrastructure)

## Install

```bash
pip install flipjump
```

`fj` is on `PATH` after install. Optional extras:

```bash
pip install flipjump[stats]     # adds plotly for macro-usage stats
pip install flipjump[tests]     # adds pytest + extras — only needed for the upstream test suite (see last section)
```

## Assemble + run (the main workflow)

```bash
fj program.fj
```

Output: a few timing lines (`parsing: …`, `macro resolve: …`, `labels resolve: …`, `create binary: …`, `loading memory: …`), then your program's stdout, then a `Finished by looping after N ops executed; ...` line on clean halt.

## Assemble only, run later

```bash
fj --asm program.fj -o program.fjm     # write the assembled .fjm
fj --run program.fjm                   # run a previously-assembled .fjm
```

Useful when you want to run the same program multiple times with different stdin, or when you want to keep the build artifact for distribution.

## Useful flags

(Flag names verified against `fj --help` — note the underscores in the multi-word ones.)

- `-w 64` — memory width in bits. Default `64`. Use `-w 16` or `-w 32` for tiny programs.
- `--werror` — treat all assemble warnings as errors. Use it on every authoring compile; it's what catches `@`/`<` clause mistakes early (see SKILL.md "Verification workflow").
- `-s` / `--silent` — suppress the assemble/run timing lines and run statistics (clean output for diffing).
- `--no_stl` — don't auto-include the standard library. Only for hand-written tests that deliberately avoid STL.
- `--no_output` — run without printing the program's stdout.
- `-t` / `--trace` — print every executed opcode (very verbose; small programs only).
- `--stats` — show macro code-size statistics after assembling (where your program-space goes).
- `-h` / `--help` — full flag list.

## Feeding stdin

stdin works directly. Prefer redirecting from a file whose bytes you control:

```bash
fj program.fj < input.bin
```

`echo "hi" | fj program.fj` also works on Unix shells — but NOT reliably on Windows, where the shell injects CRLF into the stream and silently breaks byte-exact behavior (see SKILL.md "Verification workflow"). When the exact bytes matter, write the input file from a script (or drive the run from Python via `reference/fj_verify.py`).

Macros that read input (`bit.input_bit`, `bit.input`, `hex.input_hex`, `hex.input_as_hex`, etc.) read from stdin in the natural way.

## Debug flags (when output is wrong or the program doesn't halt)

- (no flag) → on a failed run (program didn't halt via `stl.loop`), shows the last 10 executed addresses with short labels.
- `-d` / `--debug [PATH]` → keep full debug info (verbose label names — a "macro-stack" per address). When assembling+running in one shot, give NO path and a temp file is used: `fj -d program.fj`. The payoff: failure traces and breakpoints now show full macro-stack names per executed op — the *deepest* entry usually points at the macro that ran past where it should have stopped. (The file itself is for `fj`'s consumption, not for reading; the names appear in `fj`'s own printed trace.) With `--asm`, pass a path (`-d dir/debug.fjd`) to save it for a later `fj --run prog.fjm -d dir/debug.fjd`.
- `--debug-ops-list LEN` → show the last LEN executed opcodes (instead of 10) when a run fails.
- `-b NAME [NAME ...]` → pause on labels matching these exact names (needs `-d`).
- `-B NAME [NAME ...]` → pause on any label whose name contains one of these (needs `-d`).

## Reading errors

- **Compile-phase errors** appear under `parsing` / `macro resolve` / `labels resolve` lines. Most common:
  - "label X not found" → missing init macro (X is the unbuilt symbol). Switch `stl.startup` to `stl.startup_and_init_all`.
  - "X redefined" → namespacing conflict; two macros or labels with the same fully-qualified name.
- **Runtime "errors"** are just non-halting traces. If you see `Finished by looping after N ops` you ran to completion. If you don't see that, the trace shows the last N addresses; combined with `-d`, you can see which macros were on the stack at each.

## Contributing to flipjump and its testing infrastructure

**Not needed for writing FlipJump programs.** Skip this section if you're just writing and running a `.fj` file — `fj program.fj` is all you need. This material is only for opening a PR against `tomhea/flip-jump` or for running the upstream regression tests against your own copy of the STL.

### Running the upstream test suite

The upstream repo has a pytest harness driven by CSV tables. Install with `pip install flipjump[tests]` (or `poetry install --extras tests` if working inside the repo), then from the repo root:

```bash
pytest                   # fast group (default)
pytest --medium          # medium group
pytest --hexlib          # full hex-library exercises
pytest --slow            # everything else marked slow
```

Each test runs the assembler and the runtime; stdout from each program is compared exactly to a `.out` file.

### Adding a new test

Tests live in `tests/tests_tables/test_{compile,run}_{fast,medium,hexlib,slow}.csv`. One row per test. Schema:

```
# compile CSV (test_compile_<group>.csv):
# test_name, .fj source, output .fjm path, w, version, flags, use_stl, treat_warnings_as_errors
my_test, programs/foo/bar.fj, tests/compiled/foo/bar.fjm, 64, 3, 0, True, True

# run CSV (test_run_<group>.csv, matching test_name):
# test_name, .fjm path, stdin path (or empty), expected stdout path, stdin_is_binary, stdout_is_binary
my_test, tests/compiled/foo/bar.fjm, , tests/inout/foo/bar.out, False, False
```

The pytest harness reads both CSVs, runs compile then run, and diffs stdout against the named `.out` file. A test that needs stdin gets a `.in` file in `tests/inout/` referenced from the run CSV.
