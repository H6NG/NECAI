#pragma once
#include "move.h"
#include "board.h"
#include <vector>

class MoveGenerator {

    //gives you all the possible moves whether it is the best or the worst

    public: 
        MoveGenerator(Board& board); //constructor
        std::vector<Move> generate_moves(); 

    private: 
        Board& board; 
        void generate_pawn_moves(std::vector<Move>& moves); 
        void generate_bishop_moves(std::vector<Move>& moves); 
        void generate_rook_moves(std::vector<Move>& moves); 
        void generate_knight_moves(std::vector<Move>& moves); 
        void generate_queen_moves(std::vector<Move>& moves); 
        void generate_king_moves(std::vector<Move>& moves); 

}; 