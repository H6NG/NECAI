// Prints the top-K moves from classical negamax search.
// Output: K lines, each "uci_move classical_score resulting_fen"
//
// Usage: ./top_moves "<fen>" <depth> [k]

#include <iostream>
#include <string>

#include "../documentation/board.h"
#include "../documentation/move.h"
#include "search.h"

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "Usage: ./top_moves \"<fen>\" <depth> [k]\n";
        return 1;
    }

    std::string fen = argv[1];
    int depth = std::atoi(argv[2]);
    int k = (argc >= 4) ? std::atoi(argv[3]) : 5;

    if (depth < 1) depth = 1;
    if (k < 1) k = 1;

    Board board;
    board.load_fen(fen);

    Search search(board);
    auto top = search.top_k_moves(depth, k);

    for (const auto& sm : top) {
        board.make_move(sm.move);
        std::string after_fen = board.to_fen();
        board.unmake_move(sm.move);
        std::cout << move_to_uci(sm.move) << " " << sm.score << " " << after_fen << "\n";
    }

    return 0;
}
