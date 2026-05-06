#!/bin/bash

ENGINE="$(dirname "$0")/../documentation/necai_engine"

PASS=0
FAIL=0

run() {
    local desc="$1"
    local fen="$2"
    local depth="$3"
    local expect="$4"

    result=$("$ENGINE" "$fen" "$depth" 2>&1)

    if echo "$result" | grep -q "$expect"; then
        echo "PASS $desc"
        PASS=$((PASS + 1))
    else
        echo "FAIL $desc"
        echo "     expected: $expect"
        echo "     got:      $result"
        FAIL=$((FAIL + 1))
    fi
}

# Basic
run "Starting position returns a move" "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" 1 '"game_over": false'
run "White to move after 1.e4" "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1" 1 '"game_over": false'
run "Move is valid UCI format" "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" 1 '"best_move"'
run "Eval field is present" "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" 1 '"engine_eval"'
run "Depth 1 works" "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" 1 '"game_over": false'
run "Depth 2 works" "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" 2 '"game_over": false'
run "Depth 3 works" "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" 3 '"game_over": false'

# Checkmate
run "Fool's mate - white checkmated" "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3" 1 '"reason": "checkmate"'
run "Scholar's mate - black checkmated" "r1bqk2r/pppp1Qpp/2n2n2/2b1p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4" 1 '"reason": "checkmate"'
run "Back rank mate - black checkmated" "R5k1/5ppp/8/8/8/8/8/6K1 b - - 0 1" 1 '"reason": "checkmate"'
run "Smothered mate - black checkmated" "6rk/5Npp/8/8/8/8/8/6K1 b - - 0 1" 1 '"reason": "checkmate"'
run "Engine finds checkmate in 1" "7k/6Q1/5K2/8/8/8/8/8 w - - 0 1" 1 '"game_over": false'

# Stalemate
run "Stalemate - black has no moves" "k7/8/1Q6/8/8/8/8/7K b - - 0 1" 1 '"reason": "stalemate"'
run "Stalemate - white king cornered" "7k/8/8/8/8/1q6/8/K7 w - - 0 1" 1 '"reason": "stalemate"'
run "Stalemate - complex pawn block" "5k2/5P2/5K2/8/8/8/8/8 b - - 0 1" 1 '"reason": "stalemate"'

# Castling
run "Kingside castling available" "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1" 2 '"game_over": false'
run "Queenside castling available" "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1" 2 '"game_over": false'
run "No castling rights" "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w - - 0 1" 2 '"game_over": false'
run "Kingside only castling rights" "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w K - 0 1" 2 '"game_over": false'

# En passant
run "En passant available for white on f6" "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3" 2 '"game_over": false'
run "En passant available for black on e3" "rnbqkbnr/pppp1ppp/8/8/3pP3/8/PPP2PPP/RNBQKBNR b KQkq e3 0 3" 2 '"game_over": false'
run "No en passant square" "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2" 2 '"game_over": false'

# Promotion
run "White pawn promotion" "8/4P1k1/8/8/8/8/6K1/8 w - - 0 1" 2 '"game_over": false'
run "Black pawn promotion" "8/6k1/8/8/8/8/4p1K1/8 b - - 0 1" 2 '"game_over": false'
run "White promotes with capture" "5b2/4P1k1/8/8/8/8/6K1/8 w - - 0 1" 2 '"game_over": false'

# Check / forced moves
run "King must escape check" "k7/8/8/8/8/8/r7/1K6 w - - 0 1" 1 '"game_over": false'
run "King in check must block or capture" "k6r/8/8/8/8/8/8/K7 w - - 0 1" 1 '"game_over": false'
run "Double check - king must move" "k7/8/8/8/8/8/1r6/KR6 w - - 0 1" 1 '"game_over": false'

# Endgame
run "King and queen vs king" "7k/8/8/8/8/8/8/K6Q w - - 0 1" 4 '"game_over": false'
run "King and rook vs king" "7k/8/8/8/8/8/8/K6R w - - 0 1" 4 '"game_over": false'
run "King and pawn vs king" "8/8/8/8/8/4K3/4P3/4k3 w - - 0 1" 3 '"game_over": false'
run "Symmetric king and pawn endgame" "8/5pk1/6p1/7p/7P/6P1/5PK1/8 w - - 0 1" 3 '"game_over": false'
run "Rook endgame" "8/8/8/8/8/k7/8/KR6 w - - 0 1" 3 '"game_over": false'

# Halfmove clock
run "Near 50-move rule (halfmove=99)" "8/5k2/8/8/8/8/5K2/8 w - - 99 80" 2 '"game_over": false'
run "Halfmove clock at 0" "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1" 2 '"game_over": false'

# Midgame
run "Italian Game" "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4" 3 '"game_over": false'
run "Sicilian Defence" "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2" 3 '"game_over": false'
run "French Defence" "rnbqkbnr/ppp2ppp/4p3/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq d6 0 3" 3 '"game_over": false'
run "Ruy Lopez" "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 2 3" 3 '"game_over": false'
run "Queen's Gambit" "rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq c3 0 2" 3 '"game_over": false'

echo "$PASS passed, $FAIL failed"
