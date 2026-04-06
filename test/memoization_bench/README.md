# Memoization Benchmark

This folder measures three parts of the memoization claim:

- memoization-based lookup tables
- O(1) retrieval
- sub-microsecond average lookup latency

## What It Benchmarks

The benchmark loads:

- `../../necai/memoization/white/train.jsonl`
- `../../necai/memoization/black/train.jsonl`

into a C++:

```cpp
std::unordered_map<std::string, MemoEntry>
```

where the key is the FEN string.

It then runs:

- hit lookups on known FENs
- miss lookups on synthetic unknown keys

and reports average latency in both nanoseconds and microseconds.

## Build

From this folder:

```bash
make
```

## Run

From this folder:

```bash
./memo_bench
```

Useful options:

```bash
./memo_bench --lookups=1000000
./memo_bench --limit=1000
./memo_bench --limit=10000
./memo_bench --limit=50000
./memo_bench --seed=123
```

## How To Interpret

`memoization-based lookup tables`

- Supported if the benchmark is using `std::unordered_map` loaded from your memoization dataset.

`O(1) retrieval`

- This is an average-case property of `std::unordered_map`.
- For practical evidence, run the benchmark at several `--limit` sizes and verify the average lookup time stays roughly flat as the table grows.

`sub-microsecond (<1 µs) average latency`

- Supported if the benchmark prints `sub_microsecond_hit_target_met: yes`
- Or equivalently if `avg_ns < 1000`

## Notes

- The benchmark measures in-memory lookup only.
- It does not include dataset loading time from disk.
- That separation matters if you want to make a clean runtime lookup claim.
