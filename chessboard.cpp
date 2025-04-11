
// This file has a purpose of mapping the chessboard to a 2d array.
// INPUT: By default: w, but if the user switches, then b
// OUTPUT: what colour NECAI is playing as w or b

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

// Function to print the board (White or Black perspective)
void printBoard(const Board& board, bool blackPerspective = false) {
    if (blackPerspective) {
        for (int rank = 0; rank < 8; rank++) { // Start from rank 1 (a1-h1)
            std::cout << (8 - rank) << " "; // Print rank 8 to 1
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
                std::cout << c << " ";
            }
            std::cout << "\n";
        }
        std::cout << "  h g f e d c b a\n"; // Files reversed
    } else {
        for (int rank = 7; rank >= 0; rank--) { // Start from rank 8 to 1
            std::cout << (rank + 1) << " "; // Print rank number
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
                std::cout << c << " ";
            }
            std::cout << "\n";
        }
        std::cout << "  a b c d e f g h\n";
    }
}
/*
// Move structure
struct Move {
    int from;
    int to;
};

// Generate pawn moves for a given square
std::vector<Move> getPawnMoves(const Board& board, int pos) {
    std::vector<Move> moves;
    if (board[pos].piece != PAWN) return moves;
    int dir = (board[pos].color == WHITE ? 8 : -8); // White up, Black down
    int to = pos + dir;
    // Check if target square is on board and empty
    if (to >= 0 && to < 64 && board[to].piece == EMPTY) {
        moves.push_back({pos, to});
    }
    return moves;
}

// Simple evaluation function (material count)
int evaluate(const Board& board) {
    int score = 0;
    for (int i = 0; i < 64; i++) {
        if (board[i].piece == EMPTY) continue;
        int value = (board[i].piece == PAWN ? 1 :
                     board[i].piece == KNIGHT ? 3 :
                     board[i].piece == BISHOP ? 3 :
                     board[i].piece == ROOK ? 5 :
                     board[i].piece == QUEEN ? 9 : 0);
        score += (board[i].color == WHITE ? value : -value); // White +, Black -
    }
    return score;
}


// Minimax algorithm for AI thinking
int minimax(Board& board, int depth, bool maximizingPlayer, Color aiColor) {
    if (depth == 0) return evaluate(board);
    std::vector<Move> moves;
    // Generate moves for current player
    Color currentColor = maximizingPlayer ? aiColor : (aiColor == WHITE ? BLACK : WHITE);
    for (int i = 0; i < 64; i++) {
        if (board[i].piece != EMPTY && board[i].color == currentColor) {
            auto pieceMoves = getPawnMoves(board, i); // Add other pieces later
            moves.insert(moves.end(), pieceMoves.begin(), pieceMoves.end());
        }
    }
    if (moves.empty()) return evaluate(board); // No moves, evaluate position
    if (maximizingPlayer) {
        int maxScore = -10000;
        for (const Move& m : moves) {
            Square temp = board[m.to];
            board[m.to] = board[m.from];
            board[m.from] = {EMPTY, WHITE};
            maxScore = std::max(maxScore, minimax(board, depth - 1, false, aiColor));
            board[m.from] = board[m.to];
            board[m.to] = temp;
        }
        return maxScore;
    } else {
        int minScore = 10000;
        for (const Move& m : moves) {
            Square temp = board[m.to];
            board[m.to] = board[m.from];
            board[m.from] = {EMPTY, WHITE};
            minScore = std::min(minScore, minimax(board, depth - 1, true, aiColor));
            board[m.from] = board[m.to];
            board[m.to] = temp;
        }
        return minScore;
    }
}

// Find the best move for the AI
Move findBestMove(Board& board, Color aiColor) {
    std::vector<Move> moves;
    for (int i = 0; i < 64; i++) {
        if (board[i].piece != EMPTY && board[i].color == aiColor) {
            auto pieceMoves = getPawnMoves(board, i);
            moves.insert(moves.end(), pieceMoves.begin(), pieceMoves.end());
        }
    }
    if (moves.empty()) return {-1, -1}; // No valid moves
    Move bestMove = moves[0];
    int bestScore = (aiColor == WHITE ? -10000 : 10000);
    for (const Move& m : moves) {
        Square temp = board[m.to];
        board[m.to] = board[m.from];
        board[m.from] = {EMPTY, WHITE};
        int score = minimax(board, 2, aiColor == WHITE ? false : true, aiColor);
        board[m.from] = board[m.to];
        board[m.to] = temp;
        if (aiColor == WHITE) {
            if (score > bestScore) {
                bestScore = score;
                bestMove = m;
            }
        } else {
            if (score < bestScore) {
                bestScore = score;
                bestMove = m;
            }
        }
    }
    return bestMove;
}
*/

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

    // Print board based on perspective
    std::cout << "Board from " << (blackPerspective ? "Black" : "White") << " perspective:\n";
    printBoard(board, blackPerspective);

    // Write color to file
    std::ofstream outFile("necai_color.txt");
    if (outFile.is_open()) {
        outFile << colorOutput;
        outFile.close();
    } else {
        std::cerr << "Error: Could not write to necai_color.txt\n";
    }
/*
    // Find and display AI's best move
    std::cout << "\nNECAI is thinking...\n";
    Move bestMove = findBestMove(board, aiColor);
    if (bestMove.from != -1) {
        std::cout << "Best move: from " << (char)('a' + (bestMove.from % 8))
                  << (bestMove.from / 8 + 1) << " to " << (char)('a' + (bestMove.to % 8))
                  << (bestMove.to / 8 + 1) << "\n";
    } else {
        std::cout << "No valid moves found.\n";
    }
*/
    return 0;
}