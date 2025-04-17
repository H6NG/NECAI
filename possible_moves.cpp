// This file has a purpose of providing a function to get all possible moves for a given piece on the chessboard.
// JUST POSSIBLE MOVES REGARDLESS OF WHO'S PLAYING - you call possible_moves.cpp when NECAI is playing 

#include <iostream>
#include <fstream>
#include <string>
#include <vector>

class ChessBoard {
public:
    char board[8][8]; // 8x8 board

    ChessBoard() {
        // Initialize empty board
        for (int i = 0; i < 8; i++) {
            for (int j = 0; j < 8; j++) {
                board[i][j] = '.';
            }
        }
    }

    // Load board from necai.txt
    bool loadFromFile(const std::string& filename) {
        std::ifstream file(filename);
        if (!file.is_open()) {
            std::cerr << "Error opening file: " << filename << std::endl;
            return false;
        }

        std::string line;
        std::getline(file, line); // Read turn ('w')
        std::vector<std::string> board_lines;
        while (std::getline(file, line)) {
            if (line.empty() || line[0] == ' ') continue;
            board_lines.push_back(line);
        }

        // Parse board
        for (int i = 0; i < 8; i++) {
            std::string row = board_lines[i];
            int col = 0;
            for (char c : row.substr(2)) {
                if (c == ' ') continue;
                board[7 - i][col] = c;
                col++;
            }
        }

        file.close();
        return true;
    }

    // Print board
    void printBoard() {
        for (int i = 7; i >= 0; i--) {
            std::cout << (i + 1) << " ";
            for (int j = 0; j < 8; j++) {
                std::cout << board[i][j] << " ";
            }
            std::cout << std::endl;
        }
        std::cout << "  h g f e d c b a" << std::endl;
    }
};


//---------------------OK-----------------------//


struct Move {
    int fromRow, fromCol, toRow, toCol;
    Move(int fr, int fc, int tr, int tc) : fromRow(fr), fromCol(fc), toRow(tr), toCol(tc) {}
};

class ChessEngine {
    ChessBoard& board; // Reference to ChessBoard
public:
    ChessEngine(ChessBoard& b) : board(b) {}

    // Convert move to algebraic notation (e.g., e2e4)
    std::string toChessNotation(const Move& move) {
        std::string notation;
        notation += char('a' + (7 - move.fromCol)); // h=0 -> a, a=7 -> h
        notation += char('1' + move.fromRow);       // row 0 -> 1
        notation += char('a' + (7 - move.toCol));
        notation += char('1' + move.toRow);
        return notation;
    }

    // Generate White pawn moves
    void generateWhitePawnMoves(std::vector<Move>& moves) {
        for (int col = 0; col < 8; col++) {
            if (board.board[1][col] == 'p') { // White pawns on rank 2
                // Single push (e.g., e2-e3)
                if (board.board[2][col] == '.') {
                    moves.emplace_back(1, col, 2, col);
                }
                // Double push (e.g., e2-e4)
                if (board.board[2][col] == '.' && board.board[3][col] == '.') {
                    moves.emplace_back(1, col, 3, col);
                }
            }
        }
    }

    // Generate White knight moves
    void generateWhiteKnightMoves(std::vector<Move>& moves) {
        // Possible knight move offsets: L-shape (2,1) or (1,2)
        int offsets[8][2] = { {2,1}, {2,-1}, {-2,1}, {-2,-1}, {1,2}, {1,-2}, {-1,2}, {-1,-2} };
        // Check knights at b1 (row 0, col 6) and g1 (row 0, col 1)
        std::vector<std::pair<int, int>> knightPos = { {0, 6}, {0, 1} }; // b1, g1
        for (const auto& pos : knightPos) {
            int row = pos.first, col = pos.second;
            if (board.board[row][col] == 'n') { // White knight
                for (const auto& offset : offsets) {
                    int newRow = row + offset[0];
                    int newCol = col + offset[1];
                    if (newRow >= 0 && newRow < 8 && newCol >= 0 && newCol < 8) {
                        // Allow move if square is empty or has Black piece
                        if (board.board[newRow][newCol] == '.' ||
                            board.board[newRow][newCol] == 'P' || board.board[newRow][newCol] == 'R' ||
                            board.board[newRow][newCol] == 'N' || board.board[newRow][newCol] == 'B' ||
                            board.board[newRow][newCol] == 'Q' || board.board[newRow][newCol] == 'K') {
                            moves.emplace_back(row, col, newRow, newCol);
                        }
                    }
                }
            }
        }
    }

    // Generate all White moves
    std::vector<Move> generateAllWhiteMoves() {
        std::vector<Move> moves;
        generateWhitePawnMoves(moves);
        generateWhiteKnightMoves(moves);
        return moves;
    }
};

int main() {
    ChessBoard board;
    if (!board.loadFromFile("necai.txt")) {
        return 1;
    }

    // Display the board
    std::cout << "Chessboard from necai.txt:\n";
    board.printBoard();

    // Generate and display all White moves
    ChessEngine engine(board);
    std::vector<Move> moves = engine.generateAllWhiteMoves();
    std::cout << "\nAll possible moves for White:\n";
    for (const Move& move : moves) {
        std::cout << engine.toChessNotation(move) << std::endl;
    }
    std::cout << "Total moves: " << moves.size() << std::endl;

    return 0;
}
