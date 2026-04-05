
/**This file has as purpose to find the best moves using the following techniques
 * 
 * - Maximax 
 * - Alpha-beta pruning
 * - Eval function 
 */

#include "search.h"
#include <limits>

Search::Search(Board& board) : board(board), generator(board), eval(board) {}


Move Search::best_move(int depth) {
    std::vector<Move> moves = generator.generate_moves();

    if (moves.empty()) {
        throw std::runtime_error("No legal moves");
    }

    if (moves.size() == 1) {
        return moves[0];
    }

    Move best = moves[0];
    int best_score = std::numeric_limits<int>::min();

    for (const auto& move : moves) {
        board.make_move(move);
        int score = -negamax(
            depth - 1,
            std::numeric_limits<int>::min() + 1,
            std::numeric_limits<int>::max()
        );
        board.unmake_move(move);

        if (score > best_score) {
            best_score = score;
            best = move;
        }
    }

    return best;
}

int Search::negamax(int depth, int alpha, int beta) {
    if (depth == 0) return eval.evaluate();

    std::vector<Move> moves = generator.generate_moves();

    if (moves.empty()) {
        if (board.is_in_check(board.is_white_turn())) return -99999; // checkmate
        return 0; // stalemate
    }

    for (auto& move : moves) {
        board.make_move(move);
        int score = -negamax(depth - 1, -beta, -alpha);
        board.unmake_move(move);

        if (score >= beta) return beta; // beta cutoff
        if (score > alpha) alpha = score;
    }
    return alpha;
}