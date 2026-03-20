#pragma once 
#include "pieces.h"

struct Move{

    int from;
    int to; 
    Piece promotion; 
    Piece captured; 
    bool is_en_passant; 
    bool is_castling; 

    //The Move constructor
    Move(int from, int to, Piece promotion = EMPTY, Piece captured = EMPTY, bool is_en_passant = false, bool is_castling = false) :
    from(from), to(to), promotion(promotion), captured(captured), is_castling(is_castling), is_en_passant(is_en_passant){}; 
}; 

