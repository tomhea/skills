# Reading a line into a byte buffer (store, reprint, tokenize)

When a program must STORE a line of input and then re-scan or reprint it — reverse,
repeat, tokenize into words, compare two lines, dedup — stream-and-echo isn't enough.
Use a **hex-pointer byte buffer**. This is the well-trodden path (the same hex-pointer
machinery as array indexing — see `array-access.md`); the patterns below are copy-paste-ready.

## The one stride fact that trips everyone

A byte in **memory** is ONE FJ op: `hex.write_byte`/`read_byte` move 8 bits in/out of a
single op, and `hex.ptr_inc` advances by exactly one byte (`dw`). So a buffer of N bytes is
`hex.vec N` (N ops), and `buf + k*dw` is byte `k`.

The **register** form of a byte is `hex.vec 2` — two 4-bit hexes — because `hex.input` /
`hex.print` unpack the byte into `x` (low nibble) and `x+dw` (high nibble). Don't confuse
the two: the buffer is `hex.vec N` (N byte-slots), the scratch byte you read/write through
it is `hex.vec 2`. Pointers are `hex.vec hw` where `hw = w/4`.

## Setup

```fj
hw = w / 4
CAP = 84            // max line length + slack

stl.startup_and_init_all      // hex.init + ptr_init + stack — pointer/byte ops need it
```

## Core helpers — now in the STL (`hex/strings.fj`)

These three are part of the standard library, so **just call them** — they keep their own
pointer / byte-register / counter scratch inline, so you declare only the buffer and a length:

All three take a **pointer** to the buffer (a `hex.vec w/4` holding its address):

```fj
hex.input_ptr_line ptr, len    // read from input into *ptr until '\n'/0-byte(EOF); len := bytes stored (terminator not stored)
hex.print_ptr_text ptr, len    // print len bytes from *ptr
hex.print_ptr_line ptr, len    // print from *ptr until '\n'/0-byte; a terminating '\n' is echoed; len := bytes (excl. terminator)
```

Data you declare (below `stl.loop`): `buf: hex.vec CAP` (one byte per slot) — or a `reserve`d
region for unbounded input — plus a pointer `p: hex.vec hw` and `len: hex.vec hw`. Point at the
buffer (`hex.set hw, p, buf`) then call. `main`'s `<` clause lists every global it names (the
buffer, pointer, lengths). Each call keeps its own scratch, so reusing `p` for a second buffer is fine.

If you need a custom variant (different terminator, transform-while-reading), the bodies are a
straightforward read/write loop over the byte-pointer macros — read the `hex/strings.fj` source
on fjdocs (`/stl/hex/strings.html`) and adapt it.

## Two-pointer compare (palindrome, prefix/suffix, substring search)

Read a byte at a position with `hex.read_byte b, ptr` (no inc), compare two with
`hex.cmp 2, a, b, …`. Walk to an offset by looping `hex.ptr_inc`/`hex.ptr_dec` (there is no
runtime `ptr_add` — `ptr_add`'s amount is a compile-time constant). A reusable matcher that
leaves the caller's pointer put (note the caller's labels are passed as args):

**String/buffer equality is just this loop — don't generate a per-string macro.** To test
a line against a fixed literal, store the literal in a second buffer (`pat: hex.vec …` of
bytes), check the lengths match, then run the byte loop below over copies of the two
pointers (`hex.read_byte_and_inc` + `hex.cmp 2`). One small loop covers every comparison;
emitting a bespoke `equals_<that_word>` macro with N unrolled per-char compares is needless
code. Same loop, two buffers — `match_at` *is* the equality primitive.

```fj
// Jump yes if pat[:plen] matches text at startptr; else no. startptr unchanged.
def match_at startptr, pat, plen, yes, no @ mloop, eqc < mptr, pptr2, mcnt, mb, pb {
    hex.mov hw, mptr, startptr
    hex.set hw, pptr2, pat
    hex.mov hw, mcnt, plen
  mloop:
    hex.if0 hw, mcnt, yes
    hex.read_byte_and_inc mb, mptr
    hex.read_byte_and_inc pb, pptr2
    hex.cmp 2, mb, pb, no, eqc, no
  eqc:
    hex.dec hw, mcnt
    ;mloop
}
```

## Tokenizing (longest word, count words, reverse words, unique words)

Forward scan with an `instate` bit (0 = between words, 1 = inside a word). Track the current
token as a `(start-pointer, length)` pair: on the byte that starts a word, copy the
*pre-read* position into `curstart` (`hex.mov hw, posptr, scanptr` BEFORE
`hex.read_byte_and_inc`); each subsequent word byte does `hex.inc hw, curlen`. Finalize the
token on the separator byte and once more after the loop (a line can end mid-word).

Because the token's `curstart` points INTO `buf` (which persists), you never copy word bytes:
`print_ptr_text curstart, curlen` prints it, and comparing two tokens just reads from their
two start-pointers. To remember many tokens (reverse / unique), store the pairs in parallel
arrays `wstarts/wlens: hex.vec hw * MAXW` with `hex.write_hex hw, wptr, val` +
`hex.ptr_add wptr, hw` (one cell = `hw` hexes), and walk them back with `hex.ptr_sub … hw`.

## Counting by byte value (frequency table)

A 256-entry counter array is `counts: hex.vec 256` (256 byte-slots, zero-initialised). To
bump `counts[byte]` for a runtime byte: `hex.set` a pointer to `counts`, copy the byte value
into a `hex.vec 2` counter, loop `hex.ptr_inc` that many times, then read-inc-write the slot
(`hex.read_byte` / `hex.inc 2` / `hex.write_byte`). Iterate `0..255` afterward with a
parallel `hex.ptr_inc` to emit nonzero counts in ascending order.
