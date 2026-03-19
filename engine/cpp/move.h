#pragma once 

struct Move{

    int from;
    int to; 
    int promotion; 
    int captured; 
    bool is_en_passant; 
    bool is_castling; 

    //The Move constructor
    Move(int from, int to, int promotion, int captured, bool is_en_passant, bool is_castling) :
    from(from), to(to), promotion(promotion), captured(captured), is_castling(is_castling), is_en_passant(is_en_passant){}; 
}; 

