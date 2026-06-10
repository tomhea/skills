#!/usr/bin/env python3
"""Compile a FlipJump program with --werror and check its stdout byte-for-byte.

Why this exists: "it compiled" says nothing about correctness, and on Windows a
shell pipe (`echo x | fj`) injects CRLF that silently breaks byte comparisons.
This harness compiles with `--werror` (so missing/unused `@` labels and globals
missing from a `<` clause become hard errors, caught fast by the assembler) and
runs the program through the flipjump Python module, comparing raw bytes — no
shell, no newline translation.

Dependency-free beyond `pip install flipjump` (which also installs the `fj` CLI).
Run with your python3 launcher (on Windows that's `py`, not `python3`):

    py fj_verify.py prog.fj                      # compile (--werror) + run, print stdout
    py fj_verify.py prog.fj in.bin out.bin       # also assert stdout == out.bin

Or import it (the primary use):

    from fj_verify import verify, verify_source
    verify("prog.fj", in_bytes=b"12\\n30\\n\\0", out_bytes=b"42\\n")
    verify_source("stl.startup\\nstl.output \\"hi\\"\\nstl.loop\\n",
                  in_bytes=b"", out_bytes=b"hi", name="hi")

Convention reminders the harness assumes:
  - stream/line-reading programs end their .in with a `\\0` EOF sentinel.
  - .out holds the exact expected bytes (LF only; no CRLF).
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from flipjump import run_test_output


def verify(fj_path, in_bytes: bytes, out_bytes: bytes, *, w: int = 64) -> bool:
    """Compile fj_path with --werror, run it on in_bytes, assert stdout == out_bytes."""
    fj_path = Path(fj_path)
    fjm = Path(tempfile.gettempdir()) / (fj_path.stem + ".fjm")

    asm = subprocess.run(
        ["fj", "--asm", str(fj_path), "-o", str(fjm), "-w", str(w), "--werror"],
        capture_output=True,
        text=True,
    )
    if asm.returncode != 0:
        tail = (asm.stdout + asm.stderr)[-1500:]
        print(f"COMPILE FAILED ({fj_path.name}):\n{tail}")
        return False

    try:
        run_test_output(
            fjm,
            in_bytes,
            out_bytes,
            should_raise_assertion_error=True,
            print_time=False,
            print_termination=False,
        )
    except AssertionError as e:
        print(f"OUTPUT MISMATCH ({fj_path.name}): {e}")
        return False

    print(f"OK {fj_path.name}")
    return True


def verify_source(source: str, in_bytes: bytes, out_bytes: bytes, *, w: int = 64, name: str = "prog") -> bool:
    """Same as verify(), but takes .fj source text instead of a path."""
    tmp = Path(tempfile.gettempdir()) / f"{name}.fj"
    tmp.write_text(source, encoding="utf-8", newline="\n")
    return verify(tmp, in_bytes, out_bytes, w=w)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    path = sys.argv[1]
    in_b = Path(sys.argv[2]).read_bytes() if len(sys.argv) > 2 else b""
    out_b = Path(sys.argv[3]).read_bytes() if len(sys.argv) > 3 else None
    if out_b is None:
        # No expected-output file: just compile (--werror) and run, echo the result.
        ok = verify(path, in_b, b"", w=64)  # will report mismatch unless output is empty
        sys.exit(0 if ok else 1)
    sys.exit(0 if verify(path, in_b, out_b) else 1)
