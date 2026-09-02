# tokcodec

**A codec for LLM context.** Cuts the tokens Claude Code and other AI coding tools spend on logs, JSON and source files by 30–95%, lossless or lossy by level. Same failure line, same signatures, a fraction of the tokens.

```bash
npx tokcodec why path/to/any/file.py     # see the token math for yourself
npx tokcodec install                      # wire it into Claude Code (skill + hooks)
```

This npm package is a launcher. The engine is the Python package of the same name; the launcher runs it via `uvx` or `pipx` if you have them, and otherwise downloads a private copy of [uv](https://docs.astral.sh/uv/) once (about 15 MB) so it works on machines with no Python installed.

Full documentation, benchmarks and source: **https://github.com/lnxinc/tokcodec**

Provided by [LNX Inc.](https://lnxinc.com) free of charge for everyone. MIT.
