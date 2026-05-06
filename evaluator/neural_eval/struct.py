import chess
import numpy as np
import torch
import torch.nn as nn
from typing import Tuple


PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


def board_to_tensor_and_scalars(fen: str) -> Tuple[torch.Tensor, torch.Tensor]:
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


class ResBlock(nn.Module):
    def __init__(self, channels: int):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
        )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.relu(x + self.block(x))


class NECAIEvaluator(nn.Module):
    def __init__(self, scalar_dim: int = 8):
        super().__init__()

        # Input projection: 18 → 128 channels, keep 8×8
        self.input_conv = nn.Sequential(
            nn.Conv2d(18, 128, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
        )

        # 6 residual blocks, all at 128 channels, 8×8 spatial resolution
        self.res_blocks = nn.Sequential(
            ResBlock(128),
            ResBlock(128),
            ResBlock(128),
            ResBlock(128),
            ResBlock(128),
            ResBlock(128),
        )

        # Flatten 128×8×8 = 8192 → 512
        self.board_head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 8 * 8, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
        )

        self.scalar_head = nn.Sequential(
            nn.Linear(scalar_dim, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.1),
        )

        self.final = nn.Sequential(
            nn.Linear(512 + 64, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.25),
            nn.Linear(256, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1),
        )

    def forward(self, board_x, scalar_x):
        board_feat = self.board_head(self.res_blocks(self.input_conv(board_x)))
        scalar_feat = self.scalar_head(scalar_x)
        combined = torch.cat([board_feat, scalar_feat], dim=1)
        return self.final(combined)
