# Docs map — fast routing to the authoritative FlipJump reference

For each section: the fjdocs URL (prefer this), the corresponding upstream STL path (fallback only), and a one-line "what question does this answer".

## Contents

- [Getting started](#getting-started)
- [Cookbook (recipes)](#cookbook)
- [Language reference](#language-reference)
- [Standard library — index](#standard-library)
- [Standard library — `bit/` namespace](#bit-namespace)
- [Standard library — `hex/` namespace](#hex-namespace)
- [Standard library — `hex/pointers/` subtree](#hexpointers-subtree)
- [Standard library — root-level files](#root-level-stl-files)
- [Reference (concept pages)](#reference)
- [Examples](#examples)
- [Tools / external](#tools)

URL base: `https://fjdocs.tomhe.app`. GitHub base: `https://github.com/tomhea/flip-jump/tree/main`.

> **Not on fjdocs yet** (use the GitHub source directly for these): `hex.scmp` (in `hex/cond_jumps.fj`), the indexed-pointer family `hex.ptr_index` / `read_nth_hex/byte` / `write_nth_hex/byte` (in `hex/pointers/`), and everything in `hex/strings.fj` (`input_ptr_line`, `print_ptr_text`, `print_ptr_line`). These also postdate the 1.3.0 PyPI release — see the version note in SKILL.md "Required setup".

## Getting started

| fjdocs | GitHub | Answers |
|---|---|---|
| `/getting-started/index.html` | — | Where to begin if you've never compiled an `.fj` file. |
| `/getting-started/install.html` | — | How to install the `flipjump` Python package and run a sanity check. |
| `/getting-started/hello-world.html` | `programs/print_tests/hello_world.fj` | First end-to-end program: write, compile, run, see output. |
| `/getting-started/anatomy.html` | — | Why every program needs `stl.startup`, why `stl.loop` ends it, where data must live. |

## Cookbook

| fjdocs | GitHub | Answers |
|---|---|---|
| `/cookbook/index.html` | — | Index of all recipes. |
| `/cookbook/hello-world.html` | `programs/print_tests/hello_world.fj` | Minimal greeting using `stl.output`. |
| `/cookbook/echo-byte.html` | `programs/print_tests/cat.fj` | Read one byte from stdin, write to stdout. |
| `/cookbook/print-decimal.html` | `programs/print_tests/print_dec.fj` | Print a binary number as decimal text. |
| `/cookbook/conditional-branch.html` | — | `bit.if` / `bit.if0` / `bit.if1` patterns. |
| `/cookbook/loop-n-times.html` | — | Counted loop with a decrementing counter. |
| `/cookbook/addition.html` | — | `bit.add` / `hex.add` and when to pick which. |
| `/cookbook/function-call.html` | — | `stl.fcall` / `stl.fret` vs `stl.call` / `stl.return`. |
| `/cookbook/swap-two-variables.html` | — | `bit.swap` / `hex.swap` idioms. |
| `/cookbook/fixed-string.html` | — | Storing string literals with `bit.str`. |
| `/cookbook/read-and-double.html` | — | Input → arithmetic → output round-trip. |

## Language reference

| fjdocs | GitHub | Answers |
|---|---|---|
| `/language/index.html` | — | TOC of language pages. |
| `/language/instruction.html` | — | `a;b` semantics — flip bit a, jump to b. |
| `/language/lexical.html` | — | Identifiers, numbers (`0x`, `0b`, decimal), strings, `//` comments, `\` line continuation. |
| `/language/expressions.html` | — | Operator precedence table for `! = < > ? @ ^ \| % & * + - / : #`. |
| `/language/macros.html` | — | `def NAME ARGS @ LOCALS < REQUIRED > EXPORTED { ... }` syntax + arity overloading + `rep(n, var)`. |
| `/language/namespaces.html` | — | `ns X { ... }`, dotted access, `.` / `..` resolution rules. |
| `/language/directives.html` | — | `pad N`, `reserve N`, `segment ADDR`, `wflip dst, val [, jmp]`. |
| `/language/types.html` | — | What `w`, `dw`, `dbit`, `bit` mean and how they relate. |
| `/language/io.html` | — | `stl.IO` opcode mechanics; how a bit goes from program to stdout. |
| `/language/complexity.html` | — | Glossary for `@`, `w`, `dw`, `dbit`, `n`, and the `k@+c` / `n(...)` notation. |

## Standard library

| fjdocs | GitHub | Answers |
|---|---|---|
| `/stl/index.html` | `flipjump/stl/` | Design philosophy + toctree of every file. |
| `/stl/all_macros.html` | `flipjump/stl/conf.json` | Alphabetical index of every macro with its complexity + 1-line summary. |

Per-file pages (file = `.fj` source file). Notation: `/stl/<file>.html` = file page listing all its macros; `/stl/<file>/<macro>--<arity>.html` = the specific macro page.

### `bit/` namespace

| fjdocs file | GitHub | Answers |
|---|---|---|
| `/stl/bit/memory.html` | `flipjump/stl/bit/memory.fj` | `bit.bit`, `vec`, `zero`, `one`, `mov`, `swap`, `unsafe_mov`. |
| `/stl/bit/logics.html` | `flipjump/stl/bit/logics.fj` | `xor`, `or`, `and`, `not`, `exact_*`, `double_exact_xor`, `address_and_variable_xor`. |
| `/stl/bit/math.html` | `flipjump/stl/bit/math.fj` | `inc`, `dec`, `add`, `sub`, `neg`, `inc1`, `add1`. |
| `/stl/bit/mul.html` | `flipjump/stl/bit/mul.fj` | `mul`, `mul_loop`, `mul10`, `mul_add_if`. |
| `/stl/bit/div.html` | `flipjump/stl/bit/div.fj` | `div`, `idiv`, `div_loop`, `idiv_loop`, `div_step`, `div10`. |
| `/stl/bit/shifts.html` | `flipjump/stl/bit/shifts.fj` | `shl`, `shr`, `shra`, `rol`, `ror`. |
| `/stl/bit/cond_jumps.html` | `flipjump/stl/bit/cond_jumps.fj` | `if`, `if0`, `if1`, `cmp` (3-way), `cmp_next_eq`. |
| `/stl/bit/input.html` | `flipjump/stl/bit/input.fj` | `input_bit`, `input` (1 byte / n bytes). |
| `/stl/bit/output.html` | `flipjump/stl/bit/output.fj` | `output`, `print`, `print_str`, `print_as_digit`, `print_dec_*`, `print_hex_*`. |
| `/stl/bit/casting.html` | `flipjump/stl/bit/casting.fj` | `str`, `bin2ascii`, `dec2ascii`, `hex2ascii`, `ascii2bin/dec/hex`. |
| `/stl/bit/pointers.html` | `flipjump/stl/bit/pointers.fj` | `ptr_init`, `ptr_jump`, `ptr_flip`, `ptr_wflip`, `ptr_flip_dbit`, `xor_*_ptr`. |

### `hex/` namespace

| fjdocs file | GitHub | Answers |
|---|---|---|
| `/stl/hex/memory.html` | `flipjump/stl/hex/memory.fj` | `hex`, `vec`, `zero`, `mov`, `xor_by`, `set`, `swap`. |
| `/stl/hex/logics.html` | `flipjump/stl/hex/logics.fj` | `xor`, `or`, `and`, `not`, `double_xor`, `quadrupled_exact_xor`. |
| `/stl/hex/math.html` | `flipjump/stl/hex/math.fj` | `add`, `sub`, `add_constant`, `add_shifted`, `clear_carry`, `set_carry`. |
| `/stl/hex/math_basic.html` | `flipjump/stl/hex/math_basic.fj` | `inc`, `dec`, `neg`, `inc1`, `dec1`, `step`, `add_count_bits`, `sign_extend`. |
| `/stl/hex/mul.html` | `flipjump/stl/hex/mul.fj` | `mul`, `add_mul`, `clear_carry`. |
| `/stl/hex/div.html` | `flipjump/stl/hex/div.fj` | `div` (unsigned), `idiv` (signed, configurable remainder via `rem_opt`). |
| `/stl/hex/shifts.html` | `flipjump/stl/hex/shifts.fj` | `shl_hex`, `shr_hex`, `shl_bit_once`, `shr_bit_once`. |
| `/stl/hex/cond_jumps.html` | `flipjump/stl/hex/cond_jumps.fj` | `if`, `if0`, `if1`, `if_flags`, `sign`, `cmp`, `cmp_eq_next`. |
| `/stl/hex/input.html` | `flipjump/stl/hex/input.fj` | `input_hex`, `input` (1/n hex), `input_as_hex`. |
| `/stl/hex/output.html` | `flipjump/stl/hex/output.fj` | `output`, `print`, `print_as_digit`, `print_uint`, `print_int`. |
| `/stl/hex/tables_init.html` | `flipjump/stl/hex/tables_init.fj` | `hex.init`, `tables.init_shared`, `tables.init_all`, `clean_table_entry__table`, `jump_to_table_entry`. |
| *(not on fjdocs yet)* | `flipjump/stl/hex/strings.fj` | `input_ptr_line`, `print_ptr_text`, `print_ptr_line` — the line-buffer macros. GitHub source is the only reference. |

### `hex/pointers/` subtree

| fjdocs file | GitHub | Answers |
|---|---|---|
| `/stl/hex/pointers/basic_pointers.html` | `flipjump/stl/hex/pointers/basic_pointers.fj` | `ptr_init`, `ptr_jump`, `set_flip_pointer`, `set_jump_pointer`, `set_flip_and_jump_pointers`, `stack_init`. |
| `/stl/hex/pointers/pointer_arithmetics.html` | `flipjump/stl/hex/pointers/pointer_arithmetics.fj` | `ptr_inc`, `ptr_dec`, `ptr_add`, `ptr_sub`. |
| `/stl/hex/pointers/read_pointers.html` | `flipjump/stl/hex/pointers/read_pointers.fj` | `read_byte`, `read_hex`, `read_byte_and_inc`, `read_hex_and_inc`. |
| `/stl/hex/pointers/write_pointers.html` | `flipjump/stl/hex/pointers/write_pointers.fj` | `write_byte`, `write_hex`, `write_byte_and_inc`, `write_hex_and_inc`, `zero_ptr`. |
| `/stl/hex/pointers/stack.html` | `flipjump/stl/hex/pointers/stack.fj` | `push` / `pop` (single & multi), `push_byte`, `pop_byte`, `push_ret_address`, `pop_ret_address`, `sp_inc/dec/add/sub`. |
| `/stl/hex/pointers/xor_from_pointer.html` | `flipjump/stl/hex/pointers/xor_from_pointer.fj` | `xor_byte_from_ptr`, `xor_hex_from_ptr`, `read_byte_from_inners_ptrs`. |
| `/stl/hex/pointers/xor_to_pointer.html` | `flipjump/stl/hex/pointers/xor_to_pointer.fj` | `ptr_flip`, `ptr_wflip`, `ptr_wflip_2nd_word`, `ptr_flip_dbit`, `xor_*_to_ptr`, `xor_*_to_flip_ptr`. |

### Root-level STL files

| fjdocs file | GitHub | Answers |
|---|---|---|
| `/stl/runlib.html` | `flipjump/stl/runlib.fj` | `stl.startup`, `stl.loop`, `stl.skip`, `stl.fj`, `stl.wflip_macro`, `stl.comp_if*`, `stl.output*`, `stl.startup_and_init_all`. |
| `/stl/ptrlib.html` | `flipjump/stl/ptrlib.fj` | `stl.ptr_init`, `stl.stack_init`, `stl.call`, `stl.return`, `stl.get_sp`, `stl.fcall`, `stl.fret`. |
| `/stl/casting.html` | `flipjump/stl/casting.fj` | `stl.bit2hex`, `stl.hex2bit`. |

## Reference

| fjdocs | GitHub | Answers |
|---|---|---|
| `/reference/index.html` | — | TOC of concept pages. |
| `/reference/cheat-sheet.html` | — | One-page "which macro do I reach for" by task. |
| `/reference/glossary.html` | — | `w`, `dw`, `dbit`, `@`, etc. defined. |
| `/reference/how-the-stl-works.html` | — | Explains the bit-variable / hex-variable storage model and how table-driven hex ops dispatch. |

## Examples

| fjdocs | GitHub | Answers |
|---|---|---|
| `/examples/hello-world.html` | `programs/print_tests/hello_world.fj` | Annotated walkthrough of hello-world. |
| `/examples/prime-sieve.html` | `programs/prime_sieve.fj` | Sieve of Eratosthenes in pure FJ. |
| `/examples/quine.html` | `programs/quine16.fj` | 16-bit self-printing program. |
| `/examples/calculator.html` | `programs/calc.fj` | Two-operand decimal calculator. |

## Tools

| fjdocs | GitHub / URL | Answers |
|---|---|---|
| `/tools/ide.html` | https://fj.tomhe.app | In-browser editor + runtime, no install needed. |
| `/tools/c2fj.html` | https://github.com/tomhea/c2fj | C → RISC-V → FlipJump compiler. |
| `/tools/bf2fj.html` | https://github.com/tomhea/bf2fj | Brainfuck → FlipJump compiler. |
| `/tools/flip-jump.html` | https://github.com/tomhea/flip-jump | Upstream language repo + wiki. |
| `/tools/esolangs.html` | https://esolangs.org/wiki/FlipJump | External canonical reference. |
