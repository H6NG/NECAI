#pragma once
#include "board.h"
#include "moves.h"
#include "eval.h"

class Search {

    public:

        Search(Board& board);
        Move best_move(int depth);

    private:

        Board& board;
        MoveGenerator generator;
        Eval eval;

        int negamax(int depth, int alpha, int beta);
        
};