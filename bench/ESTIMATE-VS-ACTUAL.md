# Estimate vs actual

Estimate: tiktoken `o200k_base`, what `tokcodec` prints by default. Actual: Anthropic `count_tokens` for Claude Sonnet/Opus 5 (`--exact`). Level 3 on every sample.

| file | estimate raw → L3 | actual raw → L3 | estimated saving | actual saving | estimate error |
|---|---:|---:|---:|---:|---:|
| `Arr.php` | 6,008 → 933 | 8,120 → 1,487 | −84% | −82% | +2.8 pts |
| `Joiner.java` | 4,373 → 1,180 | 7,097 → 2,197 | −73% | −69% | +4.0 pts |
| `LinkedList.cs` | 3,599 → 1,495 | 6,123 → 2,669 | −58% | −56% | +2.1 pts |
| `Strings.kt` | 13,964 → 4,181 | 23,307 → 7,772 | −70% | −67% | +3.4 pts |
| `api_response.json` | 11,138 → 493 | 14,069 → 694 | −96% | −95% | +0.5 pts |
| `argparse.py` | 21,198 → 3,501 | 33,232 → 5,783 | −83% | −83% | +0.9 pts |
| `decoder.py` | 3,159 → 599 | 4,758 → 1,038 | −81% | −78% | +2.9 pts |
| `linkhash.h` | 3,197 → 893 | 5,425 → 1,688 | −72% | −69% | +3.2 pts |
| `npm_module.js` | 2,851 → 520 | 4,683 → 937 | −82% | −80% | +1.8 pts |
| `pytest_run.log` | 15,089 → 231 | 21,000 → 342 | −98% | −98% | +0.1 pts |
| `set.rb` | 7,310 → 935 | 10,152 → 1,495 | −87% | −85% | +1.9 pts |
| `strings_builder.go` | 865 → 249 | 1,415 → 393 | −71% | −72% | -1.0 pts |
| `vec_deque_iter.rs` | 1,577 → 965 | 2,536 → 1,646 | −39% | −35% | +3.7 pts |
| **total** | **94,328 → 16,175** | **141,917 → 28,141** | **−83%** | **−80%** | **+2.7 pts** |

Claude's tokenizer counts **1.50×** the proxy's tokens on these files, so absolute estimates are low, but the *saving* is what you decide on, and that is within a few points either way.

## What that is worth

Actual counts, one pass over all 13 samples (141,917 tokens raw, 28,141 at level 3), input price only, uncached:

| model | input price | read all 13 files raw | read them at level 3 | saved per pass | saved per 1,000 passes |
|---|---:|---:|---:|---:|---:|
| claude-opus-5 | $5.00/M | $0.710 | $0.141 | $0.569 | $569 |
| claude-sonnet-5 | $2.00/M | $0.284 | $0.056 | $0.228 | $228 |
| claude-haiku-4-5 | $1.00/M | $0.142 | $0.028 | $0.114 | $114 |

Cached reads are cheaper per token, but the context-window headroom saved is the same either way.
