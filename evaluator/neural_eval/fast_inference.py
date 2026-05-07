"""
Fast batched inference using the exported TorchScript model.
Supports both single-FEN and batched evaluation.

Usage:
    from evaluator.neural_eval.fast_inference import predict_fen, predict_batch
    score = predict_fen("rnbqkbnr/...")
    scores = predict_batch(["fen1", "fen2", "fen3"])
"""
from pathlib import Path
from typing import List, Optional

import numpy as np
import torch

from evaluator.neural_eval.struct import board_to_tensor_and_scalars

HERE = Path(__file__).resolve().parent
JIT_FILE = HERE / "necai_eval_jit.pt"

_device: Optional[torch.device] = None
_model = None
_dtype = None


def get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def load_model():
    global _model, _device, _dtype
    if _model is not None:
        return _model

    if not JIT_FILE.exists():
        raise FileNotFoundError(
            f"{JIT_FILE} not found. Run `python -m evaluator.neural_eval.export_jit` first."
        )

    _device = get_device()
    _dtype = torch.float32
    _model = torch.jit.load(str(JIT_FILE), map_location=_device)
    _model.eval()

    # Warm up the model (first call is slow due to lazy init)
    dummy_board = torch.zeros(1, 18, 8, 8, dtype=_dtype, device=_device)
    dummy_scalar = torch.zeros(1, 8, dtype=_dtype, device=_device)
    with torch.no_grad():
        _model(dummy_board, dummy_scalar)

    return _model


@torch.no_grad()
def predict_batch(fens: List[str]) -> List[float]:
    """Evaluate many positions at once. Far more efficient than calling predict_fen in a loop."""
    model = load_model()
    if not fens:
        return []

    board_tensors = []
    scalar_tensors = []
    for fen in fens:
        bt, st = board_to_tensor_and_scalars(fen)
        board_tensors.append(bt)
        scalar_tensors.append(st)

    board_x = torch.stack(board_tensors).to(_device, dtype=_dtype, non_blocking=True)
    scalar_x = torch.stack(scalar_tensors).to(_device, dtype=_dtype, non_blocking=True)

    preds = model(board_x, scalar_x).float().cpu().numpy().flatten()
    preds = np.nan_to_num(preds, nan=0.0, posinf=1.0, neginf=-1.0)
    # Model output is unbounded; squash through tanh to get [-1, 1] while
    # preserving relative ordering (avoids saturation from hard clipping).
    preds = np.tanh(preds)
    return preds.tolist()


@torch.no_grad()
def predict_fen(fen: str) -> float:
    """Single-position evaluation. Prefer predict_batch when possible."""
    return predict_batch([fen])[0]
