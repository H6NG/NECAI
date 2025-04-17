//NECAI thinking...

#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cstdlib>
#include <ctime>

// Convert row (0-7) and col (0-7) to algebraic notation (e.g., row=6, col=4 -> "e2")
std::string to_algebraic(int row, int col) {
    std::string move;
    move += static_cast<char>(col + 'a');
    move += static_cast<char>(7 - row + '1');
    return move;
}

// Add a move (from_row, from_col to to_row, to_col) to the moves list
void add_move(int from_row, int from_col, int to_row, int to_col, std::vector<std::string>& moves) {
    if (to_row >= 0 && to_row < 8 && to_col >= 0 && to_col < 8) {
        std::string move = to_algebraic(from_row, from_col) + to_algebraic(to_row, to_col);
        moves.push_back(move);
    }
}

// Generate pawn moves (simplified for White; Black would reverse direction)
void pawn_moves(int row, int col, char board[8][8], bool is_white, std::vector<std::string>& moves) {
    int dir = is_white ? -1 : 1; // White moves up (row decreases), Black moves down
    int start_row = is_white ? 6 : 1; // Starting row for double moves

    // Forward move (1 square)
    int to_row = row + dir;
    if (to_row >= 0 && to_row < 8 && board[to_row][col] == '.') {
        add_move(row, col, to_row, col, moves);
        // Double move from starting position
        if (row == start_row && board[to_row][col] == '.' && board[to_row + dir][col] == '.') {
            add_move(row, col, to_row + dir, col, moves);
        }
    }

    // Captures
    for (int dc : {-1, 1}) {
        int to_col = col + dc;
        if (to_row >= 0 && to_row < 8 && to_col >= 0 && to_col < 8 && board[to_row][to_col] != '.') {
            // Check if the target is an enemy piece
            if (is_white && board[to_row][to_col] >= 'a' && board[to_row][to_col] <= 'z') {
                add_move(row, col, to_row, to_col, moves);
            } else if (!is_white && board[to_row][to_col] >= 'A' && board[to_row][to_col] <= 'Z') {
                add_move(row, col, to_row, to_col, moves);
            }
        }
    }
}

// Generate knight moves
void knight_moves(int row, int col, char board[8][8], bool is_white, std::vector<std::string>& moves) {
    const std::vector<std::pair<int, int>> offsets = {
        {-2, -1}, {-2, 1}, {-1, -2}, {-1, 2},
        {1, -2}, {1, 2}, {2, -1}, {2, 1}
    };

    for (const auto& offset : offsets) {
        int to_row = row + offset.first;
        int to_col = col + offset.second;
        if (to_row >= 0 && to_row < 8 && to_col >= 0 && to_col < 8) {
            // Empty square or enemy piece
            if (board[to_row][to_col] == '.' ||
                (is_white && board[to_row][to_col] >= 'a' && board[to_row][to_col] <= 'z') ||
                (!is_white && board[to_row][to_col] >= 'A' && board[to_row][to_col] <= 'Z')) {
                add_move(row, col, to_row, to_col, moves);
            }
        }
    }
}

// Generate all moves for the current player
std::vector<std::string> generate_moves(char board[8][8], bool is_white) {
    std::vector<std::string> moves;
    for (int row = 0; row < 8; ++row) {
        for (int col = 0; col < 8; ++col) {
            char piece = board[row][col];
            // Check if the piece belongs to the current player
            if (is_white && piece >= 'A' && piece <= 'Z') {
                if (piece == 'P') pawn_moves(row, col, board, is_white, moves);
                else if (piece == 'N') knight_moves(row, col, board, is_white, moves);
                // Add other pieces (B, R, Q, K) here
            } else if (!is_white && piece >= 'a' && piece <= 'z') {
                if (piece == 'p') pawn_moves(row, col, board, is_white, moves);
                else if (piece == 'n') knight_moves(row, col, board, is_white, moves);
                // Add other pieces (b, r, q, k) here
            }
        }
    }
    return moves;
}

int main() {
    // Seed random number generator
    std::srand(static_cast<unsigned>(std::time(nullptr)));

    // Read necai.txt
    std::ifstream file("necai.txt");
    if (!file.is_open()) {
        std::cerr << "Error: Could not open necai.txt" << std::endl;
        return 1;
    }

    std::string color;
    std::getline(file, color); // Read "w" or "b"
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

    // Generate moves
    auto moves = generate_moves(board, is_white);
    if (moves.empty()) {
        std::cerr << "Error: No possible moves found" << std::endl;
        return 1;
    }

    // Select a random move
    std::string chosen_move = moves[std::rand() % moves.size()];

    // Write to updatecb.cpp
    std::ofstream out_file("updatecb.cpp");
    if (!out_file.is_open()) {
        std::cerr << "Error: Could not open updatecb.cpp" << std::endl;
        return 1;
    }
    out_file << "#include <string>\n\n";
    out_file << "const std::string chosen_move = \"" << chosen_move << "\";\n";
    out_file.close();

    // Optional: Print chosen move for verification
    std::cout << "Chosen move: " << chosen_move << "\n";
    std::cout << "Written to updatecb.cpp\n";

    return 0;
}