#pragma once
#include <string>
#include <array>


class Board {

    public: 

        void load_fen(std::string fen); 
        bool is_white_turn(); 

    private: 

        std::array<int,64> squares;
        bool white_turn; 
        bool castle_wk; 
        bool castle_wq; 
        bool castle_bk; 
        bool castle_bq; 
        int en_passant; 

        //helper func 
        void _parse_pieces(std::string board_part); 
        void _parse_turn(std::string turn_part); 
        void _parse_castling(std::string castle_part); 
        void _parse_en_passant(); 

}; 