#include <iostream>
#include <string>
#include <vector>
#include <cstdlib>

#include "board.h"
#include "moves.h"
#include "search.h"
#include "eval.h"
#include "move.h"

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "Usage: ./necai_engine \"<fen>\" <depth>\n";
        return 1;
    }

    std::string fen = argv[1];
    int depth = std::atoi(argv[2]);

    if (depth < 1) {
        depth = 1;
    }

    Board board;
    board.load_fen(fen);

    MoveGenerator generator(board);
    std::vector<Move> legal_moves = generator.generate_moves();

    if (legal_moves.empty()) {
        bool in_check = board.is_in_check(board.is_white_turn());

        std::cout << "{";
        std::cout << "\"best_move\": null, ";
        std::cout << "\"game_over\": true, ";
        std::cout << "\"reason\": \"" << (in_check ? "checkmate" : "stalemate") << "\"";
        std::cout << "}\n";

        return 0;
    }

    Search search(board);
    Move best = search.best_move(depth);

    Eval eval(board);
    int current_eval = eval.evaluate();

    std::cout << "{";
    std::cout << "\"best_move\": \"" << move_to_uci(best) << "\", ";
    std::cout << "\"engine_eval\": " << current_eval << ", ";
    std::cout << "\"game_over\": false";
    std::cout << "}\n";

    return 0;
}