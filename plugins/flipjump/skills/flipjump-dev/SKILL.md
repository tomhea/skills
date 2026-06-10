---
name: flipjump-dev
description: Use when writing or improving FlipJump code. Helps produce correct, efficient, well-tested FlipJump programs — structuring the program, applying STL macros and idioms, optimizing for speed and size, and verifying behavior with tests.
---

# FlipJump development

## What FlipJump is, in three sentences

FlipJump is a one-instruction language. The single instruction is `a;b` — flip the bit at address `a`, then jump to address `b`. Every program — arithmetic, I/O, function calls, the lot — is composed from that op via macros, the most important being the standard library at `flipjump/stl/`.

## Required setup

```bash
pip install flipjump
```

`fj` is on `PATH` after install. Every command in this skill uses that script.

## A complete runnable program

Verified by compiling and running. Use this as the orientation pattern; adapt by changing the body, not the skeleton.

```fj
// sum.fj — read two decimal numbers from stdin, print their sum.

hw = w/4                            // number width: one full word, counted in hexes

stl.startup_and_init_all            // hex ops dispatch through tables; this builds them

hex.input_dec_uint hw, a, bad       // parse an ASCII decimal (ends at '\n') into a
hex.input_dec_uint hw, b, bad
hex.add hw, a, b                    // a += b
hex.print_dec_uint hw, a
stl.output '\n'
stl.loop                            // halt

bad:
    stl.output "bad input\n"
    stl.loop

// Data lives AFTER stl.loop — executing it would be undefined behaviour.
a: hex.vec hw, 0
b: hex.vec hw, 0
```

Run it, feeding stdin from a file (not `echo |` — see the Windows CRLF warning in the verification workflow below):

```
$ fj sum.fj < sum.in        # sum.in holds "12\n30\n"
42

Finished by looping after 0.060s (27,211 ops executed; 81.63% flips, 85.62% jumps).
```

And test the *other* path too — every branch gets its own input:

```
$ fj sum.fj < bad.in        # bad.in holds "12\n3x\n"
bad input

Finished by looping after 0.023s (9,109 ops executed; 79.10% flips, 99.01% jumps).
```

The `Finished by looping` line is the clean-halt signal; the program isn't done until that line appears AND everything printed before it is exactly right.

## The single most common first mistake

**Using any `hex.*` operation without first calling its init macro.** Hex ops (`hex.add`, `hex.cmp`, `hex.if`, `hex.mul`, the table-driven pointer ops, etc.) dispatch through precomputed truth tables, and those tables only exist if you call `hex.init` (which builds all of them) or the specific `hex.<op>.init`. Forget it and you'll get a confusing "label not found" / "undefined symbol" error at the macro-resolve phase — the macro you called looks fine; it's a symbol it references that's unbuilt.

Fix that always works: replace `stl.startup` with `stl.startup_and_init_all` at the top of your program. That bundles `stl.startup` + `hex.init` + `stl.ptr_init` + `stl.stack_init 100`, covering hex ops, pointer ops, and the function-call stack. The reason: a small program-space cost in exchange for never having to think about which init you need.

## Bit vs hex — when to pick which

**Bit** ops are direct: explicit `;` flips and `wflip`s. No init, no table cost, smaller program-space per primitive op, slower per useful op when n is large.

**Hex** ops dispatch through a precomputed 256-entry truth table. ~4× faster per nibble in tight loops; costs ~6500 bits of program space for the full `hex.init` (at `w=64`); requires calling the init macro first.

Heuristic: **default to `hex.*`.** It's ~4× cheaper per useful op, so for anything that reads/compares/prints bytes or numbers — including in a loop — `hex.input`/`hex.print`/`hex.cmp 2`/`hex.input_dec_*` beat their `bit.*` equivalents and keep runtime down. Reserve `bit.*` for what is *genuinely* one-bit: a boolean flag (`bit.bit` + `bit.if0/if1`), a single-bit test (e.g. parity = bit 0), explicit per-bit manipulation (printing an 8-char binary string), or a tiny no-arithmetic one-off where pulling in `hex.init` isn't worth it. A byte read+branch is *not* a reason to use `bit.*` — use `hex.input` + `hex.cmp 2`. (Whole-byte work with `hex` needs `stl.startup_and_init_all`, not bare `stl.startup`.)

## Optimizing for speed and size

The levers, in the order they usually pay off:

1. **Pick hex over bit** (above) — ~4× per useful op, the single biggest multiplier.
2. **Check the cost before committing.** Every macro's fjdocs page documents its `@`-counted time/space complexity (`// Complexity:` in the source). Glance at it before putting a macro inside a hot loop; an O(w) macro in an O(n) loop is where runtime goes.
3. **Indexed pointer access is O(w) per call — twice.** `hex.ptr_index` / `read_nth_*` / `write_nth_*` each expand to ~`w` ops AND run ~`w` steps. Never `rep`-unroll them (compile-time blow-up: ~7 minutes to assemble 243 unrolled indexed reads), and minimize the count per iteration (runtime blow-up: ~729 of them ≈ 12 s interpreted). Walk sequential data with `read_byte_and_inc` (O(1)) instead. Details and restructuring tactics in [`reference/array-access.md`](reference/array-access.md).
4. **Shrink the word width.** `-w 32` (or `-w 16` for tiny programs) when all values fit — it halves (or quarters) every O(w) op for both compile and run.
5. **`rep` trades program size for speed.** It unrolls at compile time, so a `rep` over a large count multiplies program size; a runtime loop keeps one copy of the body. Unroll only short, hot, fixed-count bodies.

## Memory model — the one weird thing

Three constants that appear everywhere:

- `w` = machine word width (typically 64).
- `dw` = `2*w`. The size of one FJ op (flip-target word + jump-target word).
- `dbit` = `w`. The offset into a bit-variable's word at which the "data bit" lives.

The non-obvious part: a `bit`, a `hex`, AND a byte all occupy the same `dw` bits of address space — one FJ op. A `bit` uses bit `dbit`; a `hex` uses bits `dbit..dbit+3`; a byte uses bits `dbit..dbit+7`. They're packed into one op, not separate ops.

Concrete consequence: **`hex.ptr_inc ptr` advances `ptr` by `dw`, which is exactly "next FJ op" = "next hex" = "next byte"**. The same `ptr_inc` is correct for both `hex.write_hex_and_inc` and `hex.write_byte_and_inc`. There is NOT a separate "byte-stride" `ptr_inc` — there can't be, because a byte and a hex have the same address footprint.

**Indexing by hand uses the same `*dw` stride.** Element `k` (0-indexed) of a `bit.vec n` lives at `var + k*dw`, and bit `k` *within* a byte/hex lives at `var + k*dw` too — because every bit occupies one whole FJ op. So the ASCII case-bit (bit 5) of a byte `ch` is at `ch + 5*dw`, NOT `ch + 5`; the high nibble of a byte is at `ch + 4*dw`. Writing `ch + 5` (forgetting the `*dw`) silently targets the wrong address — a classic source of "flipped the wrong bit" bugs.

**A byte has TWO encodings, and they don't interchange.** This is subtle and has bitten hard in practice:
- **Register form** (`hex.vec 2`) — what `hex.input`, `hex.print`, `hex.cmp 2`, and all hex arithmetic
  use. It's **two ops**: low nibble at `b`, high nibble at `b+dw` (`hex.input` = two `input_hex`;
  `hex.print` = `output b` + `output b+dw`). Array element `k` of register-form bytes is at `b + k*2*dw`.
- **Packed form** — what `hex.write_byte`/`read_byte`/`write_byte_and_inc`/`read_byte_and_inc`/
  `read_nth_byte`/`write_nth_byte` use, and what `ptr_inc` strides over. It's **one op** (8 data bits,
  `dbit..dbit+7`). Consecutive packed bytes are `dw` apart, so element `k` is at `base + k*dw`, and
  `read_nth_byte … index k` reads that.

`read_byte`/`write_byte` are the *bridge*: they convert a packed byte in memory ↔ a register-form
`hex.vec 2`. The trap: **you cannot store with `write_byte_and_inc` (packed, 1 op apart) and then index
with `hex.cmp 2, arr + k*dw*2` (register stride, 2 ops apart)** — you'll read every other byte and
garbage. Pick one lane per array: register-form fixed slots (read each cell with `hex.input arr+k*dw*2`,
compare with `hex.cmp 2`) for small fixed grids, or packed + `read_nth_byte` for a runtime index — the
two array layouts and when to use each are in [`reference/array-access.md`](reference/array-access.md).

## Program skeleton

Every program is:

```fj
stl.startup                  // or stl.startup_and_init_all if using hex / pointers / stack
... your code ...
stl.loop                     // halt — terminates by self-looping
... data declarations ...    // bit.bit, bit.vec, hex.hex, hex.vec — MUST live below stl.loop
```

`stl.loop` compiles to `;$ - dw`, an infinite self-jump. Anything past it is unreachable as code, so it's the safe place for data. Data declarations placed ABOVE `stl.loop` get executed as instructions when control falls through; the program will do something undefined and almost certainly wrong.

**`stl.startup` and `stl.loop` are program bookends, never put them inside a helper `def`.** They appear exactly once per program: `stl.startup` at the very top of the file (not nested in any macro), `stl.loop` at the end of the mainline code. A `def` body that contains `stl.startup` would re-initialise the machine mid-run; one containing `stl.loop` would halt early. The STL itself obeys this — no macro body in `flipjump/stl/` contains either.

**Functionalize the body.** Once a program grows past ~20 lines, pull each logical step into its own named `def` rather than stacking everything in the mainline. Helpers receive their inputs as parameters and reach external data through the `< external_label` clause; they own neither the startup nor the halt. This mirrors how the STL is structured (each macro is a small focused job) and pays off on recursion, parsing, and sorts where helpers compose.

## Doc-comment vocabulary

Four conventions describe the entire STL at the source level. Read these on any macro page:

- `// Complexity: ...` (or split `Time Complexity:` / `Space Complexity:`) — the `@`-counted cost.
- `// @requires hex.add.init (or hex.init)` — declares an init dependency. Honour it or the compiler errors.
- `// @output-param NAME: ...` — documents a label exported via `> NAME` in the signature.
- `// @Assumes: ...` — a silent precondition the body relies on (e.g. `times <= n`, `dst and src do not alias`). Violating it doesn't always crash; sometimes you just get the wrong answer.

## `n > 0` is a hard precondition for every vector macro

Treat any `n` parameter as requiring `n > 0`. Several macros index `(n-1)*dw` outside their main loop — examples include `bit.idiv`, `hex.sign`, `bit.print_dec_int`, `bit.div_loop` — and `n=0` reads memory at offset `-dw`, with undefined results. Even macros that LOOK safe at `n=0` (because their body is just `rep(n, i) ...`) are still UB at `n=0` by convention. Don't pass `n=0` to ANY vector macro.

## Idioms that work

**Before you hand-roll a loop or a helper, assume the STL already has it — and check.** The STL is
broader than it looks, and re-implementing a macro it ships is the most common time-sink (it has
bitten repeatedly in practice: a min open-coded as a `cmp`+branch, a line reader rewritten three
times). The 30-second check that prevents it: skim `/stl/all_macros.html` (the alphabetical 1-line
index — fastest), or `grep -rn "def <verb>"` the installed STL source (the `flipjump/stl/` directory
inside your `pip install`'d `flipjump` package), for the *verb* you're about to write — `min`, `max`,
`abs`, `swap`, `mov`, `input_line`, `print_text`, `sort`, `count`, `reverse`. If a macro matches,
use it; don't reinvent. The entries below are the ones most often missed:

- **min / max** — `hex.min n, dst, a, b` / `hex.max n, dst, a, b` (and `bit.*`) set `dst` to the
  unsigned min/max and preserve `a`,`b` (`dst` must be distinct). Don't open-code a `cmp` + two movs.
- **Read a whole line into a buffer** — `hex.input_ptr_line ptr, len` reads bytes into the buffer at
  `*ptr` until `\n`/EOF and writes the count to `len[:w/4]` (the terminator is consumed, not stored);
  `hex.print_ptr_text ptr, len` / `hex.print_ptr_line ptr, len` print it back. Don't hand-roll the
  `input b` / `cmp '\n'` / `write_byte_and_inc` / `inc len` loop — see [`reference/line-buffer.md`](reference/line-buffer.md).
- **Print a signed number** — `bit.print_dec_int n, x` or `hex.print_int n, x, 0, 0`. Both correctly restore `x` after negation, so you can print the same variable twice in a row and get two identical signed outputs.
- **Decimal I/O in hex** — `hex.print_dec_uint n, x` / `hex.print_dec_int n, x` print a `hex.vec` in decimal, and `hex.input_dec_uint n, dst, error` / `hex.input_dec_int n, dst, error` read an ASCII decimal straight into a `hex.vec` (stopping at `\n`/`\0`, jumping to `error` on a bad byte). Don't hand-roll a digit loop for hex values — these are the inverse pair. For a decimal that ends at some **other delimiter** (`,`/`:`/`.`/`}`/…) — i.e. a field inside a larger line — use the primitives `hex.input_dec_uint_until n, dst, stop_byte` / `hex.input_dec_int_until n, dst, stop_byte`: they read digits and **stop at the first non-digit**, writing it to the *output* `stop_byte` (no error label — every input is fine; you inspect `stop_byte` to learn the delimiter). `input_dec_uint/int` are just these plus a check that `stop_byte` is `\n`/`\0`. Don't hand-roll a `read_num` loop. (For `bit.vec` decimals there is still no reader: loop `bit.input` + `bit.mul10` + `bit.ascii2dec` + `bit.add`; see `reference/quick-signatures.md`.)
- **Fixed-width hex print** — `hex.print_as_digit n, x, use_uppercase` prints `x` as **exactly n hex digits** (MSB-first, leading zeros kept) — that's the right one for a byte dump (`hex.print_as_digit 2, b, 0` → e.g. `05`). Don't write a 2-call `print_hex_byte` helper, and don't use `hex.print_uint` for this (it *strips* leading zeros, so it's for numbers, not fixed-width fields).
- **Aliasing-safe move** — `bit.mov` / `hex.mov` check `dst==src` at compile time via `stl.comp_if1` and skip the work. You don't need to roll your own zero+xor.
- **Carry chaining in hex** — the n-arity `hex.add n, dst, src` brackets its loop with `clear_carry` calls automatically. The single-hex `hex.add dst, src` does NOT auto-clear; the doc says "Relies on the add-carry, and updates it at the end." If you call single-hex `hex.add` standalone (not from inside `hex.add n, ...`), call `hex.add.clear_carry` first or you'll add a stale carry from a previous op.
- **String literals** — `bit.str "Hello"` allocates `(strlen+1)*8` bits (byte-rounded length plus a trailing null), so `bit.print_str` will stop at the null even without explicit length tracking. Even `bit.str ""` allocates 8 zero bits = a usable null terminator.
- **Single-byte read-and-echo loop** — the canonical input pattern (cat, filters, transforms):
  ```fj
  loop:
      bit.input ch
      bit.if0 8, ch, done      // treat a 0 byte as EOF / end-of-input
      bit.print ch
      ;loop
  done:
      stl.loop
  ```
  The variable lives at top level below `stl.loop` (`ch: bit.vec 8, 0`) and any enclosing `def` references it via `< ch`. To transform each byte (e.g. case-flip), mutate `ch` between the `bit.input` and `bit.print` — see the `*dw` bit-stride note in "Memory model". (Per "Bit vs hex", prefer the hex form for new code: `hex.input ch` into a `hex.vec 2`, `hex.if0 2, ch, done`, `hex.print ch`, with `stl.startup_and_init_all`.)
- **Reading to true EOF terminates the run before your check fires** — `hex.input`/`bit.input` past the end of input ends the program (cause `EOF`), so a loop that only stops on a sentinel you *read* must actually receive that sentinel. Two safe shapes: stop on a known terminator already in the data (`'\n'`), **or** make the driver append a `\0` byte so the loop's `if0`/EOF-check fires on a real read. A program that scans to end-of-input (no `'\n'` stop) needs that trailing `\0` in its input, or it halts with no output.
- **Halt the program** — `stl.loop`. Equivalent to `;$-dw`.

## Things that are easy to misread in FlipJump source

Recognising these up front avoids whole classes of false "this is buggy" conclusions when reading STL source.

- **`addr;` IS the flip operation**, not "no-op then jump-to-fall-through". Every FJ op is two words: flip-target + jump-target. `addr;` is shorthand for the op that flips the bit at `addr` and jumps to the next op in source. Reading `def exact_not dst { dst; }` as "this macro does nothing" is wrong — it flips `dst`. The reason it looks empty: a single FJ op is the WHOLE primitive operation, and `dst;` already says "flip `dst`".

- **Conditional-jump label order is `l0, l1` = "false-branch, true-branch"** in `bit.if x, l0, l1`: `x==0` → jump `l0`; else (`x==1`) → jump `l1`. The FIRST label is the FALSE branch. Macros like `bit.swap` use this in subtle ways (`.if a, a0, a1` followed by `.if b, end, notnot` vs `.if b, notnot, end`) — the label order in `.if` is what makes the swap correct. Reading the order backwards leads to "this macro looks buggy" when it isn't.

- **Arity is part of the macro identity** — `bit.input/1` (reads one byte into a `bit[:8]`), `bit.input/2` (reads n bytes), and `bit.input_bit/1` (reads one bit) are three different macros with different bodies. The fjdocs site always shows the `/<arity>` suffix on links and headings; preserve it when looking macros up. Saying "macro X does Y" without specifying arity loses information — e.g. `hex.pointers.xor_hex_to_flip_ptr` exists at both /1 and /2, with different bodies, and `@Assumes: bit_shift is divisible by 4` belongs only on /2.

- **Aliasing (same address) vs overlapping (distinct addresses, overlapping ranges) are different problems**. Most macros handle `dst==src` correctly because they have a compile-time `stl.comp_if1 (dst-src), ...` check. Almost none handle overlapping ranges (e.g. `bit.swap n, base, base+dw` corrupts because each per-bit swap operates on memory just written by the previous one). When a doc says "Unsafe if dst and src overlap! but safe if they are the exact same address", it means literally that.

- **`bit.print n, x` prints one BYTE; `bit.output bit` prints one BIT.** `bit.print ch` (where `ch: bit.vec 8, 0`) emits the one character that byte encodes. `bit.output` takes a single bit-address and emits its raw `0`/`1` signal — calling it on an 8-bit variable prints garbage (8 bit-chars instead of the character). Reach for `bit.print` for characters and `bit.print_dec_uint` / `bit.print_dec_int` for numbers; `bit.output` is only for raw single-bit I/O.

- **`bit.div n, a, b, q, r` does NOT divide in place** — it writes quotient→`q`, remainder→`r`, and leaves the dividend `a` UNCHANGED. So `bit.div n, x, ten, q, r` followed by `bit.print_dec_uint n, x` prints the original `x`, not `x/10`; to actually divide in place you need `bit.div n, x, b, q, r` **then `bit.mov n, x, q`**. The remainder-only pattern (`…, q, r` then read `r` for `a % b`) is the common *correct* use — it's the quotient that's easy to forget to move back out of `q`. Same for `hex.div`, `bit.idiv`, `hex.idiv`. (This silently produces wrong numbers and compiles clean — a domain cross-check is what catches it.)

- **Width-mismatched operands read past the end — silently, with a wrong answer.** `hex.<op> n, a, b` reads `n` nibbles of *both* `a` and `b`. So `hex.sub hw, idx, la` where `la` is a 2-nibble constant (`hex.vec 2, 'a'`) reads `hw` nibbles of `la` — the high nibbles are whatever sits in memory after it — and subtracts garbage. Likewise `hex.mov hw, two_nibble_dst, wide_src` overruns the dst. Fixes: do the op at the *narrower* width when the values fit and there's no borrow/carry across the boundary (`hex.sub 2, idx, la` touches only `idx`'s low byte), or declare the constant at the wide width (`hex.vec hw, 'a'`). This compiles clean and is only caught by checking the output — treat any width mismatch between an op's `n` and its operands' declared widths as a bug.

A general habit that helps with all four: when claiming a macro behaves a particular way, quote the exact source lines you're reasoning from, and trace concrete values through them. Lots of analysis errors come from reading source with the wrong sign or wrong label order in mind; concrete values catch the inversion.

## Naming trap — don't name a label `w`, `dw`, or `dbit`

Don't give a label or variable the name of a machine **constant** — `w` (word width),
`dw` (`2*w`), or `dbit` — because a constant always wins over a same-named label in
expressions, so every reference to your label silently resolves to the constant instead,
and these three are exactly the constants the STL's address arithmetic uses everywhere
(`var + k*dw`, `+dbit`). The compiler rejects this with a clear *"label `dw` … is also
defined as a constant"* error. Common parameter / loop-variable names like `n`, `i`, `d`
are **safe** — macro parameters and `rep` iterators are now isolated from your names, so
only the three machine constants are off-limits.

## Macro `@` / `<` clauses — the discipline `--werror` enforces

Every `def` declares the labels it touches, and `--werror` (and the test suite) reject any
mismatch. Getting these clauses wrong is the single most common authoring error — the
messages are precise, so trust them and fix the clause, don't fight it:

- **`@ l1, l2, …`** lists EXACTLY the macro's own inner labels (the `name:` targets in its
  body). Every listed label must be used (a `;name` or branch to it) and every inner label
  must be listed. Missing one a branch targets → *"label … used but isn't in the @ clause"*;
  listing one you don't use → *"unused labels: …"*.
- **`< x, y, …`** lists EXACTLY the GLOBAL labels this body names — and **passing a global as
  a macro argument counts as naming it** (`print_buffer buf, slen` makes `buf` and `slen`
  referenced *here*, so they go in this macro's `<`). It must NOT list globals that only the
  macros you *call* use — those belong in THEIR `<`. Over-listing → *"unused labels"*;
  under-listing → *"Used a not global/parameter/declared-extern label"*.
- **Every name in a `<` clause must be DECLARED as data** (`name: bit.vec …` / `hex.vec …`
  below `stl.loop`). A helper's scratch registers are globals — declare them. A `<`-listed
  name with no declaration assembles to *"Can't evaluate label …"* (an assemble-time, not
  parse-time, error — easy to miss).

**Derive both clauses mechanically from the body, don't guess** (this is the #1 source of
fix-and-retry cycles): `@` = the set of `name:` lines in the body; `<` = the set of names the
body *writes literally* (operands and macro-call args) that aren't this macro's own parameters,
minus any that are only ever named inside the helpers you call. Corollary: a helper's own
scratch lives in *that helper's* `<` and is declared once as data — the caller does **not**
relist it just because the helper uses it.

- **Thread control labels through helper chains.** A macro can only `;label` (or pass) a label
  that is its own inner `@` label *or* one it received as a parameter. So a deep helper that must
  jump to `main`'s `bad`/`error`/`done` needs `bad` passed as an arg at every level
  (`check_cell bidx, bad` ← `check_line …, bad` ← `main`). Forgetting one link gives *"Can't
  evaluate label … in expression"* at assemble time. This is how `error`/`yes`/`no`/`done` labels
  travel (the STL's own `hex.input_dec_uint n, dst, error` does exactly this).

Syntax traps with confusing error messages:
- **A `def` header must be on ONE physical line.** `def f a, b @ l1, l2 < x, y {` cannot wrap
  onto a second line — a newline inside the header gives a bare *"Syntax Error … token NL"*
  pointing at the `def` line, which doesn't obviously say "join the line".
- **In the header, `@` must come BEFORE `<`** (`def f a @ l1, l2 < g1, g2 {`). Writing them
  reversed (`< … @ …`) parses wrong and surfaces as a misleading *"Syntax Error … token `}`"* on
  the macro's *closing brace*, far from the actual mistake in the header.
- **`rep(n, i)` takes a single statement, NOT a `{ block }`, and cannot template label names.**
  `rep(n,i) { … }` is a syntax error on the `{`. For a multi-statement loop body or per-iteration
  labels, factor the body into a helper macro and rep-call it: `rep(8, i) do_cell i`. The helper
  uses `i` for addressing (`arr + i*dw*2`) and its OWN inner labels — each instantiation gets a
  fresh label scope, so there's no collision. (Non-contiguous indices: just call it explicitly,
  `do_cell 0` / `do_cell 1` / `do_cell 3` …, since `rep` only yields `0..n-1`.)
- **After `bit.cmp n, a, b, lt, eq, gt` (and `hex.cmp`) ALL THREE branches jump** — the next
  instruction is not a fall-through for eq/gt. If you mean "lt → handle, otherwise → print",
  give the print an explicit label and aim eq/gt at it (`…, handle, doprint, doprint`); never
  let eq/gt jump to a shared `done` that sits *past* the code they should run.
- Don't name a scratch label `w` / `dw` / `dbit` (see the naming trap above).

## Common errors and what they mean

- **"label not found" / "undefined symbol" at macro-resolve phase** → you used a `hex.*` op (or a pointer/memory op) without its init. Fix by switching `stl.startup` to `stl.startup_and_init_all` (covers `hex.init` + `stl.ptr_init` + the stack).
- **Program runs forever (no `Finished by looping...` line)** → either you forgot `stl.loop` at the end of your code, or a data declaration ended up above it and is being executed as instructions. Move data below `stl.loop`.
- **`Finished by ip<2w`, or `runtime-memory-error` at a giant address (bit 63 set)** → a `wflip`/jump resolved to garbage. The usual cause is an uninitialized or non-`dw`-aligned pointer. (Naming a label after a machine constant — see "Naming trap" above — used to crash this way too, but the compiler now rejects it at parse time.) Re-run with `fj -d labels.txt program.fj` and read the *deepest* macro on the last-executed ops — it points at where execution went wrong (details in `reference/fj-tool.md`).
- **Program doesn't halt and the cause isn't obvious** → same `fj -d labels.txt program.fj` workflow: the verbose label names show which macro ran past where it should have stopped.

## Verification workflow — the loop

Don't declare a program correct because it compiled. Run it.

1. **Write** the `.fj` file to disk: `stl.startup` (or `stl.startup_and_init_all`), your code, `stl.loop`, then data.
2. **Run** with `fj program.fj` (assembles and runs in one shot). Pipe in stdin if needed.
3. **Read the output.** The success signal is the `Finished by looping after N ops executed; ...` line at the end.
4. **If wrong output or no halt**, fix and repeat from step 2.
5. **Cover every behavior path.** Each branch the spec implies — the error label, the empty input, the boundary value — gets its own input and its own run, like the two runs of the anchor example above.

A FlipJump program is done when BOTH:
- The `Finished by looping ...` line is present (the program reached `stl.loop` and halted cleanly).
- Everything stdout-printed BEFORE that final line matches the intended output exactly.

If either fails, change the program and rerun. The reason "compiled successfully" isn't enough: compile success only means the macros expanded and labels resolved. It says nothing about whether the runtime produces the output you intended.

**Two author-time accelerators:**
- **Assemble with `--werror`**: `fj --asm program.fj -o out.fjm -w 64 --werror`. It promotes the cheap static warnings into hard errors the (fast) assembler catches *now* instead of at run/test time — an inner label used but missing from a macro's `@` clause, an *unused* `@` label, or a global referenced but absent from its `<` clause. (Authoring rule this enforces: every inner label goes in the macro's `@` clause; every external data label it references goes in the `<` clause.)
- **Compare output byte-for-byte, and don't trust a shell pipe on Windows** — `echo x | fj` injects CRLF and silently breaks the comparison. Drive the program from Python and compare raw bytes. The one-call form is `flipjump.assemble_and_run_test_output([Path('p.fj')], in_bytes, out_bytes, warning_as_errors=True, should_raise_assertion_error=False)` — it does compile(`--werror`) + run + byte-check and returns a bool, so a tight loop over many inputs needs no temp `.fjm` files (compile once with `flipjump.assemble(...)` + `flipjump.run_test_output(fjm, …)` if you want to reuse the binary). A ready-made harness is [`reference/fj_verify.py`](reference/fj_verify.py); the emit-and-verify loop is in [`reference/authoring-harness.md`](reference/authoring-harness.md).
- **An old/stale `flipjump` install lags the published macros.** If `fj` / `import flipjump` report that a macro *or a sub-macro it expands to* "isn't defined" (e.g. an older `bit.mul` calling a `mul.mul_add_if` helper its own `mul.fj` doesn't contain), or behavior matches an old version, your installed `flipjump` is behind the docs — **`pip install -U flipjump`**, and confirm the location with `python -c "import flipjump; print(flipjump.__file__)"`. (If you're developing flipjump itself from a clone rather than just using it, `pip install -e .` from the clone root makes `fj`/`import flipjump` resolve to your live working tree — STL `.fj` files included — so edits take effect with no reinstall.)
  - **Don't hand-roll a replacement for a macro that "doesn't resolve."** If fjdocs (or your installed STL source) clearly defines the macro, a resolve/runtime failure is almost always a stale install, not a real gap — upgrade the install, don't reinvent the macro. (Macros that have specifically tripped this on a behind-the-release install: `bit.mul` and its inner `mul.mul_add_if`; the `hex.input_dec_uint/int` decimal readers and `hex.mul10` / `hex.min` / `hex.max`; and the `hex.input_dec_*` "repeat" bug where a hex var named `d`/`i` collided with a truth-table loop var. All present and correct in current releases.)

## Where to find authoritative reference

Don't rely on memory for exact macro signatures — they're easy to get subtly wrong (arity, parameter order, `< require` clauses). Fetch the right page when in doubt.

**Primary**: https://fjdocs.tomhe.app — the rendered, navigable documentation site. Prefer it for everything.

**Fallback** (only when fjdocs is unreachable): the upstream source at https://github.com/tomhea/flip-jump/tree/main/flipjump/stl.

Common routing (full map in [`reference/docs-map.md`](reference/docs-map.md)):

| Question | Where to look |
|---|---|
| What does `bit.X` / `hex.X` / `stl.X` do? | `/stl/all_macros.html` — alphabetical index with 1-line summaries. |
| Full signature + complexity of one macro | `/stl/<file>/<macro>--<arity>.html`. |
| Which `*.init` does a hex op need? | The `@requires` line on that macro's page. |
| What does `@`, `dw`, `dbit` mean? | `/language/complexity.html` (and `/reference/glossary.html`). |
| How does FJ macro syntax work? | `/language/macros.html`. |
| A cookbook recipe for task X | `/cookbook/index.html`. |
| Concept overview (e.g. how table dispatch works) | `/reference/how-the-stl-works.html`. |
| Program structure, startup, halt | `/getting-started/anatomy.html`. |

For tool details (assembling, running, debugging, plus the testing infrastructure for contributing to flipjump), see [`reference/fj-tool.md`](reference/fj-tool.md).

**Project recipes** (this skill's own how-to references, distilled from real authoring campaigns):

| Need | Reference |
|---|---|
| Exact arg order / arity for the macros used constantly | [`reference/quick-signatures.md`](reference/quick-signatures.md) |
| Index an array (constant index vs runtime pointer macros) | [`reference/array-access.md`](reference/array-access.md) |
| Read a whole line into a buffer to reprint / tokenize / compare (reverse, repeat, word stats, substring search) | [`reference/line-buffer.md`](reference/line-buffer.md) |
| Emit a `.fj` and verify it byte-exact (`--werror` + raw-byte check) | [`reference/authoring-harness.md`](reference/authoring-harness.md) + [`reference/fj_verify.py`](reference/fj_verify.py) |
