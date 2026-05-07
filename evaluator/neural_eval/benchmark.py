"""
Benchmark inference speed: original vs TorchScript+FP16, single vs batched.
"""
import time
import random

import chess

from evaluator.neural_eval.inference import predict_fen as predict_slow
from evaluator.neural_eval.fast_inference import predict_fen as predict_fast, predict_batch


def random_fens(n: int):
    fens = []
    for _ in range(n):
        board = chess.Board()
        for _ in range(random.randint(8, 30)):
            if board.is_game_over():
                break
            board.push(random.choice(list(board.legal_moves)))
        fens.append(board.fen())
    return fens


def bench(name, fn, fens):
    # warmup
    fn(fens[:2])
    start = time.perf_counter()
    for f in fens:
        fn(f)
    elapsed = time.perf_counter() - start
    per_call = elapsed / len(fens) * 1000
    rate = len(fens) / elapsed
    print(f"{name:30s}  {elapsed*1000:7.1f} ms total  |  {per_call:6.2f} ms/call  |  {rate:7.0f} evals/sec")


def bench_batch(name, batch_fn, fens, batch_size):
    # warmup
    batch_fn(fens[:batch_size])
    start = time.perf_counter()
    for i in range(0, len(fens), batch_size):
        batch_fn(fens[i:i + batch_size])
    elapsed = time.perf_counter() - start
    per_call = elapsed / len(fens) * 1000
    rate = len(fens) / elapsed
    print(f"{name:30s}  {elapsed*1000:7.1f} ms total  |  {per_call:6.2f} ms/call  |  {rate:7.0f} evals/sec")


def main():
    print("Generating 500 random positions...")
    random.seed(0)
    fens = random_fens(500)

    print(f"\n--- Single-call benchmarks ---")
    bench("Original (Python eval)",   lambda f: predict_slow(f) if isinstance(f, str) else None, fens)
    bench("TorchScript+FP16 single",  lambda f: predict_fast(f) if isinstance(f, str) else None, fens)

    print(f"\n--- Batched benchmarks (TorchScript+FP16) ---")
    for bs in (8, 32, 128, 256):
        bench_batch(f"Batch size {bs}", predict_batch, fens, bs)


if __name__ == "__main__":
    main()
