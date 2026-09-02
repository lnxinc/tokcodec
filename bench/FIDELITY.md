# Fidelity results

Generated 2026-09-02 by `bench/fidelity/run.py`. Model: `claude-sonnet-5`. 104 questions, 13 samples, levels [0, 1, 2, 3].

Every question is answered from the file at each level and graded against an expected answer (exact/substring match first, model-graded otherwise). `expected to survive` counts only questions whose answer should still be present at that level; the gap between the two rows is what compression deliberately removes.

## Accuracy by level

| | L0 | L1 | L2 | L3 |
|---|---:|---:|---:|---:|
| all questions | 100% | 100% | 88% | 68% |
| expected to survive | 100% | 100% | 100% | 100% |
| input tokens (all samples) | 94,328 | 90,153 | 49,280 | 16,175 |

## Accuracy by question type

| type | L0 | L1 | L2 | L3 |
|---|---:|---:|---:|---:|
| detail | 100% | 100% | 54% | 4% |
| failure | 100% | 100% | 100% | 100% |
| structural | 100% | 100% | 100% | 100% |
| value | 100% | 100% | 100% | 69% |

## Accuracy by sample

| sample | L0 | L1 | L2 | L3 |
|---|---:|---:|---:|---:|
| `Arr.php` | 100% | 100% | 88% | 62% |
| `Joiner.java` | 100% | 100% | 88% | 50% |
| `LinkedList.cs` | 100% | 100% | 88% | 62% |
| `Strings.kt` | 100% | 100% | 88% | 75% |
| `api_response.json` | 100% | 100% | 100% | 75% |
| `argparse.py` | 100% | 100% | 88% | 75% |
| `decoder.py` | 100% | 100% | 88% | 75% |
| `linkhash.h` | 100% | 100% | 88% | 75% |
| `npm_module.js` | 100% | 100% | 88% | 62% |
| `pytest_run.log` | 100% | 100% | 88% | 88% |
| `set.rb` | 100% | 100% | 88% | 62% |
| `strings_builder.go` | 100% | 100% | 88% | 50% |
| `vec_deque_iter.rs` | 100% | 100% | 88% | 75% |

## Every wrong answer (45)

Unedited. `exp L` is the highest level the question was expected to survive.

| id | level | exp L | question | expected | answer |
|---|---|---|---|---|---|
| arr-05 | L2 | 1 | What `@return` type does the docblock of `first` declare? | `TValue\|TFirstDefault` | NOT IN FILE |
| arr-05 | L3 | 1 | What `@return` type does the docblock of `first` declare? | `TValue\|TFirstDefault` | NOT IN FILE |
| arr-06 | L3 | 2 | Which PHP encoding constant does `query` pass as the last argument to `http_build_query`? | `PHP_QUERY_RFC3986` | NOT IN FILE |
| arr-07 | L3 | 2 | What is the exact `InvalidArgumentException` message thrown by `random` when more items are requested than available? | `You requested {$requested} items, but there are only {$count} items available.` | NOT IN FILE |
| joiner-05 | L2 | 1 | Which bug id does the block comment cite for the Kotlin bug that motivates using `<? extends @Nullable Object>` instead of `<?>`? | `b/189937072` | NOT IN FILE |
| joiner-05 | L3 | 1 | Which bug id does the block comment cite for the Kotlin bug that motivates using `<? extends @Nullable Object>` instead of `<?>`? | `b/189937072` | NOT IN FILE |
| joiner-06 | L3 | 2 | In the private static helper `iterable(first, second, rest)`, what does the anonymous list's `size()` return? | `rest.length + 2` | NOT IN FILE |
| joiner-07 | L3 | 2 | What is the exact `UnsupportedOperationException` message thrown when `withKeyValueSeparator` is called on a joiner returned by `skipNulls()`? | `can't use .skipNulls() with maps` | NOT IN FILE |
| joiner-08 | L3 | 2 | What is the exact exception message thrown when `skipNulls()` is called on a joiner already configured with `useForNull`? | `already specified useForNull` | NOT IN FILE |
| linkedlist-05 | L2 | 1 | What does the trailing comment on the `VersionName`, `CountName` and `ValuesName` constants warn? | `Do not rename (binary serialization)` | NOT IN FILE |
| linkedlist-05 | L3 | 1 | What does the trailing comment on the `VersionName`, `CountName` and `ValuesName` constants warn? | `Do not rename (binary serialization)` | NOT IN FILE |
| linkedlist-06 | L3 | 2 | What is the `Debug.Assert` message in `InternalRemoveNode` that checks `node.list == this`? | `Deleting the node from another list!` | NOT IN FILE |
| linkedlist-08 | L3 | 2 | Which `SR` resource string is used for the `InvalidOperationException` thrown by `ValidateNode` when the node belongs to a different list? | `SR.ExternalLinkedListNode` | NOT IN FILE |
| strings-05 | L2 | 1 | In the `DelimitedRangesSequence` iterator, what do the three `nextState` values -1, 0 and 1 mean according to the inline comment? | `-1 for unknown, 0 for done, 1 for continue` | There is no inline comment explaining the `nextState` values -1, 0, and 1 in the file — NOT IN FILE. |
| strings-05 | L3 | 1 | In the `DelimitedRangesSequence` iterator, what do the three `nextState` values -1, 0 and 1 mean according to the inline comment? | `-1 for unknown, 0 for done, 1 for continue` | NOT IN FILE |
| strings-06 | L3 | 2 | In the private `split(delimiter: String, ignoreCase, limit)` function, what initial capacity expression is passed to `ArrayList<String>`? | `if (isLimited) limit.coerceAtMost(10) else 10` | NOT IN FILE |
| api_response-07 | L3 | 2 | What is the `plan` of the user with id `usr_00010`? | `free` | NOT IN FILE |
| api_response-08 | L3 | 2 | What are the `tags` of the last user in `data` (id `usr_00119`)? | `["a", "b", "c"]` | NOT IN FILE |
| argparse-05 | L2 | 1 | According to the `ArgumentParser` class docstring, what is the default value of `prog`? | `os.path.basename(sys.argv[0])` | NOT IN FILE |
| argparse-05 | L3 | 1 | According to the `ArgumentParser` class docstring, what is the default value of `prog`? | `os.path.basename(sys.argv[0])` | NOT IN FILE |
| argparse-06 | L3 | 2 | In `HelpFormatter.__init__`, how is `width` computed when it is passed as None? | `shutil.get_terminal_size().columns - 2` | NOT IN FILE |
| decoder-05 | L2 | 1 | According to the translation table in the `JSONDecoder` class docstring, what Python value does JSON `null` decode to? | `None` | NOT IN FILE |
| decoder-05 | L3 | 1 | According to the translation table in the `JSONDecoder` class docstring, what Python value does JSON `null` decode to? | `None` | NOT IN FILE |
| decoder-06 | L3 | 2 | In `JSONDecoder.decode`, what error message is raised when characters remain after the decoded document? | `Extra data` | NOT IN FILE |
| linkhash-05 | L2 | 1 | How does the doc comment above `LH_PRIME` describe it? | `golden prime used in hash functions` | NOT IN FILE |
| linkhash-05 | L3 | 1 | How does the doc comment above `LH_PRIME` describe it? | `golden prime used in hash functions` | NOT IN FILE |
| linkhash-06 | L3 | 2 | What expression does the inline function `lh_get_hash` return? | `t->hash_fn(k)` | NOT IN FILE |
| npm_module-05 | L2 | 1 | What does the line comment directly above the `pause()` method call the pause/resume pair? | `backpressure mechanism` | NOT IN FILE |
| npm_module-05 | L3 | 1 | What does the line comment directly above the `pause()` method call the pause/resume pair? | `backpressure mechanism` | NOT IN FILE |
| npm_module-06 | L3 | 2 | In the `GlobUtil` constructor, what value is the private `#sep` field given when `opts.platform === 'win32'` and `opts.posix` is falsy? | `'\\'` | NOT IN FILE |
| npm_module-07 | L3 | 2 | What is the exact error message thrown by the constructor when child matches cannot be ignored because the ignore object lacks `add()`? | `cannot ignore child matches, ignore lacks add() method.` | NOT IN FILE |
| pytest_run-08 | L2 | 1 | What is the full timestamp on the line that reports the FAILED test? | `2026-09-02T10:17:01.123` | NOT IN FILE |
| pytest_run-08 | L3 | 1 | What is the full timestamp on the line that reports the FAILED test? | `2026-09-02T10:17:01.123` | NOT IN FILE |
| set-05 | L2 | 1 | According to the header comment, who besides Akinori MUSHA is credited with the documentation? | `Gavin Sinclair` | NOT IN FILE |
| set-05 | L3 | 1 | According to the header comment, who besides Akinori MUSHA is credited with the documentation? | `Gavin Sinclair` | NOT IN FILE |
| set-06 | L3 | 2 | In `initialize`, what default value is the internal `@hash` created with? | `Hash.new(false)` | NOT IN FILE |
| set-07 | L3 | 2 | What `ArgumentError` message does `superset?` raise when its argument is not a Set? | `value must be a set` | NOT IN FILE |
| strings_builder-05 | L2 | 1 | Which Go issue number does the comment inside `copyCheck` cite as the reason for the escape-analysis workaround? | `23382` | NOT IN FILE |
| strings_builder-05 | L3 | 1 | Which Go issue number does the comment inside `copyCheck` cite as the reason for the escape-analysis workaround? | `23382` | NOT IN FILE |
| strings_builder-06 | L3 | 2 | In `grow`, what expression is passed to `bytealg.MakeNoZero` to size the new buffer? | `2*cap(b.buf) + n` | NOT IN FILE |
| strings_builder-07 | L3 | 2 | What is the exact panic message when `Grow` is called with a negative count? | `strings.Builder.Grow: negative count` | NOT IN FILE |
| strings_builder-08 | L3 | 2 | What is the exact panic message raised by `copyCheck` when a non-zero Builder was copied by value? | `strings: illegal use of non-zero Builder copied by value` | NOT IN FILE |
| vec_deque_iter-05 | L2 | 1 | Which issue number does the FIXME comment above the `Clone` impl reference? | `#26925` | NOT IN FILE |
| vec_deque_iter-05 | L3 | 1 | Which issue number does the FIXME comment above the `Clone` impl reference? | `#26925` | NOT IN FILE |
| vec_deque_iter-06 | L3 | 2 | In `next()`, what does the `None` branch do before retrying `self.i1.next()`? | `mem::swap(&mut self.i1, &mut self.i2)` | NOT IN FILE |
