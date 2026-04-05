from pathlib import Path
from typing import Optional

import torch

from model.model import NECAIEvaluator, board_to_tensor_and_scalars


MODEL_FILE = Path(__file__).resolve().parent / "necai_eval.pt"

_device: Optional[torch.device] = None
_model: Optional[NECAIEvaluator] = None


def get_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def load_model() -> NECAIEvaluator:
    global _model, _device

    if _model is not None:
        return _model

    _device = get_device()
    model = NECAIEvaluator().to(_device)

    if not MODEL_FILE.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_FILE}")

    checkpoint = torch.load(MODEL_FILE, map_location=_device)

    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)

    model.eval()
    _model = model
    return _model


@torch.no_grad()
def predict_fen(fen: str) -> float:
    global _device

    model = load_model()

    if _device is None:
        _device = get_device()

    board_tensor, scalar_tensor = board_to_tensor_and_scalars(fen)

    board_tensor = board_tensor.unsqueeze(0).to(_device)   # [1, 18, 8, 8]
    scalar_tensor = scalar_tensor.unsqueeze(0).to(_device) # [1, 8]

    pred = model(board_tensor, scalar_tensor)
    return float(pred.item())