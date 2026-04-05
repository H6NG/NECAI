// Legal Move Checker for testing purposes

#include <iostream>
#include <string>

#include "../engine/cpp/board.h"
#include "../engine/cpp/move.h"
#include "../engine/cpp/moves.h"

int main()
{
    Board board;

    std::string fen;
    std::cout << "Enter FEN: ";
    std::getline(std::cin, fen);

    board.load_fen(fen);

    std::cout << "\nYou entered:\n" << fen << std::endl;

    MoveGenerator generator(board);
    auto moves = generator.generate_moves();

    std::cout << "\nLegal moves (" << moves.size() << "):\n";

    for (const auto& move : moves) {
        std::cout << move_to_uci(move) << std::endl;
    }
    std::cout << "White to move? " << board.is_white_turn() << std::endl;
    std::cout << "Black to move? " << !board.is_white_turn() << std::endl;
    std::cout << "Black in check? " << board.is_in_check(board.is_white_turn()) << std::endl;
    std::cout << "White in check? " << board.is_in_check(!board.is_white_turn()) << std::endl;

    return 0; // optional but clean
}