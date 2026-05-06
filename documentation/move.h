#pragma once
#include <string>
#include "pieces.h"

struct Move {
    int from;
    int to;
    Piece promotion;
    Piece captured;
    bool is_en_passant;
    bool is_castling;

    Move(
        int from,
        int to,
        Piece promotion = EMPTY,
        Piece captured = EMPTY,
        bool is_en_passant = false,
        bool is_castling = false
    )
        : from(from),
          to(to),
          promotion(promotion),
          captured(captured),
          is_en_passant(is_en_passant),
          is_castling(is_castling) {}
};

std::string square_to_uci(int square);
char promotion_to_uci(Piece piece);
std::string move_to_uci(const Move& move);