/**This file has as purpose to find the best moves using the following techniques
 *
 * - Negamax
 * - Alpha-beta pruning
 * - Move ordering (captures first)
 * - Quiescence search
 * - Eval function
 */

#include "search.h"
#include <limits>
#include <stdexcept>
#include <algorithm>

Search::Search(Board& board) : board(board), generator(board), eval(board) {}


// Captures are searched first to improve alpha-beta cutoff rate.
static void order_moves(std::vector<Move>& moves) {
    std::stable_partition(moves.begin(), moves.end(), [](const Move& m) {
        return m.captured != EMPTY;
    });
}

// Quiescence search: keep searching captures at the leaf to avoid the horizon effect.
int Search::quiescence(int alpha, int beta) {
    int stand_pat = eval.evaluate();

    if (stand_pat >= beta) return beta;
    if (stand_pat > alpha) alpha = stand_pat;

    std::vector<Move> moves = generator.generate_moves();

    for (auto& move : moves) {
        if (move.captured == EMPTY) continue; // only captures

        board.make_move(move);
        int score = -quiescence(-beta, -alpha);
        board.unmake_move(move);

        if (score >= beta) return beta;
        if (score > alpha) alpha = score;
    }

    return alpha;
}

Move Search::best_move(int depth) {
    std::vector<Move> moves = generator.generate_moves();

    if (moves.empty()) {
        throw std::runtime_error("No legal moves");
    }

    if (moves.size() == 1) {
        return moves[0];
    }

    order_moves(moves);

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

// Returns up to K moves sorted by classical score, best first.
std::vector<ScoredMove> Search::top_k_moves(int depth, int k) {
    std::vector<Move> moves = generator.generate_moves();
    std::vector<ScoredMove> scored;
    scored.reserve(moves.size());

    order_moves(moves);

    for (const auto& move : moves) {
        board.make_move(move);
        int score = -negamax(
            depth - 1,
            std::numeric_limits<int>::min() + 1,
            std::numeric_limits<int>::max()
        );
        board.unmake_move(move);
        scored.push_back({move, score});
    }

    std::sort(scored.begin(), scored.end(),
              [](const ScoredMove& a, const ScoredMove& b) { return a.score > b.score; });

    if ((int)scored.size() > k) scored.erase(scored.begin() + k, scored.end());
    return scored;
}

int Search::negamax(int depth, int alpha, int beta) {
    if (depth == 0) return quiescence(alpha, beta);

    std::vector<Move> moves = generator.generate_moves();

    if (moves.empty()) {
        if (board.is_in_check(board.is_white_turn())) return -99999; // checkmate
        return 0; // stalemate
    }

    order_moves(moves);

    for (auto& move : moves) {
        board.make_move(move);
        int score = -negamax(depth - 1, -beta, -alpha);
        board.unmake_move(move);

        if (score >= beta) return beta;
        if (score > alpha) alpha = score;
    }
    return alpha;
}
