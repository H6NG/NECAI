
// This file has a purpose of mapping the chessboard to a 2d array.
// INPUT: By default: w, but if the user switches, then b
// OUTPUT: what colour NECAI is playing as w or b in a file called necai.txt

#include <array>
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <algorithm>

// Define piece types and colors
enum Piece { EMPTY, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING };
enum Color { WHITE, BLACK };

// Struct to hold piece and color for each square
struct Square {
    Piece piece = EMPTY;
    Color color; // Only matters if piece != EMPTY
};

// Use a 64-element array to represent the 8x8 board
using Board = std::array<Square, 64>;

// Function to initialize the board to the starting chess position
void initializeBoard(Board& board) {
    // Clear board
    for (int i = 0; i < 64; i++) {
        board[i] = {EMPTY, WHITE}; // Color is irrelevant for empty squares
    }

    // Set up white pieces (lowercase in notation: p=pawn, n=knight, etc.)
    board[0] = {ROOK, WHITE};   // a1
    board[1] = {KNIGHT, WHITE}; // b1
    board[2] = {BISHOP, WHITE}; // c1
    board[3] = {QUEEN, WHITE};  // d1
    board[4] = {KING, WHITE};   // e1
    board[5] = {BISHOP, WHITE}; // f1
    board[6] = {KNIGHT, WHITE}; // g1
    board[7] = {ROOK, WHITE};   // h1
    // White pawns on rank 2 (a2 to h2)
    for (int i = 8; i < 16; i++) {
        board[i] = {PAWN, WHITE};
    }

    // Set up black pieces (uppercase in notation)
    board[56] = {ROOK, BLACK};   // a8
    board[57] = {KNIGHT, BLACK}; // b8
    board[58] = {BISHOP, BLACK}; // c8
    board[59] = {QUEEN, BLACK};  // d8
    board[60] = {KING, BLACK};   // e8
    board[61] = {BISHOP, BLACK}; // f8
    board[62] = {KNIGHT, BLACK}; // g8
    board[63] = {ROOK, BLACK};   // h8
    // Black pawns on rank 7 (a7 to h7)
    for (int i = 48; i < 56; i++) {
        board[i] = {PAWN, BLACK};
    }
}

// Function to output the board to a stream (console or file)
void outputBoard(const Board& board, bool blackPerspective, std::ostream& out) {
    if (blackPerspective) {
        for (int rank = 0; rank < 8; rank++) { // Start from rank 1 (a1-h1) to rank 8
            out << (rank + 1) << " "; // Rank numbers 1 to 8
            for (int file = 7; file >= 0; file--) { // Files h to a
                int idx = rank * 8 + file;
                Square sq = board[idx];
                char c;
                if (sq.piece == EMPTY) {
                    c = '.';
                } else {
                    switch (sq.piece) {
                        case PAWN:   c = (sq.color == WHITE ? 'p' : 'P'); break;
                        case KNIGHT: c = (sq.color == WHITE ? 'n' : 'N'); break;
                        case BISHOP: c = (sq.color == WHITE ? 'b' : 'B'); break;
                        case ROOK:   c = (sq.color == WHITE ? 'r' : 'R'); break;
                        case QUEEN:  c = (sq.color == WHITE ? 'q' : 'Q'); break;
                        case KING:   c = (sq.color == WHITE ? 'k' : 'K'); break;
                        default: c = '?';
                    }
                }
                out << c << " ";
            }
            out << "\n";
        }
        out << "  h g f e d c b a\n";
    } else {
        for (int rank = 7; rank >= 0; rank--) { // Start from rank 8 to 1
            out << (rank + 1) << " ";
            for (int file = 0; file < 8; file++) {
                int idx = rank * 8 + file;
                Square sq = board[idx];
                char c;
                if (sq.piece == EMPTY) {
                    c = '.';
                } else {
                    switch (sq.piece) {
                        case PAWN:   c = (sq.color == WHITE ? 'p' : 'P'); break;
                        case KNIGHT: c = (sq.color == WHITE ? 'n' : 'N'); break;
                        case BISHOP: c = (sq.color == WHITE ? 'b' : 'B'); break;
                        case ROOK:   c = (sq.color == WHITE ? 'r' : 'R'); break;
                        case QUEEN:  c = (sq.color == WHITE ? 'q' : 'Q'); break;
                        case KING:   c = (sq.color == WHITE ? 'k' : 'K'); break;
                        default: c = '?';
                    }
                }
                out << c << " ";
            }
            out << "\n";
        }
        out << "  a b c d e f g h\n";
    }
}

// Main function to test the board and AI
int main() {
    std::string answer;
    std::cout << "Is NECAI black(b) or white(w)? ";
    std::getline(std::cin, answer); // Read user input

    Board board;
    initializeBoard(board);
    Color aiColor;
    bool blackPerspective;
    std::string colorOutput;

    if (answer == "b") {
        aiColor = BLACK;
        blackPerspective = true;
        colorOutput = "b";
    } else {
        // Default to white for 'w' or invalid input
        aiColor = WHITE;
        blackPerspective = false;
        colorOutput = "w";
    }

    // Output the color NECAI is playing as
    std::cout << "NECAI is playing as: " << colorOutput << "\n";

    // Print board to console
    std::cout << "Board from " << (blackPerspective ? "Black" : "White") << " perspective:\n";
    outputBoard(board, blackPerspective, std::cout);

    // Write color and board to file
    std::ofstream outFile("necai.txt");
    if (outFile.is_open()) {
        outFile << colorOutput << "\n";
        outputBoard(board, blackPerspective, outFile);
        outFile.close();
    } else {
        std::cerr << "Error: Could not write to necai.txt\n";
    }

    return 0;
}