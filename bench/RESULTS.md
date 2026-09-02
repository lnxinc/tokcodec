# Benchmark results

Generated 2026-09-02 by `bench/run.py`. Counter: tiktoken `o200k_base` (proxy).

## Savings per level

| file | kind | what it is | raw tokens | L1 lossless | L2 light | L3 heavy |
|---|---|---|---:|---:|---:|---:|
| `Arr.php` | php | Laravel `Collections/Arr.php` | 6,008 | 6,008 (−0%) | 3,458 (−42%) | 933 (−84%) |
| `Joiner.java` | java | Guava `Joiner.java` | 4,373 | 4,373 (−0%) | 2,007 (−54%) | 1,180 (−73%) |
| `LinkedList.cs` | csharp | .NET runtime `LinkedList.cs` | 3,599 | 3,599 (−0%) | 3,354 (−7%) | 1,495 (−58%) |
| `Strings.kt` | kotlin | Kotlin stdlib `text/Strings.kt` | 13,964 | 13,963 (−0%) | 7,449 (−47%) | 4,181 (−70%) |
| `api_response.json` | json | pretty-printed REST response, 120 records | 11,138 | 6,983 (−37%) | 6,983 (−37%) | 493 (−96%) |
| `argparse.py` | python | CPython stdlib `argparse.py` | 21,198 | 21,195 (−0%) | 15,688 (−26%) | 3,501 (−83%) |
| `decoder.py` | python | CPython stdlib `json/decoder.py` | 3,159 | 3,159 (−0%) | 2,105 (−33%) | 599 (−81%) |
| `linkhash.h` | c | json-c `linkhash.h` | 3,197 | 3,197 (−0%) | 907 (−72%) | 893 (−72%) |
| `npm_module.js` | js | `glob/dist/esm/walker.js` from npm | 2,851 | 2,851 (−0%) | 2,520 (−12%) | 520 (−82%) |
| `pytest_run.log` | log | pytest run, 412 tests, ANSI colour, timestamps, 1 failure | 15,089 | 15,073 (−0%) | 231 (−98%) | 231 (−98%) |
| `set.rb` | ruby | Ruby stdlib `set.rb` | 7,310 | 7,310 (−0%) | 2,795 (−62%) | 935 (−87%) |
| `strings_builder.go` | go | Go stdlib `strings/builder.go` | 865 | 865 (−0%) | 433 (−50%) | 249 (−71%) |
| `vec_deque_iter.rs` | rust | Rust `alloc` `vec_deque/iter.rs` | 1,577 | 1,577 (−0%) | 1,350 (−14%) | 965 (−39%) |
| **total** | | | **94,328** | **90,153 (−4%)** | **49,280 (−48%)** | **16,175 (−83%)** |

## Bytes are not tokens

Measured on `samples/decoder.py`.

| variant | bytes | tokens | vs original | model can read it? |
|---|---:|---:|---:|---|
| original | 12,873 | 3,159 | +0% | yes |
| gzip + base64 | 4,876 | 3,297 | +4% | no, the model cannot inflate gzip |
| vowels removed | 11,075 | 3,908 | +24% | partly, and it guesses wrong |
| tokcodec L1 | 12,866 | 3,159 | +0% | yes, lossless |
| tokcodec L2 | 7,996 | 2,105 | -33% | yes, comments gone |
| tokcodec L3 | 1,957 | 599 | -81% | yes, bodies gone (outline) |
