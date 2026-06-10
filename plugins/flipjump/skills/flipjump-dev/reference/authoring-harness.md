# Authoring harness — emit a `.fj`, verify it byte-exact

When you're writing more than one or two programs, stop hand-running `fj` and
eyeballing output. Two pieces make the loop fast and trustworthy:

1. **A verify step that's honest** — compile with `--werror`, run through the
   Python module, compare raw bytes. (`reference/fj_verify.py`.)
2. **An emit step** — assemble the `.fj` text from parts so the header, `main`
   wrapper, helpers, and data are always shaped the same way.

This pays off enormously at scale: ~450 programs in one authoring campaign were written this way.

## Verify: `reference/fj_verify.py`

```python
from fj_verify import verify, verify_source

verify("factorial.fj", in_bytes=b"5\n\0", out_bytes=b"120\n")
verify_source(SRC_STRING, in_bytes=b"", out_bytes=b"hi", name="hi")
```

It compiles `fj --asm prog.fj -o … -w 64 --werror` and, only if that succeeds,
runs via `flipjump.run_test_output(...)` and asserts stdout equals `out_bytes`
**byte-for-byte**. Returns `True`/`False`; prints `OK`, `OUTPUT MISMATCH`, or
`COMPILE FAILED`. Run it with your python3 launcher that has `flipjump` installed
(on Windows that's `py`, not `python3`).

Why this beats `echo … | fj`:
- `--werror` turns the cheap static warnings into failures *here*, not later:
  an inner label used but missing from a macro's `@` clause, an **unused** `@`
  label, or a global referenced but absent from the `<` clause. The assembler is
  fast, so this is the cheapest place to catch them.
- Driving from Python avoids the Windows shell injecting CRLF into stdin/stdout —
  a silent source of byte-mismatch. Comparison is on raw bytes.

## Emit: assemble the `.fj` from parts

Every program has the same shape, so generate it rather than retype it:

```
// <Name>                     <- header line 1
                              <- blank
// <one-line description>     <- header line 2..

main                          <- top-level is just the macro invocation

def main @ <inner labels> < <globals> {
    stl.startup               <- startup/loop ONLY here, never in a helper
    ... body ...
    stl.loop
}

def helper ... { ... }        <- helper macros, each with a // comment
...

x: bit.vec 8, 0               <- data declarations last
```

A tiny `emit(name, desc, main_body, helpers, data, in_bytes, out_bytes)` that
string-joins those parts and then calls `verify` gives you: write intent →
get a clean, header-correct, byte-verified `.fj` + a pass/fail. Conventions that
earned their keep:

- **Byte-exact `.out`, LF only** — never `\r\n`. Build expected output as raw
  `bytes`, not shell text.
- **Compute the expected output with an oracle, don't hand-type it.** For any
  input→output transform (a cipher, a hash, RLE, a dump, base-N), write the spec's
  rule as 2-3 lines of Python and let *that* produce the `out_bytes` you verify
  against — `out = bytes((c ^ 7) for c in line) + b"\n"`. Byte-exact verification is
  only trustworthy when the expected bytes come from an independent correct
  computation; hand-typed expected output just encodes the same mistake twice. (This
  is what makes the emit→verify loop catch real bugs.) For fixed-output programs the
  `.out` *is* the spec, so write it directly; for transforms, oracle it.
- **Author in a Python script, never inline `python -c`/bash heredocs** when the
  source contains `\` or newlines. FlipJump string literals use `\\` for a backslash
  and `\n` for newline; routing that through a shell mangles it (a `\n` becomes a real
  newline, `\\` collapses). Use constants like `NL = chr(92)+"n"`, `BS = chr(92)` and
  build the `.fj` text in a `.py` file.
- **`\0` EOF sentinel** — programs that read a stream/line in a loop terminate on
  a `\0`; end every such `.in` with one. (Programs that read an exact fixed
  number of bytes don't need it.)
- **Header description is the single source of truth** — if you keep a spec list,
  make the `.fj` header line match it verbatim so the two never drift.

## What a production harness adds (campaign-coupled)

`fj_verify.py` is the decoupled, reusable core — it's all you need to author and
byte-verify standalone programs. A larger campaign usually wraps it with two
extra, project-specific responsibilities, worth re-creating if you run one:

- an **`emit(name, desc, body, helpers, data, in, out)`** that assembles the
  header + `main` + chosen helper macros + data from parts, so every program
  comes out shaped identically; and
- a **`register()`** that, after the `--werror` compile + byte-exact run, also
  appends the program's rows to the test tables and byte-matches the `.fj`
  header description against the spec list, so code and spec can't drift.

Both are coupled to a particular spec file and test harness, so treat them as a
design pattern to re-create per project — not a drop-in. The reusable part that
carries across projects is the decoupled `fj_verify.py` above.
