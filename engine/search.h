#pragma once
#include "../documentation/board.h"
#include "../documentation/moves.h"
#include "../evaluator/eval.h"

class Search {

    public:

        Search(Board& board);
        Move best_move(int depth);

    private:

        Board& board;
        MoveGenerator generator;
        Eval eval;

        int negamax(int depth, int alpha, int beta);
        int quiescence(int alpha, int beta);
        
};