# Quick signatures — the macros you reach for constantly

A fast lookup for the handful of macros used in almost every program, with the
arg orders that are easy to get wrong. Signatures verified against
`flipjump/stl/` (file:line cited). For anything not here, go to fjdocs
(`reference/docs-map.md`); don't guess.

Entries marked **(git main)** postdate the 1.3.0 PyPI release — see the version note in
SKILL.md "Required setup". Cited line numbers are as of git main (2026-06) and drift over
time — trust the file name, verify the line.

Many come in a **1-unit** form and an **n-unit** form — the arity is part of the
identity (see SKILL.md "Arity is part of the macro identity").

## I/O — the classic confusions
- `bit.input dst` — read **one byte** into a `bit[:8]`. `bit.input n, dst` — n bytes. `bit.input_bit dst` — one bit. (`bit/input.fj:9,18,26`)
- `bit.print x` — print **one byte**. `bit.print n, x` — n bytes. (`bit/output.fj:19,25`)
- `bit.output x` — prints **ONE BIT**, not a byte. Reaching for `bit.output` to print a character is the classic bug; use `bit.print`. (`bit/output.fj:4`)
- `stl.output "str"` / `stl.output 'c'` — print a string / char literal. (`runlib.fj:165`)

## Decimal / hex — parse and print
- `bit.print_dec_uint n, x` — unsigned decimal, no leading zeros. (`bit/output.fj:150`)
- `bit.print_dec_int n, x` — signed decimal (restores `x` after). (`bit/output.fj:227`)
- `bit.ascii2dec error, dec, ascii` — ASCII digit → 4-bit value; `error`=1 if not `0`-`9`. **Order: error, dec, ascii.** (`bit/casting.fj:93`)
- `bit.ascii2hex error, hex, ascii` — same shape for `0-9a-fA-F`. (`bit/casting.fj:120`)
- `bit.mul10 n, x` — `x *= 10` (the Horner step in decimal reading). (`bit/mul.fj:5`)

### Hex equivalents (need `hex.init`; `n` counts hexes = 4-bit units)
- `hex.print_dec_uint n, x` / `hex.print_dec_int n, x` — decimal, no leading zeros. (`hex/output.fj:219,230`) **(git main)**
- `hex.input_dec_uint n, dst, error` / `hex.input_dec_int n, dst, error` — read an ASCII decimal (signed form allows a leading `-`) until `\n`/`\0`(EOF); **jump to `error` on any non-digit byte**. The inverse of the printers — no manual digit loop needed. (`hex/input.fj:163,178`) **(git main)**
- `hex.input_dec_uint_until n, dst, stop_byte` / `hex.input_dec_int_until n, dst, stop_byte` — the **primitives** behind the two readers above: read digits (signed form allows a leading `-`), **stop at the first non-digit byte** and write it to `stop_byte[:2]` (an *output*) — **no error label**, every input is valid. For parsing a decimal field out of the middle of a line, where the caller inspects `stop_byte` (`','`/`':'`/`'.'`/`'\n'`/…) to know the delimiter. (`input_dec_uint/int` are thin wrappers that just check `stop_byte ∈ {'\n','\0'}` and jump `error` otherwise.) (`hex/input.fj`) **(git main)**
- `hex.print_as_digit n, x, use_uppercase` — print `x` as **exactly n hex digits**, MSB-first, leading zeros kept (the fixed-width byte/word dump: `hex.print_as_digit 2, b, 0` → `05`). `hex.print_uint n, x, prefix, upper` instead *strips* leading zeros (for numbers). (`hex/output.fj:151,161`)
- `hex.mul10 n, x` — `x *= 10`. (`hex/mul.fj:36`) **(git main)**

## Compare / branch  (label order is the trap)
- `bit.cmp n, a, b, lt, eq, gt` — jump `lt` if a<b, `eq` if a==b, `gt` if a>b. (`bit/cond_jumps.fj:80`)
- `hex.cmp n, a, b, lt, eq, gt` — same, unsigned (MSB-first); needs `hex.cmp.init`. (`hex/cond_jumps.fj:120`)
- `hex.scmp n, a, b, lt, eq, gt` — **SIGNED** two's-complement compare (sign-bias; `a,b` unmodified); needs `hex.cmp.init`. Use this for signed `hex.vec` ordering — `hex.cmp` is unsigned only. (`hex/cond_jumps.fj:209`) **(git main)**
- `hex.min n, dst, a, b` / `hex.max n, dst, a, b` — unsigned min/max into `dst` (must be distinct from `a`,`b`); needs `hex.cmp.init`. (`hex/cond_jumps.fj:168,184`) **(git main)**
- `bit.if0 x, l0` / `bit.if0 n, x, l0` — jump `l0` if (all-)zero. `bit.if1` likewise. The **1-bit** form takes no `n`. (`bit/cond_jumps.fj:45,53`)
- For `bit.if x, l0, l1` the **first label is the FALSE branch** (see SKILL.md).
- `stl.comp_if0 c, l` / `stl.comp_if1 c, l` — **compile-time** branch on a constant.

## Move / set / clear / negate
- `bit.mov dst, src` / `bit.mov n, dst, src` — aliasing-safe (skips if dst==src). (`bit/memory.fj:73,83`)
- `bit.zero bit` / `bit.zero n, x` ; `bit.one bit` / `bit.one n, x`. **1-bit form takes no `n`.** (`bit/memory.fj:35,41,48,55`)
- `bit.not dst` / `bit.not n, dst` — flip bit / flip n bits. (`bit/logics.fj:111,118`)

## Arithmetic
- `bit.add n, dst, src` (`dst += src`) ; `bit.sub n, dst, src`. (`bit/math.fj:80,91`)
- `bit.inc n, x` ; `bit.dec n, x`. (`bit/math.fj:34,47`)
- `bit.neg n, x` (two's-complement negate).
- `bit.div n, a, b, q, r` — `q = a/b`, `r = a%b` (unsigned); **`a` is preserved, NOT divided in place** — for `a /= b` do `bit.div n, a, b, q, r` then `bit.mov n, a, q`. `bit.idiv` is signed. (`bit/div.fj:108`)
- **Hex mul/div use OUTPUT operands and a different arg order than bit** (a `bit.vec 16` maps to a `hex.vec 4`; `bit.vec 32` → `hex.vec 8`):
  - `hex.add n, dst, src` / `hex.sub n, dst, src` / `hex.inc n, x` / `hex.dec n, x` / `hex.neg n, x` — in-place, like `bit.*`.
  - `hex.mul n, res, a, b` — `res = a*b`. **`res` is an output and must NOT alias `a`/`b`** (it's zeroed first), unlike `bit.mul`'s alias-safe in-place `dst*=src`. Low-`n` products are two's-complement-correct, so this also works for signed `a,b` (when no overflow). (`hex/mul.fj:53`)
  - `hex.div n, nb, q, r, a, b, div0` — `q=a/b`, `r=a%b` (unsigned; `q,a` are `[:n]`, `r,b` are `[:nb]`); jumps to `div0` if `b==0`. Order = widths, OUTPUTS `q,r`, INPUTS `a,b`, then the div-by-zero label — *not* `bit.div`'s order. `hex.idiv n, nb, q, r, a, b, div0, rem_opt` is signed. (`hex/div.fj:11,86`)
- `bit.shl n, x` / `bit.shl n, times, x` ; `bit.shr` likewise. **`times` is a COMPILE-TIME constant** (it `rep`s), so you can't shift by a runtime amount — loop shift-by-1 instead. (`bit/shifts.fj`)

## Inits (what needs setting up)
- Pure `bit.*` arithmetic/logic/IO: nothing beyond `stl.startup`.
- Any `hex.*` table op (`hex.add/cmp/if/mul`, pointer/memory ops): needs `hex.init` (or the specific `hex.<op>.init`).
- Pointer + memory macros: need `stl.ptr_init`.
- **`stl.startup_and_init_all` covers all of the above** — use it whenever you touch hex, pointers, or the call stack.

## Idioms (one-liners worth memorizing)
- **bit `k` of a byte `ch`** (a `bit.vec 8`) lives at `ch + k*dw`.
- **case-flip** a letter: toggle bit 5 → `bit.not ch + 5*dw` (ASCII upper/lower differ by `0x20`).
- **range check** `lo <= ch <= hi`: two `bit.cmp`s (`ch` vs `lo` then vs `hi`).
- **read a decimal** into `value[:n]`: loop `bit.input ch`; on a digit do `bit.mul10 n, value` then `bit.ascii2dec err, digit, ch` then `bit.add n, value, digit`; stop at `\n`/`\0`. (In hex-land, just call `hex.input_dec_uint`/`int` — it does this for you.)
- **array cell `i`** (constant `i`): `arr + i*dw*cell_size` — see `reference/array-access.md`.
