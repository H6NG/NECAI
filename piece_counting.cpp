//This file is mainly for counting the pieces on the chessboard

#include <iostream>
#include <fstream>
#include <string>

int main() {
    // Open necai.txt
    std::ifstream file("necai.txt");
    if (!file.is_open()) {
        std::cerr << "Error: Could not open necai.txt" << std::endl;
        return 1;
    }

    // Read color (b or w)
    std::string color;
    std::getline(file, color);

    // Initialize board (row 0 = rank 8, col 0 = file h)
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

    // Count pieces
    int white_pieces = 0;
    int black_pieces = 0;
    for (int row = 0; row < 8; ++row) {
        for (int col = 0; col < 8; ++col) {
            char piece = board[row][col];
            if (piece >= 'A' && piece <= 'Z') {
                ++white_pieces; // Uppercase: White piece
            } else if (piece >= 'a' && piece <= 'z') {
                ++black_pieces; // Lowercase: Black piece
            }
            // Ignore '.' (empty squares)
        }
    }

    // Output counts
    std::cout << "Black pieces: " << white_pieces << "\n";
    std::cout << "White pieces: " << black_pieces << "\n";

    return 0;
}