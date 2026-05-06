#include "eval.h"

const int Eval::PAWN_TABLE[64] = {
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
};
const int Eval::KNIGHT_TABLE[64] = {
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
};
const int Eval::BISHOP_TABLE[64] = {
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
};
const int Eval::ROOK_TABLE[64] = {
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0
};
const int Eval::QUEEN_TABLE[64] = {
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
};
const int Eval::KING_MIDDLE_TABLE[64] = {
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
};
const int Eval::KING_END_TABLE[64] = {
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
};

Eval::Eval(Board& board) : board(board), generator(board) {}

int Eval::evaluate() {
    int score = 0;
    score += evaluate_material();
    score += evaluate_piece_square_tables();
    score += evaluate_pawn_structure();
    score += evaluate_king_safety();
    score += evaluate_mobility();
    return board.is_white_turn() ? score : -score;
}

int Eval::evaluate_material() {
    int score = 0;
    for (int i = 0; i < 64; i++) {
        switch (board.get_piece(i)) {
            case WHITE_PAWN: score += PAWN_VALUE; break;
            case WHITE_KNIGHT: score += KNIGHT_VALUE; break;
            case WHITE_BISHOP: score += BISHOP_VALUE; break;
            case WHITE_ROOK: score += ROOK_VALUE; break;
            case WHITE_QUEEN: score += QUEEN_VALUE; break;
            case BLACK_PAWN: score -= PAWN_VALUE; break;
            case BLACK_KNIGHT: score -= KNIGHT_VALUE; break;
            case BLACK_BISHOP: score -= BISHOP_VALUE; break;
            case BLACK_ROOK: score -= ROOK_VALUE; break;
            case BLACK_QUEEN: score -= QUEEN_VALUE; break;
            default: break;
        }
    }
    return score;
}

// Endgame when both sides have no queens, or queen + at most one minor/rook.
bool Eval::is_endgame() const {
    int queens = 0, minors_rooks = 0;
    for (int i = 0; i < 64; i++) {
        Piece p = board.get_piece(i);
        if (p == WHITE_QUEEN || p == BLACK_QUEEN) queens++;
        if (p == WHITE_ROOK || p == BLACK_ROOK ||
            p == WHITE_BISHOP || p == BLACK_BISHOP ||
            p == WHITE_KNIGHT || p == BLACK_KNIGHT) minors_rooks++;
    }
    return queens == 0 || (queens <= 2 && minors_rooks <= 2);
}

int Eval::evaluate_piece_square_tables() {
    int score = 0;
    bool endgame = is_endgame();
    for (int i = 0; i < 64; i++) {
        Piece p = board.get_piece(i);
        int mirror = (7 - i / 8) * 8 + (i % 8);
        switch (p) {
            case WHITE_PAWN: score += PAWN_TABLE[i]; break;
            case WHITE_KNIGHT: score += KNIGHT_TABLE[i]; break;
            case WHITE_BISHOP: score += BISHOP_TABLE[i]; break;
            case WHITE_ROOK: score += ROOK_TABLE[i]; break;
            case WHITE_QUEEN: score += QUEEN_TABLE[i]; break;
            case WHITE_KING: score += endgame ? KING_END_TABLE[i] : KING_MIDDLE_TABLE[i]; break;
            case BLACK_PAWN: score -= PAWN_TABLE[mirror]; break;
            case BLACK_KNIGHT: score -= KNIGHT_TABLE[mirror]; break;
            case BLACK_BISHOP: score -= BISHOP_TABLE[mirror]; break;
            case BLACK_ROOK: score -= ROOK_TABLE[mirror]; break;
            case BLACK_QUEEN: score -= QUEEN_TABLE[mirror]; break;
            case BLACK_KING: score -= endgame ? KING_END_TABLE[mirror] : KING_MIDDLE_TABLE[mirror]; break;
            default: break;
        }
    }
    return score;
}

int Eval::evaluate_pawn_structure() {
    int score = 0;
    int white_pawns_per_file[8] = {0};
    int black_pawns_per_file[8] = {0};

    for (int i = 0; i < 64; i++) {
        if (board.get_piece(i) == WHITE_PAWN) white_pawns_per_file[i % 8]++;
        if (board.get_piece(i) == BLACK_PAWN) black_pawns_per_file[i % 8]++;
    }

    for (int f = 0; f < 8; f++) {
        if (white_pawns_per_file[f] > 1) score -= 20 * (white_pawns_per_file[f] - 1);
        if (black_pawns_per_file[f] > 1) score += 20 * (black_pawns_per_file[f] - 1);

        bool white_isolated = white_pawns_per_file[f] > 0 &&
            (f == 0 || white_pawns_per_file[f-1] == 0) &&
            (f == 7 || white_pawns_per_file[f+1] == 0);
        bool black_isolated = black_pawns_per_file[f] > 0 &&
            (f == 0 || black_pawns_per_file[f-1] == 0) &&
            (f == 7 || black_pawns_per_file[f+1] == 0);

        if (white_isolated) score -= 15;
        if (black_isolated) score += 15;
    }
    return score;
}

int Eval::evaluate_king_safety() {
    int score = 0;
    int white_king = -1, black_king = -1;

    for (int i = 0; i < 64; i++) {
        if (board.get_piece(i) == WHITE_KING) white_king = i;
        if (board.get_piece(i) == BLACK_KING) black_king = i;
    }

    // Check pawns directly in front and diagonally in front of the king.
    // Guard against file-wrapping: diagonal squares must be on an adjacent file.
    for (int dir : {-7, -8, -9}) {
        int sq = white_king + dir;
        if (sq >= 0 && sq < 64) {
            if (dir == -8 || abs(sq % 8 - white_king % 8) == 1) {
                if (board.get_piece(sq) == WHITE_PAWN) score += 10;
            }
        }
    }
    for (int dir : {7, 8, 9}) {
        int sq = black_king + dir;
        if (sq >= 0 && sq < 64) {
            if (dir == 8 || abs(sq % 8 - black_king % 8) == 1) {
                if (board.get_piece(sq) == BLACK_PAWN) score -= 10;
            }
        }
    }
    return score;
}

int Eval::evaluate_mobility() {
    std::vector<Move> my_moves;
    generator.generate_legal_moves(my_moves);

    // temporarily flip turn to count opponent moves
    board.flip_turn();
    MoveGenerator opp_gen(board);
    std::vector<Move> opp_moves;
    opp_gen.generate_legal_moves(opp_moves);
    board.flip_turn();

    return ((int)my_moves.size() - (int)opp_moves.size()) * 5;
}