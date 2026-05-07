"""
Download and preprocess positions from HuggingFace to disk.
Saves numpy memmap files so training can load at full speed with multiple workers.

Usage:
    python -m evaluator.neural_eval.prepare_data

Output files in the same directory as this script:
    data_board.npy    - uint8 (N, 18, 8, 8)   ~54GB for 50M positions
    data_scalar.npy   - float32 (N, 8)         ~1.6GB
    data_target.npy   - float32 (N,)           ~0.2GB
    data_count.txt    - number of positions saved
"""

import pickle
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from tqdm import tqdm

from evaluator.neural_eval.train import (
    DEPTH_THRESHOLD,
    TOTAL_POSITIONS,
    VAL_CACHE_SIZE,
    _process_item_mp,
    build_val_cache,
    generate_synthetic_positions,
    open_hf_stream,
    row_to_target,
    SYNTHETIC_POSITIONS,
)

HERE = Path(__file__).resolve().parent

BOARD_FILE = HERE / "data_board.npy"
SCALAR_FILE = HERE / "data_scalar.npy"
TARGET_FILE = HERE / "data_target.npy"
COUNT_FILE = HERE / "data_count.txt"

BOARD_SHAPE = (18, 8, 8)
SCALAR_DIM = 8
NUM_PROC = 8
CHUNK_SIZE = NUM_PROC * 16


def already_done() -> int:
    if COUNT_FILE.exists():
        return int(COUNT_FILE.read_text().strip())
    return 0


def prepare():
    total = TOTAL_POSITIONS + SYNTHETIC_POSITIONS

    done = already_done()
    if done >= total:
        print(f"Already have {done:,} positions. Nothing to do.")
        return

    print(f"Allocating memmap files for {total:,} positions...")
    board_mm = np.lib.format.open_memmap(
        BOARD_FILE, mode="w+", dtype=np.uint8, shape=(total, *BOARD_SHAPE)
    )
    scalar_mm = np.lib.format.open_memmap(
        SCALAR_FILE, mode="w+", dtype=np.float32, shape=(total, SCALAR_DIM)
    )
    target_mm = np.lib.format.open_memmap(
        TARGET_FILE, mode="w+", dtype=np.float32, shape=(total,)
    )

    idx = done
    stream = open_hf_stream()
    skipped = 0
    chunk = []

    print(f"Streaming from HuggingFace (skipping {VAL_CACHE_SIZE:,} val positions)...")
    with Pool(processes=NUM_PROC) as pool:
        pbar = tqdm(total=TOTAL_POSITIONS, initial=idx, desc="Positions")

        for item in stream:
            if skipped < VAL_CACHE_SIZE:
                skipped += 1
                continue
            if idx >= TOTAL_POSITIONS:
                break

            chunk.append(item)

            if len(chunk) >= CHUNK_SIZE:
                for result in pool.map(_process_item_mp, chunk):
                    if result is None or idx >= TOTAL_POSITIONS:
                        continue
                    board_np, scalar_np, target = result
                    board_mm[idx] = board_np.astype(np.uint8)
                    scalar_mm[idx] = scalar_np
                    target_mm[idx] = target
                    idx += 1
                    pbar.update(1)
                chunk = []

        if chunk:
            for result in pool.map(_process_item_mp, chunk):
                if result is None or idx >= TOTAL_POSITIONS:
                    continue
                board_np, scalar_np, target = result
                board_mm[idx] = board_np.astype(np.uint8)
                scalar_mm[idx] = scalar_np
                target_mm[idx] = target
                idx += 1
                pbar.update(1)

        pbar.close()

    print(f"Adding {SYNTHETIC_POSITIONS:,} synthetic positions...")
    synthetic = generate_synthetic_positions(SYNTHETIC_POSITIONS)
    for item in tqdm(synthetic, desc="Synthetic"):
        try:
            board_np, scalar_np, target_val = _process_item_mp(item)
            if board_np is None:
                continue
            board_mm[idx] = board_np.astype(np.uint8)
            scalar_mm[idx] = scalar_np
            target_mm[idx] = target_val
            idx += 1
        except Exception:
            continue

    board_mm.flush()
    scalar_mm.flush()
    target_mm.flush()

    COUNT_FILE.write_text(str(idx))
    print(f"Done. {idx:,} positions saved to {HERE}")


if __name__ == "__main__":
    prepare()
