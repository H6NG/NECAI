#include "../cpp/board.h"
#include "../cpp/search.h"
#include <iostream>
#include <sstream>
#include <string>

//g++ -O2 -std=c++17 -I../engine/cpp -o testengine testengine.cpp ../engine/cpp/board.cpp ../engine/cpp/moves.cpp ../engine/cpp/eval.cpp ../engine/cpp/search.cpp

std::string move_to_uci(const Move& move) {
    std::string result = "";
    result += (char)('a' + move.from % 8);
    result += (char)('8' - move.from / 8);
    result += (char)('a' + move.to % 8);
    result += (char)('8' - move.to / 8);
    if (move.promotion != EMPTY) {
        switch (move.promotion) {
            case WHITE_QUEEN: case BLACK_QUEEN: result += 'q'; break;
            case WHITE_ROOK: case BLACK_ROOK: result += 'r'; break;
            case WHITE_BISHOP: case BLACK_BISHOP: result += 'b'; break;
            case WHITE_KNIGHT: case BLACK_KNIGHT: result += 'n'; break;
            default: break;
        }
    }
    return result;
}

Move uci_to_move(const std::string& uci, Board& board) {
    int from = (uci[0] - 'a') + (8 - (uci[1] - '0')) * 8;
    int to   = (uci[2] - 'a') + (8 - (uci[3] - '0')) * 8;

    MoveGenerator generator(board);
    std::vector<Move> moves = generator.generate_moves();
    for (auto& move : moves) {
        if (move.from == from && move.to == to) {
            if (uci.size() == 5) {
                // promotion — match the promotion piece
                char promo = uci[4];
                bool is_white = board.is_white_turn();
                Piece expected = EMPTY;
                if (promo == 'q') expected = is_white ? WHITE_QUEEN : BLACK_QUEEN;
                if (promo == 'r') expected = is_white ? WHITE_ROOK : BLACK_ROOK;
                if (promo == 'b') expected = is_white ? WHITE_BISHOP : BLACK_BISHOP;
                if (promo == 'n') expected = is_white ? WHITE_KNIGHT : BLACK_KNIGHT;
                if (move.promotion == expected) return move;
            } else {
                return move;
            }
        }
    }
    return Move(from, to); // fallback
}

int main() {
    Board board;
    std::string line;

    while (std::getline(std::cin, line)) {
        std::istringstream ss(line);
        std::string token;
        ss >> token;

        if (token == "uci") {
            std::cout << "id name NECAI\n";
            std::cout << "id author you\n";
            std::cout << "uciok\n";
        }
        else if (token == "isready") {
            std::cout << "readyok\n";
        }
        else if (token == "position") {
            ss >> token;
            if (token == "startpos") {
                board.load_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
                ss >> token; // consume "moves" if present
            } else if (token == "fen") {
                std::string fen = "";
                while (ss >> token && token != "moves") fen += token + " ";
                board.load_fen(fen);
            }
            // apply moves
            while (ss >> token) {
                Move move = uci_to_move(token, board);
                board.make_move(move);
            }
        }
        else if (token == "go") {
            int depth = 10; // default depth
            while (ss >> token) {
                if (token == "depth") ss >> depth;
            }
            Search search(board);
            Move best = search.best_move(depth);
            std::cout << "bestmove " << move_to_uci(best) << "\n";
        }
        else if (token == "quit") {
            break;
        }
    }
    return 0;
}