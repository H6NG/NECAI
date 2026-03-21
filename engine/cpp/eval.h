#pragma once
#include "board.h"
#include "moves.h"

class Eval {
public:
    Eval(Board& board);
    int evaluate();

private:
    Board& board;
    MoveGenerator generator;

    static const int PAWN_VALUE = 100;
    static const int KNIGHT_VALUE = 320;
    static const int BISHOP_VALUE = 330;
    static const int ROOK_VALUE = 500;
    static const int QUEEN_VALUE = 900;

    // individual eval components
    int evaluate_material();
    int evaluate_piece_square_tables();
    int evaluate_pawn_structure();
    int evaluate_king_safety();
    int evaluate_mobility();

    // piece square tables
    static const int PAWN_TABLE[64];
    static const int KNIGHT_TABLE[64];
    static const int BISHOP_TABLE[64];
    static const int ROOK_TABLE[64];
    static const int QUEEN_TABLE[64];
    static const int KING_MIDDLE_TABLE[64];
    static const int KING_END_TABLE[64];
};