# Benchmark results

Generated 2026-09-02 by `bench/run.py`. Counter: tiktoken `o200k_base` (proxy).

## Savings per level

| file | kind | what it is | raw tokens | L1 lossless | L2 light | L3 heavy |
|---|---|---|---:|---:|---:|---:|
| `api_response.json` | json | pretty-printed REST response, 120 records | 11,138 | 6,983 (−37%) | 6,983 (−37%) | 493 (−96%) |
| `argparse.py` | python | CPython stdlib `argparse.py` | 21,198 | 21,195 (−0%) | 15,688 (−26%) | 3,501 (−83%) |
| `decoder.py` | python | CPython stdlib `json/decoder.py` | 3,159 | 3,159 (−0%) | 2,105 (−33%) | 599 (−81%) |
| `npm_module.js` | js | `glob/dist/esm/walker.js` from npm | 2,851 | 2,851 (−0%) | 2,520 (−12%) | 520 (−82%) |
| `pytest_run.log` | log | pytest run, 412 tests, ANSI colour, timestamps, 1 failure | 15,089 | 15,073 (−0%) | 231 (−98%) | 231 (−98%) |
| **total** | | | **53,435** | **49,261 (−8%)** | **27,527 (−48%)** | **5,344 (−90%)** |

## Bytes are not tokens

Measured on `samples/decoder.py`.

| variant | bytes | tokens | vs original | model can read it? |
|---|---:|---:|---:|---|
| original | 12,873 | 3,159 | +0% | yes |
| gzip + base64 | 4,876 | 3,296 | +4% | no, the model cannot inflate gzip |
| vowels removed | 11,075 | 3,908 | +24% | partly, and it guesses wrong |
| tokpack L1 | 12,866 | 3,159 | +0% | yes, lossless |
| tokpack L2 | 7,996 | 2,105 | -33% | yes, comments gone |
| tokpack L3 | 1,957 | 599 | -81% | yes, bodies gone (outline) |
