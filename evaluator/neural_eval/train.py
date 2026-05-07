import os
import random
import pickle
import sys
from multiprocessing import Pool
from pathlib import Path
from typing import Dict, List, Optional

import chess
import numpy as np
import torch
import torch.nn as nn
from datasets import load_dataset
from huggingface_hub import HfApi
from torch.utils.data import DataLoader, Dataset, IterableDataset
from tqdm import tqdm

from evaluator.neural_eval.struct import NECAIEvaluator, board_to_tensor_and_scalars

HF_REPO_ID = "h4ng/necai"
HF_MODEL_PATH = "models/necai_eval.pt"


HERE = Path(__file__).resolve().parent
VAL_CACHE_FILE = HERE / "val_cache.pkl"
MODEL_FILE = HERE / "necai_eval.pt"

TOTAL_POSITIONS = 50_000_000
VAL_CACHE_SIZE = 100_000
SYNTHETIC_POSITIONS = 30_000

BATCH_SIZE = 2048
NUM_EPOCHS = 30
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4
DEPTH_THRESHOLD = 18
SEED = 42
EARLY_STOP_PATIENCE = 5

CP_CLIP = 2000
CP_SCALE = 600.0

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


def set_seed(seed: int = SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def cp_to_target(cp: int) -> float:
    cp = max(-CP_CLIP, min(CP_CLIP, cp))
    return float(np.tanh(cp / CP_SCALE))


def row_to_target(row: Dict) -> float:
    if row["mate"] is not None:
        return 1.0 if row["mate"] > 0 else -1.0
    cp = row["cp"] or 0
    return cp_to_target(cp)


def process_row(row: Dict):
    board_tensor, scalar_tensor = board_to_tensor_and_scalars(row["fen"])
    target = torch.tensor([row_to_target(row)], dtype=torch.float32)
    return board_tensor, scalar_tensor, target


def generate_synthetic_positions(n: int = SYNTHETIC_POSITIONS) -> List[Dict]:
    positions = []
    templates = [
        (chess.QUEEN, 1),
        (chess.ROOK, 1),
        (chess.BISHOP, 1),
        (chess.KNIGHT, 1),
        (chess.PAWN, 1),
        (chess.ROOK, 2),
        (chess.PAWN, 2),
        (chess.BISHOP, 2),
    ]

    for _ in range(n):
        board = chess.Board()
        for _ in range(random.randint(0, 12)):
            if board.is_game_over():
                break
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(random.choice(moves))

        if board.is_game_over():
            continue

        piece_type, count = random.choice(templates)
        victim_color = random.choice([chess.WHITE, chess.BLACK])
        candidates = list(board.pieces(piece_type, victim_color))
        random.shuffle(candidates)

        removed = 0
        removed_value = 0
        for sq in candidates:
            if removed >= count:
                break
            piece = board.piece_at(sq)
            if piece is None or piece.piece_type == chess.KING:
                continue
            board.remove_piece_at(sq)
            removed += 1
            removed_value += PIECE_VALUES[piece.piece_type]

        if removed == 0 or not board.is_valid():
            continue

        cp = removed_value if victim_color == chess.BLACK else -removed_value
        positions.append({"fen": board.fen(), "cp": cp, "mate": None, "depth": 99})

    return positions


def open_hf_stream():
    dataset = load_dataset(
        "Lichess/chess-position-evaluations",
        split="train",
        streaming=True,
    )
    return dataset.filter(
        lambda x: x["depth"] is not None and x["depth"] >= DEPTH_THRESHOLD
    )


def build_val_cache() -> List[Dict]:
    if VAL_CACHE_FILE.exists():
        print("Loading validation cache...")
        with open(VAL_CACHE_FILE, "rb") as f:
            return pickle.load(f)

    print(f"Building validation cache ({VAL_CACHE_SIZE:,} positions)...")
    stream = open_hf_stream()
    data = []
    for item in tqdm(stream, total=VAL_CACHE_SIZE, desc="Val cache"):
        data.append(item)
        if len(data) >= VAL_CACHE_SIZE:
            break

    with open(VAL_CACHE_FILE, "wb") as f:
        pickle.dump(data, f)

    print(f"Validation cache saved: {VAL_CACHE_FILE}")
    return data


class ValDataset(Dataset):
    def __init__(self, data: List[Dict]):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx: int):
        return process_row(self.data[idx])


def _process_item_mp(item: Dict):
    try:
        board_tensor, scalar_tensor = board_to_tensor_and_scalars(item["fen"])
        target = row_to_target(item)
        return board_tensor.numpy(), scalar_tensor.numpy(), float(target)
    except Exception:
        return None


class StreamingTrainDataset(IterableDataset):
    def __init__(self, total: int, skip: int, synthetic: List[Dict], num_proc: int = 8):
        self.total = total
        self.skip = skip
        self.synthetic = synthetic
        self.num_proc = num_proc
        self.chunk_size = num_proc * 8

    def __iter__(self):
        stream = open_hf_stream()
        count = 0
        skipped = 0
        chunk = []

        with Pool(processes=self.num_proc) as pool:
            for item in stream:
                if skipped < self.skip:
                    skipped += 1
                    continue
                if count >= self.total:
                    break

                chunk.append(item)

                if len(chunk) >= self.chunk_size:
                    for result in pool.map(_process_item_mp, chunk):
                        if result is not None and count < self.total:
                            board_np, scalar_np, target = result
                            yield (
                                torch.from_numpy(board_np),
                                torch.from_numpy(scalar_np),
                                torch.tensor([target], dtype=torch.float32),
                            )
                            count += 1
                    chunk = []

            if chunk:
                for result in pool.map(_process_item_mp, chunk):
                    if result is not None and count < self.total:
                        board_np, scalar_np, target = result
                        yield (
                            torch.from_numpy(board_np),
                            torch.from_numpy(scalar_np),
                            torch.tensor([target], dtype=torch.float32),
                        )
                        count += 1

        for item in self.synthetic:
            try:
                yield process_row(item)
            except Exception:
                continue


BOARD_FILE = HERE / "data_board.npy"
SCALAR_FILE = HERE / "data_scalar.npy"
TARGET_FILE = HERE / "data_target.npy"
COUNT_FILE = HERE / "data_count.txt"


class DiskDataset(Dataset):
    def __init__(self):
        count = int(COUNT_FILE.read_text().strip())
        self.board = np.lib.format.open_memmap(BOARD_FILE, mode="r", dtype=np.uint8)
        self.scalar = np.lib.format.open_memmap(SCALAR_FILE, mode="r", dtype=np.float32)
        self.target = np.lib.format.open_memmap(TARGET_FILE, mode="r", dtype=np.float32)
        self.count = min(count, len(self.target))

    def __len__(self):
        return self.count

    def __getitem__(self, idx):
        board = torch.from_numpy(self.board[idx].astype(np.float32).copy())
        scalar = torch.from_numpy(self.scalar[idx].copy())
        target = torch.tensor([self.target[idx]], dtype=torch.float32)
        return board, scalar, target


@torch.no_grad()
def evaluate(model, loader, loss_fn, device):
    model.eval()
    total_loss = 0.0
    total_mae = 0.0
    total_count = 0

    for board_x, scalar_x, y in loader:
        board_x = board_x.to(device)
        scalar_x = scalar_x.to(device)
        y = y.to(device)

        pred = model(board_x, scalar_x)
        loss = loss_fn(pred, y)

        total_loss += loss.item() * len(y)
        total_mae += torch.abs(pred - y).sum().item()
        total_count += len(y)

    return total_loss / total_count, total_mae / total_count


def train(from_disk: bool = False):
    set_seed(SEED)

    device = get_device()
    print(f"Training on: {device}")
    use_cuda = device.type == "cuda"

    val_data = build_val_cache()
    val_dataset = ValDataset(val_data)

    if from_disk:
        print("Loading training data from disk...")
        train_dataset = DiskDataset()
        print(f"Disk dataset: {len(train_dataset):,} positions")
        num_workers = 8
    else:
        print("Generating synthetic positions...")
        synthetic = generate_synthetic_positions(SYNTHETIC_POSITIONS)
        print(f"Synthetic positions: {len(synthetic):,}")
        train_dataset = StreamingTrainDataset(
            total=TOTAL_POSITIONS,
            skip=VAL_CACHE_SIZE,
            synthetic=synthetic,
        )
        num_workers = 0

    num_gpus = torch.cuda.device_count() if use_cuda else 0
    effective_batch = BATCH_SIZE * max(1, num_gpus)

    train_loader = DataLoader(
        train_dataset,
        batch_size=effective_batch,
        num_workers=num_workers,
        pin_memory=use_cuda,
        shuffle=from_disk,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=use_cuda,
    )

    model = NECAIEvaluator().to(device)
    if num_gpus > 1:
        print(f"Using {num_gpus} GPUs with DataParallel")
        model = nn.DataParallel(model)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE * max(1, num_gpus) if use_cuda else LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )

    start_epoch = 0
    best_val_loss = float("inf")
    epochs_without_improvement = 0

    if MODEL_FILE.exists():
        print("Loading existing checkpoint...")
        checkpoint = torch.load(MODEL_FILE, map_location=device, weights_only=True)

        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
            if "optimizer_state_dict" in checkpoint:
                optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            if "epoch" in checkpoint:
                start_epoch = checkpoint["epoch"] + 1
            if "best_val_loss" in checkpoint:
                best_val_loss = checkpoint["best_val_loss"]
        else:
            model.load_state_dict(checkpoint)

        print(f"Resuming from epoch {start_epoch}")

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=2,
    )
    loss_fn = nn.SmoothL1Loss()

    for epoch in range(start_epoch, NUM_EPOCHS):
        model.train()
        running_loss = 0.0
        steps = 0

        progress = tqdm(train_loader, desc=f"Epoch {epoch + 1}/{NUM_EPOCHS}")

        for board_x, scalar_x, y in progress:
            board_x = board_x.to(device)
            scalar_x = scalar_x.to(device)
            y = y.to(device)

            pred = model(board_x, scalar_x)
            loss = loss_fn(pred, y)

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            running_loss += loss.item()
            steps += 1
            progress.set_postfix(loss=f"{loss.item():.4f}")

        train_loss = running_loss / max(steps, 1)
        val_loss, val_mae = evaluate(model, val_loader, loss_fn, device)
        scheduler.step(val_loss)

        current_lr = optimizer.param_groups[0]["lr"]
        print(
            f"Epoch {epoch + 1} complete | "
            f"Train loss: {train_loss:.4f} | "
            f"Val loss: {val_loss:.4f} | "
            f"Val MAE: {val_mae:.4f} | "
            f"LR: {current_lr:.6f}"
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_without_improvement = 0
            state = model.module.state_dict() if isinstance(model, nn.DataParallel) else model.state_dict()
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": state,
                    "optimizer_state_dict": optimizer.state_dict(),
                    "best_val_loss": best_val_loss,
                    "cp_clip": CP_CLIP,
                    "cp_scale": CP_SCALE,
                },
                MODEL_FILE,
            )
            print(f"Best model saved to {MODEL_FILE}")
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= EARLY_STOP_PATIENCE:
                print(f"Early stopping: no improvement for {EARLY_STOP_PATIENCE} epochs.")
                break

    print("Training complete.")
    upload_model()


def upload_model():
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("HF_TOKEN not set — skipping upload.")
        return

    if not MODEL_FILE.exists():
        print("No model file found — skipping upload.")
        return

    print(f"Uploading model to {HF_REPO_ID} ...")
    api = HfApi()
    api.upload_file(
        path_or_fileobj=str(MODEL_FILE),
        path_in_repo=HF_MODEL_PATH,
        repo_id=HF_REPO_ID,
        repo_type="dataset",
        token=token,
    )
    print(f"Model uploaded to {HF_REPO_ID}/{HF_MODEL_PATH}")


if __name__ == "__main__":
    from_disk = "--from-disk" in sys.argv
    train(from_disk=from_disk)
