#pragma once
#include <string>
#include <array>
#include "move.h"

class Board {

    public: 

        Board(); //it's own constructor I've decided to do OOP 
        void load_fen(const std::string& fen); 
        bool is_white_turn(); 
        Piece get_piece(int square) const; 
        int get_en_passant() const; 
        void make_move(const Move& move);
        void unmake_move(const Move& move);

    private: 

        std::array<int,64> squares; //my int arr[][]
        bool white_turn; 
        bool castle_wk; 
        bool castle_wq; 
        bool castle_bk; 
        bool castle_bq; 
        int en_passant; 
        int halfmove; 
        int fullmove;

        //helper func 
        void parse_pieces(const std::string& board_part); 
        void parse_turn(const std::string& turn_part); 
        void parse_castling(const std::string& castle_part); 
        void parse_en_passant(const std::string& ep_part); 
        void parse_halfmove(const std::string& hm_part); 
        void parse_fullmove(const std::string& fm_part);
        void checkRep(); 

}; 