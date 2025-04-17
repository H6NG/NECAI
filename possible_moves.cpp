// This file has a purpose of providing a function to get all possible moves for a given piece on the chessboard.
// JUST POSSIBLE MOVES REGARDLESS OF WHO'S PLAYING - you call possible_moves.cpp when NECAI is playing 

#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <sstream>

struct Position {
    int row, col; // Row (0-7, 8 to 1), Col (0-7, h to a in necai.txt)
};

// Piece struct to store type and color
struct Piece {
    char symbol; // e.g., 'P', 'p', 'N', 'n'
    Position pos; // Board position
    bool is_white; // True if white, false if black
};

// Move struct to store source and destination
struct Move {
    Position from, to;
    std::string notation; // Algebraic notation (e.g., "e2e4", "Nf3")
};

// Convert necai.txt column (h=0, a=7) to standard (a=0, h=7)
int necai_col_to_std(int col) {
    return 7 - col;
}

// Convert row (0-based, 8 at top) to standard (1-based, 1 at bottom)
int row_to_std(int row) {
    return 8 - row;
}

// Convert standard column (0=a) to algebraic (a-h)
char col_to_file(int col) {
    return 'a' + col;
}

// Generate algebraic notation for a move
std::string move_to_notation(const Move& move, char piece, bool is_capture, const std::vector<Piece>& pieces) {
    std::string notation;
    int from_col = necai_col_to_std(move.from.col);
    int to_col = necai_col_to_std(move.to.col);
    int from_row = row_to_std(move.from.row);
    int to_row = row_to_std(move.to.row);

    // For non-pawns, include piece letter (e.g., N for knight)
    if (piece != 'P' && piece != 'p') {
        notation += toupper(piece);
    }

    // Check for ambiguity (same piece type can move to same square)
    bool ambiguous_file = false, ambiguous_row = false;
    for (const auto& p : pieces) {
        if (p.symbol == piece && (p.pos.row != move.from.row || p.pos.col != move.from.col)) {
            // Check if this piece could move to the same destination
            // Simplified: just check if it's the same piece type
            if (p.pos.row == move.from.row) ambiguous_row = true;
            if (p.pos.col == move.from.col) ambiguous_file = true;
        }
    }

    // Include file or rank if ambiguous
    if (piece != 'P' && piece != 'p') {
        if (ambiguous_file || ambiguous_row) {
            notation += col_to_file(from_col);
            if (ambiguous_row) {
                notation += std::to_string(from_row);
            }
        }
    } else {
        // For pawns, include file only on capture
        if (is_capture) {
            notation += col_to_file(from_col);
        }
    }

    // Add capture symbol
    if (is_capture) {
        notation += 'x';
    }

    // Add destination square
    notation += col_to_file(to_col);
    notation += std::to_string(to_row);

    return notation;
}

// Check if position is within board
bool is_valid_pos(int row, int col) {
    return row >= 0 && row < 8 && col >= 0 && col < 8;
}

// Check if target square is empty or capturable
bool can_occupy(int row, int col, const char board[8][8], bool is_white) {
    if (!is_valid_pos(row, col)) return false;
    if (board[row][col] == '.') return true;
    bool target_is_white = isupper(board[row][col]);
    return target_is_white != is_white; // Can capture opponent's piece
}

// Generate pawn moves
void generate_pawn_moves(const Piece& piece, const char board[8][8], std::vector<Move>& moves, const std::vector<Piece>& pieces) {
    Position from = piece.pos;
    int dir = piece.is_white ? -1 : 1; // White moves up (-1), Black down (+1)
    int start_row = piece.is_white ? 6 : 1; // 2nd rank for white (6), 7th for black (1)

    // Single push
    int new_row = from.row + dir;
    if (is_valid_pos(new_row, from.col) && board[new_row][from.col] == '.') {
        Move move = {from, {new_row, from.col}, ""};
        move.notation = move_to_notation(move, piece.symbol, false, pieces);
        moves.push_back(move);

        // Double push from starting rank
        if (from.row == start_row) {
            new_row = from.row + 2 * dir;
            if (board[new_row][from.col] == '.' && board[from.row + dir][from.col] == '.') {
                Move double_move = {from, {new_row, from.col}, ""};
                double_move.notation = move_to_notation(double_move, piece.symbol, false, pieces);
                moves.push_back(double_move);
            }
        }
    }

    // Captures
    int capture_cols[2] = {from.col - 1, from.col + 1};
    for (int col : capture_cols) {
        if (is_valid_pos(new_row, col) && board[new_row][col] != '.' && can_occupy(new_row, col, board, piece.is_white)) {
            Move capture = {from, {new_row, col}, ""};
            capture.notation = move_to_notation(capture, piece.symbol, true, pieces);
            moves.push_back(capture);
        }
    }

    // Note: En passant requires game history (previous move). Omitted for simplicity.
}

// Generate knight moves
void generate_knight_moves(const Piece& piece, const char board[8][8], std::vector<Move>& moves, const std::vector<Piece>& pieces) {
    Position from = piece.pos;
    int offsets[8][2] = {
        {-2, -1}, {-2, 1}, {-1, -2}, {-1, 2},
        {1, -2}, {1, 2}, {2, -1}, {2, 1}
    };

    for (const auto& offset : offsets) {
        int new_row = from.row + offset[0];
        int new_col = from.col + offset[1];
        if (can_occupy(new_row, new_col, board, piece.is_white)) {
            Move move = {from, {new_row, new_col}, ""};
            bool is_capture = board[new_row][new_col] != '.';
            move.notation = move_to_notation(move, piece.symbol, is_capture, pieces);
            moves.push_back(move);
        }
    }
}

// Generate sliding moves (bishop, rook, queen)
void generate_sliding_moves(const Piece& piece, const char board[8][8], std::vector<Move>& moves, const std::vector<Piece>& pieces, bool diagonal, bool straight) {
    Position from = piece.pos;
    int directions[8][2] = {
        {-1, -1}, {-1, 1}, {1, -1}, {1, 1}, // Diagonals
        {-1, 0}, {1, 0}, {0, -1}, {0, 1}   // Straights
    };
    int start = diagonal ? 0 : 4;
    int end = straight ? 8 : 4;

    for (int i = start; i < end; ++i) {
        int row = from.row;
        int col = from.col;
        while (true) {
            row += directions[i][0];
            col += directions[i][1];
            if (!is_valid_pos(row, col)) break;
            if (can_occupy(row, col, board, piece.is_white)) {
                Move move = {from, {row, col}, ""};
                bool is_capture = board[row][col] != '.';
                move.notation = move_to_notation(move, piece.symbol, is_capture, pieces);
                moves.push_back(move);
                if (board[row][col] != '.') break; // Stop after capture
            } else {
                break; // Blocked by own piece
            }
        }
    }
}

// Generate king moves
void generate_king_moves(const Piece& piece, const char board[8][8], std::vector<Move>& moves, const std::vector<Piece>& pieces) {
    Position from = piece.pos;
    int offsets[8][2] = {
        {-1, -1}, {-1, 0}, {-1, 1},
        {0, -1},           {0, 1},
        {1, -1}, {1, 0}, {1, 1}
    };

    for (const auto& offset : offsets) {
        int new_row = from.row + offset[0];
        int new_col = from.col + offset[1];
        if (can_occupy(new_row, new_col, board, piece.is_white)) {
            Move move = {from, {new_row, new_col}, ""};
            bool is_capture = board[new_row][new_col] != '.';
            move.notation = move_to_notation(move, piece.symbol, is_capture, pieces);
            moves.push_back(move);
        }
    }

    // Note: Castling requires checking king/rook movement history and squares. Omitted for simplicity.
}

// Generate moves for a piece
std::vector<Move> generate_moves(const Piece& piece, const char board[8][8], const std::vector<Piece>& pieces) {
    std::vector<Move> moves;
    char type = toupper(piece.symbol);
    switch (type) {
        case 'P':
            generate_pawn_moves(piece, board, moves, pieces);
            break;
        case 'N':
            generate_knight_moves(piece, board, moves, pieces);
            break;
        case 'B':
            generate_sliding_moves(piece, board, moves, pieces, true, false);
            break;
        case 'R':
            generate_sliding_moves(piece, board, moves, pieces, false, true);
            break;
        case 'Q':
            generate_sliding_moves(piece, board, moves, pieces, true, true);
            break;
        case 'K':
            generate_king_moves(piece, board, moves, pieces);
            break;
    }
    return moves;
}

int main() {
    std::ifstream file("necai.txt");
    if (!file.is_open()) {
        std::cerr << "Error: Could not open necai.txt\n";
        return 1;
    }

    std::string line;
    std::getline(file, line); // Read color
    bool necai_is_white = (line == "w");

    // Read board
    char board[8][8];
    std::vector<Piece> necai_pieces;
    for (int row = 0; row < 8; ++row) {
        std::getline(file, line);
        std::istringstream iss(line);
        std::string token;
        int col = 0;
        while (iss >> token && col < 8) {
            board[row][col] = token[0];
            if (board[row][col] != '.') {
                bool is_white = isupper(board[row][col]);
                if (is_white == necai_is_white) {
                    necai_pieces.push_back({board[row][col], {row, col}, is_white});
                }
            }
            ++col;
        }
    }
    file.close();

    // Generate and print moves for each piece
    for (const auto& piece : necai_pieces) {
        std::vector<Move> moves = generate_moves(piece, board, necai_pieces);
        if (!moves.empty()) {
            int std_col = necai_col_to_std(piece.pos.col);
            int std_row = row_to_std(piece.pos.row);
            std::cout << "Piece " << piece.symbol << " at " << col_to_file(std_col) << std_row << " can move to:\n";
            for (const auto& move : moves) {
                std::cout << "  " << move.notation << "\n";
            }
        }
    }

    return 0;
}