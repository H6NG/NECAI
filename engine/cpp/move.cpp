#include "move.h"
#include <string>

std::string square_to_uci(int square) {
    int file = square % 8;
    int rank = square / 8;

    char file_char = 'a' + file;
    char rank_char = '8' - rank;

    return std::string{file_char, rank_char};
}

char promotion_to_uci(Piece piece) {
    switch (piece) {
        case WHITE_QUEEN:
        case BLACK_QUEEN:
            return 'q';
        case WHITE_ROOK:
        case BLACK_ROOK:
            return 'r';
        case WHITE_BISHOP:
        case BLACK_BISHOP:
            return 'b';
        case WHITE_KNIGHT:
        case BLACK_KNIGHT:
            return 'n';
        default:
            return '\0';
    }
}

std::string move_to_uci(const Move& move) {
    std::string uci = square_to_uci(move.from) + square_to_uci(move.to);

    char promo = promotion_to_uci(move.promotion);
    if (promo != '\0') {
        uci += promo;
    }

    return uci;
}