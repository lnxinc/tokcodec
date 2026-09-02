# Benchmark results (exact Claude token counts)

Generated 2026-09-02 by `bench/run.py`. Counter: Anthropic `count_tokens` (exact).

## Savings per level

| file | kind | what it is | raw tokens | L1 lossless | L2 light | L3 heavy |
|---|---|---|---:|---:|---:|---:|
| `Arr.php` | php | Laravel `Collections/Arr.php` | 8,120 | 8,120 (−0%) | 4,846 (−40%) | 1,487 (−82%) |
| `Joiner.java` | java | Guava `Joiner.java` | 7,097 | 7,097 (−0%) | 3,560 (−50%) | 2,197 (−69%) |
| `LinkedList.cs` | csharp | .NET runtime `LinkedList.cs` | 6,123 | 6,123 (−0%) | 5,748 (−6%) | 2,669 (−56%) |
| `Strings.kt` | kotlin | Kotlin stdlib `text/Strings.kt` | 23,307 | 23,307 (−0%) | 12,835 (−45%) | 7,772 (−67%) |
| `api_response.json` | json | pretty-printed REST response, 120 records | 14,069 | 9,792 (−30%) | 9,792 (−30%) | 694 (−95%) |
| `argparse.py` | python | CPython stdlib `argparse.py` | 33,232 | 33,232 (−0%) | 25,490 (−23%) | 5,783 (−83%) |
| `decoder.py` | python | CPython stdlib `json/decoder.py` | 4,758 | 4,758 (−0%) | 3,244 (−32%) | 1,038 (−78%) |
| `linkhash.h` | c | json-c `linkhash.h` | 5,425 | 5,425 (−0%) | 1,710 (−68%) | 1,688 (−69%) |
| `npm_module.js` | js | `glob/dist/esm/walker.js` from npm | 4,683 | 4,683 (−0%) | 4,168 (−11%) | 937 (−80%) |
| `pytest_run.log` | log | pytest run, 412 tests, ANSI colour, timestamps, 1 failure | 21,000 | 20,988 (−0%) | 342 (−98%) | 342 (−98%) |
| `set.rb` | ruby | Ruby stdlib `set.rb` | 10,152 | 10,152 (−0%) | 4,068 (−60%) | 1,495 (−85%) |
| `strings_builder.go` | go | Go stdlib `strings/builder.go` | 1,415 | 1,415 (−0%) | 751 (−47%) | 393 (−72%) |
| `vec_deque_iter.rs` | rust | Rust `alloc` `vec_deque/iter.rs` | 2,536 | 2,536 (−0%) | 2,192 (−14%) | 1,646 (−35%) |
| **total** | | | **141,917** | **137,628 (−3%)** | **78,746 (−45%)** | **28,141 (−80%)** |

## Bytes are not tokens

Measured on `samples/decoder.py`.

| variant | bytes | tokens | vs original | model can read it? |
|---|---:|---:|---:|---|
| original | 12,873 | 4,758 | +0% | yes |
| gzip + base64 | 4,876 | 4,640 | -2% | no, the model cannot inflate gzip |
| vowels removed | 11,075 | 5,589 | +17% | partly, and it guesses wrong |
| tokcodec L1 | 12,866 | 4,758 | +0% | yes, lossless |
| tokcodec L2 | 7,996 | 3,244 | -32% | yes, comments gone |
| tokcodec L3 | 1,957 | 1,038 | -78% | yes, bodies gone (outline) |
