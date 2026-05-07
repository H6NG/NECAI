// Streaming classical evaluator: reads FENs from stdin (one per line),
// prints evaluation scores to stdout (one per line, in centipawns from
// White's perspective).
//
// Build: see Makefile target `eval_stream`.

#include <iostream>
#include <string>

#include "../../documentation/board.h"
#include "eval.h"

int main() {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(nullptr);

    std::string fen;
    while (std::getline(std::cin, fen)) {
        if (fen.empty()) continue;

        Board board;
        board.load_fen(fen);

        Eval eval(board);
        int score = eval.evaluate();

        // evaluate() returns score from side-to-move perspective.
        // Flip to White's perspective for consistency with the neural eval.
        if (!board.is_white_turn()) score = -score;

        std::cout << score << "\n";
    }

    std::cout.flush();
    return 0;
}
