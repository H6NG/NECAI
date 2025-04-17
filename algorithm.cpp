#include <iostream>
#include <fstream>
#include <vector>
#include <string>

// Simple evaluation function to score a move
double evaluate_move(const std::string& move, char board[8][8]) {
    // Extract destination square (e.g., "e5" from "e7e5")
    int to_col = move[2] - 'a';
    int to_row = 7 - (move[3] - '1');

    // Heuristic: Prefer moves that control the center (d4, d5, e4, e5)
    if ((to_col == 3 || to_col == 4) && (to_row == 3 || to_row == 4)) {
        return 2.0; // High score for center pawn moves (e7e5, d7d5)
    }

    // Prefer knight development to c6 or f6
    if (move == "b8c6" || move == "g8f6") {
        return 1.5;
    }

    // Default score for other moves (e.g., a7a6, h7h5)
    return 1.0;
}

// Find the best move
std::string find_best_move(const std::vector<std::string>& moves, char board[8][8]) {
    if (moves.empty()) return "";
    
    std::string best_move = moves[0];
    double best_score = evaluate_move(moves[0], board);

    for (const auto& move : moves) {
        double score = evaluate_move(move, board);
        if (score > best_score) {
            best_score = score;
            best_move = move;
        }
    }

    return best_move;
}

int main() {
    // Read necai.txt
    std::ifstream file("necai.txt");
    if (!file.is_open()) {
        std::cerr << "Error: Could not open necai.txt" << std::endl;
        return 1;
    }

    std::string color;
    std::getline(file, color); // Read "b" for Black
    bool is_white = (color == "w");

    // Initialize board (row 0 = rank 8, col 0 = file a)
    char board[8][8];
    for (int row = 0; row < 8; ++row) {
        std::string line;
        std::getline(file, line);
        // Extract pieces (skip rank number and spaces)
        int col = 0;
        for (char c : line) {
            if (c == ' ' || (c >= '1' && c <= '8')) continue; // Skip spaces and rank numbers
            if (col < 8) {
                board[row][col] = c;
                ++col;
            }
        }
    }
    file.close();

    // Simulate possible_moves.cpp output (replace with actual integration if possible)
    std::vector<std::string> moves = {
        "b8a6", "b8c6", "g8f6", "g8h6",
        "a7a6", "a7a5", "b7b6", "b7b5",
        "c7c6", "c7c5", "d7d6", "d7d5",
        "e7e6", "e7e5", "f7f6", "f7f5",
        "g7g6", "g7g5", "h7h6", "h7h5"
    };

    // Find the best move
    std::string best_move = find_best_move(moves, board);
    if (best_move.empty()) {
        std::cerr << "Error: No best move found" << std::endl;
        return 1;
    }

    // Print the best move
    std::cout << best_move << std::endl;

    return 0;
}