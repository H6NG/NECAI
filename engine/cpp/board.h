#pragma once
#include <string>
#include <array>


enum Piece {
    EMPTY = 0,
    WHITE_PAWN = 1, WHITE_KNIGHT = 2, WHITE_BISHOP = 3,
    WHITE_ROOK = 4, WHITE_QUEEN = 5,  WHITE_KING = 6,
    BLACK_PAWN = 7, BLACK_KNIGHT = 8, BLACK_BISHOP = 9,
    BLACK_ROOK = 10, BLACK_QUEEN = 11, BLACK_KING = 12
};

class Board {

    public: 

        Board(); //it's own constructor I've decided to do OOP 
        void load_fen(std::string fen); 
        bool is_white_turn(); 

    private: 

        std::array<int,64> squares; //my int arr[][]
        bool white_turn; 
        bool castle_wk; 
        bool castle_wq; 
        bool castle_bk; 
        bool castle_bq; 
        int en_passant; 

        //helper func 
        void parse_pieces(std::string board_part); 
        void parse_turn(std::string turn_part); 
        void parse_castling(std::string castle_part); 
        void parse_en_passant(std::string ep_part); 

}; 