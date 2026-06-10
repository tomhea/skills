# Array access in FlipJump

There is no `arr[i]` syntax. You index an array one of two ways. **Pick by when
the index is known.**

| Index known at... | Use | Cost |
|---|---|---|
| compile time | Mode 1 — address arithmetic | free (it's just a variable) |
| run time | Mode 2 — pointer + memory macros | a pointer op per access; thoroughly tested |

Both rest on the memory model: every cell — a `bit`, a `hex`, or a byte — occupies
one FJ op = `dw` (= `2*w`) bits of address space. So consecutive cells are `dw`
apart, and a `bit.vec N` / `hex.vec N` cell of width `N` units spans `N*dw`.

---

## Mode 1 — constant (compile-time) index

The address of cell `i` in an array based at label `arr`, where each cell is
`cell_size` units wide (bits for a `bit.vec`, hexes for a `hex.vec`):

```
arr + i*dw*cell_size
```

`i` and `cell_size` must be compile-time constants. The resulting address is just
a normal variable — pass it to any `bit.*` / `hex.*` macro. No init needed.

```fj
// Array of three 8-bit cells. Print cell 2 in decimal.  (verified: prints 30)
stl.startup
bit.print_dec_uint 8, arr + 2*8*dw       // cell_size = 8 (the vec width)
stl.output '\n'
stl.loop

arr: bit.vec 8, 10
     bit.vec 8, 20                        // contiguous, anonymous cells
     bit.vec 8, 30
```

For a `hex.vec` array of `HEX_LEN`-hex cells, cell `i` is `arr + i*dw*HEX_LEN`.
A `rep(N, i) ... arr + i*dw*cell_size ...` loop unrolls a fixed-size traversal at
compile time (the `i` there is the legal `rep` loop variable).

Prefer Mode 1 whenever you can — it costs nothing beyond the macro you were going
to call anyway.

---

## Mode 2 — runtime (pointer) index

A pointer is a `hex.vec w/4` (or `bit.vec w`) holding a **`dw`-aligned** address.
You set it, then read/write *through* it, and advance it.

**Init**: the pointer/memory macros are table-driven. Call `stl.ptr_init` once
(or just use `stl.startup_and_init_all`, which bundles it). Pointer *arithmetic*
(`hex.ptr_add` etc.) additionally needs `hex.init` — also covered by
`stl.startup_and_init_all`.

```fj
// Point at a cell, write through the pointer, read it back, advance, repeat.
// (verified: prints 75)
hw = w/4

stl.startup_and_init_all

hex.set hw, ptr, arr            // ptr -> arr[0]   (set pointer to a constant address)
hex.write_hex ptr, seven        // *ptr = 7
hex.read_hex  got, ptr          // got = *ptr
hex.print_as_digit 1, got, 0    // -> 7

hex.ptr_add ptr, 1              // advance one cell (stride dw)
hex.write_hex ptr, five         // *ptr = 5
hex.read_hex  got, ptr
hex.print_as_digit 1, got, 0    // -> 5

stl.output '\n'
stl.loop

ptr:   hex.vec hw               // a pointer is w/4 hexes wide
arr:   hex.vec 2
got:   hex.vec 1
seven: hex.vec 1, 7
five:  hex.vec 1, 5
```

### The macros (hex family; `@requires hex.pointers.ptr_init` unless noted)

| Purpose | Macro | Notes |
|---|---|---|
| set ptr to an address | `hex.set hw, ptr, addr` | `addr` is a constant label/value |
| read one hex | `hex.read_hex dst, ptr` | `dst = *ptr` |
| read one byte | `hex.read_byte dst, ptr` | `dst` is `hex[:2]` |
| read n hexes | `hex.read_hex n, dst, ptr` | leaves `ptr` unchanged |
| read + advance | `hex.read_hex_and_inc dst, ptr` | then `ptr += dw` |
| write one hex | `hex.write_hex ptr, src` | `*ptr = src` |
| write one byte | `hex.write_byte ptr, src` | `src` is `hex[:2]` |
| write n / write+inc | `hex.write_hex n, ptr, src` / `hex.write_hex_and_inc ptr, src` | |
| advance / retreat 1 cell | `hex.ptr_inc ptr` / `hex.ptr_dec ptr` | stride `dw`; `@requires hex.init` |
| advance / retreat k cells | `hex.ptr_add ptr, k` / `hex.ptr_sub ptr, k` | **`k` is a compile-time constant** |

(Bit-family equivalents exist — `bit.ptr_inc`, `bit.pointers.*` — but the hex
pointer/memory macros are the well-trodden, heavily-tested path.)

### Indexing by a RUNTIME `i`

`hex.ptr_add ptr, k` takes a **constant** `k`, so you can't `ptr_add` by a runtime
index directly. Use the **indexed (nth) pointer macros** — they compute the address in
O(w) (not O(i)) and work for negative `i` too:

| Purpose | Macro |
|---|---|
| address of i-th op | `hex.ptr_index dst, ptr, i` → `dst = ptr + i*dw` |
| read i-th hex / byte | `hex.read_nth_hex dst, ptr, i` / `hex.read_nth_byte dst, ptr, i` |
| write i-th hex / byte | `hex.write_nth_hex ptr, i, src` / `hex.write_nth_byte ptr, i, src` |

`ptr` is a base **pointer** (`hex.vec w/4` holding the array's address — `hex.set w/4, ptr,
arr` once); `i` is a signed `hex.vec w/4` (**must be w/4-wide** — these read the index at width
w/4; a `hex.vec 4` index leaves garbage in the high hexes → bad address). `ptr`/`i` are preserved.
`@requires hex.init + stl.ptr_init` (covered by `stl.startup_and_init_all`).

The `read_nth_*`/`write_nth_*` are **single-unit** (one hex or one byte). For an array of
**n-hex cells**, scale the index yourself and use `ptr_index` + `read_hex n` / `write_hex n`:
`hex.mul w/4, sidx, i, n_const ; hex.ptr_index cell, ptr, sidx ; hex.read_hex n, out, cell`
(or store the array as **bytes** — values ≤ 255 — and use `read_nth_byte` directly).

Older hand-rolled approaches you'll still see in pre-existing code:
1. **Walk**: advance one cell per loop iteration until a counter reaches `i` (O(i)).
2. **Computed offset**: build `i*cell_size*dw` in a register and `hex.add` it onto the base.
   (The nth macros above now encapsulate exactly this.)

### The whole runtime pattern, in four moves

Every pointer traversal is the same four steps — all shown runnable in the Mode 2
example above:
- declare the array: `array: hex.vec CELL_HEX_LEN * MAX_SIZE`.
- point at the base each pass: `hex.set hw, array_ptr, array`.
- advance one cell per step: `hex.ptr_add array_ptr, CELL_HEX_LEN`.
- read/write through it: `hex.read_hex CELL_HEX_LEN, dst, array_ptr` /
  `hex.write_hex array_ptr, src`.

### Gotchas

- **Stride is always `dw`.** `ptr_inc`/`read_*_and_inc` advance by one FJ op =
  one hex = one byte = `dw`. There is no separate byte-stride increment.
- **Pointers must be `dw`-aligned** (every pointer macro `@Assumes` it). Addresses
  of `vec` cells are aligned by construction; don't hand-build misaligned ones.
- **Init before use** — forgetting `stl.ptr_init` gives a macro-resolve "label not
  found", same failure mode as forgetting `hex.init` (see SKILL.md).
- A pointer is `w/4` hexes (or `w` bits) wide — size it to the machine address,
  not to the cell.

### Cost — the indexed (`nth`/`ptr_index`) ops are O(w), and it bites twice

`ptr_index` (and the `read_nth_*`/`write_nth_*` built on it) is **O(w)**: each call
expands to ~`w` ops *and* runs ~`w` steps. That's fine occasionally, but it dominates
when you do many of them:

- **Compile blow-up if you UNROLL them.** A grid validator that `rep`-unrolled 243
  indexed reads took **~7 minutes to assemble** (each expansion is O(w) ops). Never
  bulk-unroll indexed access — write a **runtime loop** with one copy of the body.
- **Runtime blow-up from the count.** ~729 indexed accesses at `w=64` ran ~12 s in the
  interpreter. Cut it: (a) **minimize indexed ops per iteration** — e.g. replace an
  indexed `seen[v]` array with a handful of dispatched `bit.bit`s / fixed registers when
  the index range is tiny; read sequential data with `read_byte_and_inc` (a cheap O(1)
  walk) instead of `nth`; (b) **drop to `w=32`** (set the program's `word_size`) when the
  values fit — it halves every O(w) op for both compile and run.

So: estimate `nth_count × w` before writing. If it's large, restructure (runtime loop,
fewer indexed ops, smaller `w`) rather than discovering a multi-minute compile or
multi-second run after the fact.
