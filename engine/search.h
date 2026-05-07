#pragma once
#include <vector>
#include "../documentation/board.h"
#include "../documentation/moves.h"
#include "../evaluator/classical_eval/eval.h"

struct ScoredMove {
    Move move;
    int score;
};

class Search {

    public:

        Search(Board& board);
        Move best_move(int depth);
        std::vector<ScoredMove> top_k_moves(int depth, int k);

    private:

        Board& board;
        MoveGenerator generator;
        Eval eval;

        int negamax(int depth, int alpha, int beta);
        int quiescence(int alpha, int beta);

};