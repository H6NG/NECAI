"""
Export the trained NECAI model to TorchScript with FP16 weights.
This produces a self-contained .pt file callable from Python or LibTorch (C++).

Usage:
    python -m evaluator.neural_eval.export_jit
"""
from pathlib import Path

import torch

from evaluator.neural_eval.struct import NECAIEvaluator

HERE = Path(__file__).resolve().parent
MODEL_FILE = HERE / "necai_eval.pt"
JIT_FILE = HERE / "necai_eval_jit.pt"


def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def main():
    device = get_device()
    print(f"Exporting on: {device}")

    model = NECAIEvaluator().to(device)
    checkpoint = torch.load(MODEL_FILE, map_location=device, weights_only=True)
    state = checkpoint["model_state_dict"] if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint else checkpoint
    model.load_state_dict(state)
    model.eval()

    # Keep FP32 for numerical accuracy (FP16 saturates on this model).
    dtype = torch.float32
    example_board = torch.zeros(1, 18, 8, 8, dtype=dtype, device=device)
    example_scalar = torch.zeros(1, 8, dtype=dtype, device=device)

    with torch.no_grad():
        traced = torch.jit.trace(model, (example_board, example_scalar))

    # Optimize for inference (fuses ops, removes dropout, etc.)
    traced = torch.jit.optimize_for_inference(traced)

    traced.save(str(JIT_FILE))
    print(f"Saved TorchScript model to {JIT_FILE}")
    print(f"Size: {JIT_FILE.stat().st_size / 1e6:.1f} MB")

    # Sanity check
    out = traced(example_board, example_scalar)
    print(f"Sanity output shape: {out.shape}, value: {out.item():.4f}")


if __name__ == "__main__":
    main()
