# tomhea-skills

A [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) for Tom's skills.

## Install

```
/plugin marketplace add tomhea/skills
/plugin install flipjump@tomhea-skills
```

## Plugins

### flipjump

Write correct, efficient, well-tested [FlipJump](https://github.com/tomhea/flip-jump) programs — FlipJump being the single-instruction esolang (`a;b`: flip the bit at `a`, jump to `b`) whose entire computational world is built from macros, chiefly its standard library.

The plugin ships one skill, **`flipjump-dev`**, which triggers automatically whenever you ask Claude to write, debug, optimize, or run FlipJump code (`.fj` files, STL macros in the `bit`/`hex`/`stl` namespaces, etc.). It deliberately does *not* duplicate the language reference — instead it gives Claude three things:

1. **A precise map of where to look** — routing every kind of question (macro signatures, init requirements, syntax, recipes) to the right page of [fjdocs.tomhe.app](https://fjdocs.tomhe.app), with the [upstream STL source](https://github.com/tomhea/flip-jump/tree/main/flipjump/stl) as fallback.
2. **The non-obvious gotchas** the references don't make obvious — the memory model's `*dw` stride, the two byte encodings, init-macro dependencies, `@`/`<` clause discipline, label-order traps, and more, all learned from real authoring sessions.
3. **A mandatory verification loop** — every generated program is run through the `fj` CLI (the [flipjump](https://pypi.org/project/flipjump/) Python package) and is only "done" when it halts cleanly via `stl.loop` *and* its output matches byte-for-byte, with each behavior path covered by its own test input. "It compiled" is never accepted as correct.

Requires `pip install flipjump` (puts `fj` on `PATH`).

## License

[BSD 2-Clause](LICENSE)
