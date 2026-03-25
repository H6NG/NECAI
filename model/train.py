import os
import random
import pickle
from typing import List, Dict, Tuple

import chess
import numpy as np
import torch
import torch.nn as nn
from datasets import load_dataset
from torch.utils.data import Dataset, DataLoader, random_split
from tqdm import tqdm


# =========================================================
# Config
# =========================================================
CACHE_FILE = "positions_cache.pkl"
MODEL_FILE = "necai_eval.pt"

TOTAL_POSITIONS = 500_000
SYNTHETIC_POSITIONS = 30_000

BATCH_SIZE = 256
NUM_EPOCHS = 30
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4
VALID_RATIO = 0.1
DEPTH_THRESHOLD = 18
SEED = 42

CP_CLIP = 2000
CP_SCALE = 600.0


# =========================================================
# Reproducibility
# =========================================================
def set_seed(seed: int = SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


# =========================================================
# Piece values
# =========================================================
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


# =========================================================
# Feature extraction
# =========================================================
def board_to_tensor_and_scalars(fen: str) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Returns:
        board_tensor: [18, 8, 8]
        scalar_tensor: [8]

    Channels:
      0-5   white P N B R Q K
      6-11  black P N B R Q K
      12    side to move
      13    white kingside castling
      14    white queenside castling
      15    black kingside castling
      16    black queenside castling
      17    en passant square
    """
    board = chess.Board(fen)
    tensor = np.zeros((18, 8, 8), dtype=np.float32)

    piece_map = {
        (chess.PAWN, chess.WHITE): 0,
        (chess.KNIGHT, chess.WHITE): 1,
        (chess.BISHOP, chess.WHITE): 2,
        (chess.ROOK, chess.WHITE): 3,
        (chess.QUEEN, chess.WHITE): 4,
        (chess.KING, chess.WHITE): 5,
        (chess.PAWN, chess.BLACK): 6,
        (chess.KNIGHT, chess.BLACK): 7,
        (chess.BISHOP, chess.BLACK): 8,
        (chess.ROOK, chess.BLACK): 9,
        (chess.QUEEN, chess.BLACK): 10,
        (chess.KING, chess.BLACK): 11,
    }

    for square, piece in board.piece_map().items():
        row, col = divmod(square, 8)
        channel = piece_map[(piece.piece_type, piece.color)]
        tensor[channel, row, col] = 1.0

    if board.turn == chess.WHITE:
        tensor[12, :, :] = 1.0

    if board.has_kingside_castling_rights(chess.WHITE):
        tensor[13, :, :] = 1.0
    if board.has_queenside_castling_rights(chess.WHITE):
        tensor[14, :, :] = 1.0
    if board.has_kingside_castling_rights(chess.BLACK):
        tensor[15, :, :] = 1.0
    if board.has_queenside_castling_rights(chess.BLACK):
        tensor[16, :, :] = 1.0

    if board.ep_square is not None:
        row, col = divmod(board.ep_square, 8)
        tensor[17, row, col] = 1.0

    white_material = 0
    black_material = 0

    for _, piece in board.piece_map().items():
        val = PIECE_VALUES[piece.piece_type]
        if piece.color == chess.WHITE:
            white_material += val
        else:
            black_material += val

    material_diff = (white_material - black_material) / 4000.0

    stm_mobility = board.legal_moves.count() / 100.0

    opp_board = board.copy()
    opp_board.turn = not board.turn
    opp_mobility = opp_board.legal_moves.count() / 100.0

    in_check = float(board.is_check())
    fullmove = min(board.fullmove_number, 100) / 100.0
    halfmove = min(board.halfmove_clock, 100) / 100.0
    white_bishop_pair = float(len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2)
    black_bishop_pair = float(len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2)

    scalar_features = np.array([
        material_diff,
        stm_mobility,
        opp_mobility,
        in_check,
        fullmove,
        halfmove,
        white_bishop_pair,
        black_bishop_pair,
    ], dtype=np.float32)

    return torch.tensor(tensor), torch.tensor(scalar_features)


# =========================================================
# Target transform
# =========================================================
def cp_to_target(cp: int) -> float:
    cp = max(-CP_CLIP, min(CP_CLIP, cp))
    return float(np.tanh(cp / CP_SCALE))


def row_to_target(row: Dict) -> float:
    if row["mate"] is not None:
        return 1.0 if row["mate"] > 0 else -1.0

    cp = row["cp"]
    if cp is None:
        cp = 0

    return cp_to_target(cp)


# =========================================================
# Synthetic positions
# =========================================================
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

        num_random_moves = random.randint(0, 12)
        for _ in range(num_random_moves):
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

        if removed == 0:
            continue

        if not board.is_valid():
            continue

        cp = removed_value if victim_color == chess.BLACK else -removed_value

        positions.append({
            "fen": board.fen(),
            "cp": cp,
            "mate": None,
            "depth": 99,
        })

    return positions


# =========================================================
# Data loading
# =========================================================
def load_data(total: int = TOTAL_POSITIONS) -> List[Dict]:
    if os.path.exists(CACHE_FILE):
        print("✅ Loading dataset from local cache...")
        with open(CACHE_FILE, "rb") as f:
            data = pickle.load(f)
    else:
        print("Streaming from Hugging Face...")
        dataset = load_dataset(
            "Lichess/chess-position-evaluations",
            split="train",
            streaming=True,
        )

        dataset = dataset.filter(
            lambda x: x["depth"] is not None and x["depth"] >= DEPTH_THRESHOLD
        )

        data = []
        for item in tqdm(dataset, total=total, desc="Downloading positions"):
            data.append(item)
            if len(data) >= total:
                break

        with open(CACHE_FILE, "wb") as f:
            pickle.dump(data, f)

    print("Generating synthetic positions...")
    synthetic = generate_synthetic_positions(SYNTHETIC_POSITIONS)
    data.extend(synthetic)

    random.shuffle(data)
    print(f"✅ Total positions: {len(data)}")
    return data


# =========================================================
# Dataset
# =========================================================
class ChessEvalDataset(Dataset):
    def __init__(self, data: List[Dict]):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx: int):
        row = self.data[idx]
        board_tensor, scalar_tensor = board_to_tensor_and_scalars(row["fen"])
        target = row_to_target(row)

        return (
            board_tensor,
            scalar_tensor,
            torch.tensor([target], dtype=torch.float32),
        )


# =========================================================
# Model
# =========================================================
class NECAIEvaluator(nn.Module):
    def __init__(self, scalar_dim: int = 8):
        super().__init__()

        self.conv = nn.Sequential(
            nn.Conv2d(18, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),

            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),

            nn.MaxPool2d(2),

            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),

            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),

            nn.MaxPool2d(2),
        )

        self.board_head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256 * 2 * 2, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
        )

        self.scalar_head = nn.Sequential(
            nn.Linear(scalar_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
        )

        self.final = nn.Sequential(
            nn.Linear(512 + 64, 256),
            nn.ReLU(),
            nn.Dropout(0.25),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )

    def forward(self, board_x, scalar_x):
        board_feat = self.board_head(self.conv(board_x))
        scalar_feat = self.scalar_head(scalar_x)
        combined = torch.cat([board_feat, scalar_feat], dim=1)
        return self.final(combined)


# =========================================================
# Evaluation
# =========================================================
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

    avg_loss = total_loss / total_count
    avg_mae = total_mae / total_count
    return avg_loss, avg_mae


# =========================================================
# Train
# =========================================================
def train():
    set_seed(SEED)

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Training on: {device}")

    data = load_data(TOTAL_POSITIONS)
    dataset = ChessEvalDataset(data)

    valid_size = int(len(dataset) * VALID_RATIO)
    train_size = len(dataset) - valid_size

    train_dataset, valid_dataset = random_split(
        dataset,
        [train_size, valid_size],
        generator=torch.Generator().manual_seed(SEED),
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=4,
        pin_memory=True,
        persistent_workers=True,
    )

    valid_loader = DataLoader(
        valid_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=4,
        pin_memory=True,
        persistent_workers=True,
    )

    model = NECAIEvaluator().to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )

    start_epoch = 0
    best_val_loss = float("inf")

    if os.path.exists(MODEL_FILE):
        print("🔁 Loading existing checkpoint...")
        checkpoint = torch.load(MODEL_FILE, map_location=device)

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
        optimizer,
        mode="min",
        factor=0.5,
        patience=2,
    )

    loss_fn = nn.SmoothL1Loss()

    for epoch in range(start_epoch, NUM_EPOCHS):
        model.train()
        running_loss = 0.0

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
            progress.set_postfix(loss=f"{loss.item():.4f}")

        train_loss = running_loss / len(train_loader)
        val_loss, val_mae = evaluate(model, valid_loader, loss_fn, device)
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
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "best_val_loss": best_val_loss,
                    "cp_clip": CP_CLIP,
                    "cp_scale": CP_SCALE,
                },
                MODEL_FILE,
            )
            print(f"✅ Best model saved to {MODEL_FILE}")

    print("Training complete.")


if __name__ == "__main__":
    train()