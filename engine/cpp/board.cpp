#include "board.h"
#include <sstream> 
#include <stdexcept> //for exceptions no assertion with cassert

//Time complexity of O(128) =~ O(1)
//Space Complexity of O(n) because of istringstream ss(fen) so I change to by passing reference for O(1) 

Board::Board() : white_turn(true), castle_wq(false), castle_wk(false), castle_bk(false), castle_bq(false), en_passant(-1), halfmove(0), fullmove(1){

    squares.fill(EMPTY);

}

/**
 * 
 * Example of input:
 * 
 * rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
 * 
 * [BLACK PIECES]/[BLACK PAWNS]/[EMPTY]/[EMPTY]/[EMPTY]/[EMPTY]/[WHITE PAWNS]/[WHITE PIECES] [who's turn] [Rights to castle and which side] [En passant squares allowance?] [LAST PAWN MOVE] [FULL MOVE]
 * 
 * Details: 
 * 
 * lowercase is for black pieces
 * uppercase is for white pieces
 * 
 * [LAST PAWN MOVE] is used for the 50-move rule
 * 0 means something just happened (pawn move or capture)
 * 
 * [FULLMOVE number] tracks which move number the game is on. kinda useless
 * Move 1 = White plays + Black plays
 * Move 2 = next pair of moves
 * and so on and so on 
 * 
 */
void Board::load_fen(const std::string& fen){

    // Exceptions 

    if(fen.empty()) throw std::invalid_argument("String FEN cannot be empty");

    std::istringstream ss(fen);
    std::string section[6];

    int count = 0;
    //ss is going to read one word until it hits a space
    while (count < 6 && ss >> section[count]) count++;
    if(count != 6) throw std::invalid_argument("FEN must have exactly 6 parts"); 
    if (section[1] != "w" && section[1] != "b") throw std::invalid_argument("FEN turn must be w or b");
    for (char c : section[2]) {
        if (section[2] != "-" && c != 'K' && c != 'Q' && c != 'k' && c != 'q')
            throw std::invalid_argument("FEN castling rights invalid");
    }
    if (section[3] != "-") {
        if (section[3].length() != 2)
            throw std::invalid_argument("FEN en passant invalid");
        if (section[3][0] < 'a' || section[3][0] > 'h')
            throw std::invalid_argument("FEN en passant file invalid");
        if (section[3][1] != '3' && section[3][1] != '6')
            throw std::invalid_argument("FEN en passant rank invalid");
    }
    if (std::stoi(section[4]) < 0)
        throw std::invalid_argument("FEN halfmove cannot be negative");
    if (std::stoi(section[5]) < 1)
        throw std::invalid_argument("FEN fullmove must be at least 1");

    //Exception ending

    parse_pieces(section[0]);
    parse_turn(section[1]); 
    parse_castling(section[2]); 
    parse_en_passant(section[3]); 
    parse_halfmove(section[4]);
    parse_fullmove(section[5]); 
    checkRep(); 
}
bool Board::is_white_turn(){

    return white_turn; 

}

Piece Board::get_piece(int index) const{

    return static_cast<Piece>(squares[index]);
    //static_cast converts a type to another at compile time

}

int Board::get_en_passant() const{

    return en_passant;

}

void Board::parse_pieces(const std::string& board_part){

    int index = 0; 

    for(char c : board_part){

        if(c == '/'){} //new line 
        
        else if(c >= '1' && c <= '8'){ //if they are numbers then it means that it's empty square/space
            index += c - '0'; 
        }
        else{ //it has to be a piece
            switch(c){
                case 'P': squares[index] = WHITE_PAWN; break; 
                case 'N': squares[index] = WHITE_KNIGHT; break;
                case 'B': squares[index] = WHITE_BISHOP; break;
                case 'R': squares[index] = WHITE_ROOK; break;
                case 'Q': squares[index] = WHITE_QUEEN; break;
                case 'K': squares[index] = WHITE_KING; break;
                case 'p': squares[index] = BLACK_PAWN; break;
                case 'n': squares[index] = BLACK_KNIGHT; break;
                case 'b': squares[index] = BLACK_BISHOP; break;
                case 'r': squares[index] = BLACK_ROOK; break;
                case 'q': squares[index] = BLACK_QUEEN; break;
                case 'k': squares[index] = BLACK_KING; break;
            }
            index++; 
        }
    }
}
void Board::parse_turn(const std::string& turn_part){

    white_turn = (turn_part == "w"); 
}
void Board::parse_castling(const std::string& castle_part){

    //rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
    //find lookup is O(1) 
    //npos means not found or no matches

    castle_wk = (castle_part.find('K') != std::string::npos);
    castle_wq = (castle_part.find('Q') != std::string::npos);
    castle_bk = (castle_part.find('k') != std::string::npos);
    castle_bq = (castle_part.find('q') != std::string::npos);

}
void Board::parse_en_passant(const std::string& ep_part){

    //ep_part is a future potential move that one can take
    // var en_passant tells the engine what is the possible move in board metrics

    /** 
     * file: a=0, b=1, c=2, d=3, e=4, f=5, g=6, h=7
     * rank: 8=0, 7=1, 6=2, 5=3, 4=4, 3=5, 2=6, 1=7
     */

     /**
      * Chess:          Array index:
      * Rank 8 ──→      0  1  2  3  4  5  6  7
      * Rank 7 ──→      8  9  10 11 12 13 14 15
      * Rank 6 ──→      16 17 18 19 20 21 22 23
      * Rank 5 ──→      24 25 26 27 28 29 30 31
      * Rank 4 ──→      32 33 34 35 36 37 38 39
      * Rank 3 ──→      40 41 42 43 44 45 46 47
      * Rank 2 ──→      48 49 50 51 52 53 54 55
      * Rank 1 ──→      56 57 58 59 60 61 62 63
      *                  a  b  c  d  e  f  g  h

      * where white is rank 1 and 2 at the beginning
      * black is rank 7-8 at the beginning
      */

    if(ep_part == "-") en_passant = -1;
    else{
        int file = ep_part[0] - 'a'; 
        int rank = 8 - (ep_part[1] - '0'); 
        en_passant = rank * 8 + file; // after we can just do modulo 8 = rank and do division which the remainder = file 
    }

}
void Board::parse_halfmove(const std::string& hm_part){

    halfmove = std::stoi(hm_part);

}

void Board::parse_fullmove(const std::string& fm_part){

    fullmove = std::stoi(fm_part); 

}

void Board::checkRep(){ //always need the prefix to include member func of Board

    int num_king_white = 0; 
    int num_king_black = 0; 

    for(auto i = 0; i < 64; i++){
        if(squares[i] == WHITE_KING) num_king_white++; 
        if(squares[i] == BLACK_KING) num_king_black++; 
    }
    if (num_king_white != 1) throw std::invalid_argument("Board must have exactly one white king");
    if (num_king_black != 1) throw std::invalid_argument("Board must have exactly one black king");

    for (auto index = 0; index < 8; index++) {
        if (squares[index] == WHITE_PAWN || squares[index] == BLACK_PAWN) throw std::invalid_argument("No pawns allowed on rank 8");
        if (squares[56 + index] == WHITE_PAWN || squares[56 + index] == BLACK_PAWN) throw std::invalid_argument("No pawns allowed on rank 1");
    }
    if (en_passant != -1) {
        int rank = en_passant / 8;
        if (rank != 2 && rank != 5) throw std::invalid_argument("En passant square on invalid rank");
    }

    if (halfmove < 0) throw std::invalid_argument("Halfmove cannot be negative");
    if (fullmove < 1) throw std::invalid_argument("Fullmove must be at least 1");

    for (int i = 0; i < 64; i++) {
        if (squares[i] < EMPTY || squares[i] > BLACK_KING) throw std::invalid_argument("Invalid piece value on board");
    }

}

void Board::make_move(const Move& move){

    history[history_size++] = {en_passant, castle_wk, castle_wq, castle_bk, castle_bq, halfmove};
    Piece piece = squares[move.from];
    if (move.is_en_passant) {
        int captured_pawn = move.to + (white_turn ? +8 : -8);
        squares[captured_pawn] = EMPTY;
    }
    if (move.is_castling) {
        if (move.to == 62) { squares[63] = EMPTY; squares[61] = WHITE_ROOK; }
        if (move.to == 58) { squares[56] = EMPTY; squares[59] = WHITE_ROOK; }
        if (move.to == 6) { squares[7] = EMPTY; squares[5] = BLACK_ROOK; }
        if (move.to == 2) { squares[0] = EMPTY; squares[3] = BLACK_ROOK; }
    }
    squares[move.to] = (move.promotion != EMPTY) ? move.promotion : piece;
    squares[move.from] = EMPTY;

    bool is_double_push = (piece == WHITE_PAWN || piece == BLACK_PAWN) && abs(move.to - move.from) == 16;
    en_passant = is_double_push ? (move.from + move.to) / 2 : -1;

    //we need to update castling rights
    if (piece == WHITE_KING) { castle_wk = false; castle_wq = false; }
    if (piece == BLACK_KING) { castle_bk = false; castle_bq = false; }
    if (move.from == 63 || move.to == 63) castle_wk = false;
    if (move.from == 56 || move.to == 56) castle_wq = false;
    if (move.from == 7 || move.to == 7 ) castle_bk = false;
    if (move.from == 0 || move.to == 0 ) castle_bq = false;

    //update the halfmove clock
    bool is_capture  = move.captured != EMPTY;
    bool is_pawn_move = (piece == WHITE_PAWN || piece == BLACK_PAWN);
    halfmove = (is_capture || is_pawn_move) ? 0 : halfmove + 1;

    if (!white_turn) fullmove++;
    //update the turn
    white_turn = !white_turn;
}

void Board::unmake_move(const Move& move){

    BoardState prev = history[--history_size]; //removes last element

    //set as prev
    en_passant = prev.en_passant; 
    castle_wk = prev.castle_wk;
    castle_wq = prev.castle_wq;
    castle_bk = prev.castle_bk;
    castle_bq = prev.castle_bq;
    halfmove = prev.halfmove;

    white_turn = !white_turn;

    Piece piece = squares[move.to];
    if (move.promotion != EMPTY) piece = white_turn ? WHITE_PAWN : BLACK_PAWN;
    squares[move.from] = piece;
    // restore captured piece (EMPTY if none)
    squares[move.to] = move.captured;  
    //we undo the en_passant
    if (move.is_en_passant) {
        squares[move.to] = EMPTY;
        int captured_pawn = move.to + (white_turn ? +8 : -8);
        squares[captured_pawn] = white_turn ? BLACK_PAWN : WHITE_PAWN;
    }
    //undo the castling
    if (move.is_castling) {
        if (move.to == 62) { squares[61] = EMPTY; squares[63] = WHITE_ROOK; }
        if (move.to == 58) { squares[59] = EMPTY; squares[56] = WHITE_ROOK; }
        if (move.to == 6) { squares[5] = EMPTY; squares[7] = BLACK_ROOK; }
        if (move.to == 2) { squares[3] = EMPTY; squares[0] = BLACK_ROOK; }
    }
    if (!white_turn) fullmove--;
}

bool Board::get_castling_wk() const { //const means it's only reading, not writing
    return castle_wk; 
}
bool Board::get_castling_wq() const {
    return castle_wq; 
}
bool Board::get_castling_bk() const {
    return castle_bk;  
}
bool Board::get_castling_bq() const {
    return castle_bq;
}

bool Board::is_in_check(bool is_white) const{

    Piece my_king = is_white ? WHITE_KING : BLACK_KING; 
    Piece enemy_rook = is_white ? BLACK_ROOK : WHITE_ROOK;
    Piece enemy_queen = is_white ? BLACK_QUEEN : WHITE_QUEEN;
    Piece enemy_bishop = is_white ? BLACK_BISHOP : WHITE_BISHOP;
    Piece enemy_knight = is_white ? BLACK_KNIGHT : WHITE_KNIGHT;
    Piece enemy_pawn = is_white ? BLACK_PAWN : WHITE_PAWN;
    Piece enemy_king = is_white ? BLACK_KING : WHITE_KING;

    int king_square = -1;

    for (int i = 0; i < 64; i++) {
        if (squares[i] == my_king) {
            king_square = i;
            break;
        }
    }

    //check various attack from enemy 
    for (int dir : {1, -1, 8, -8}) {
        int sq = king_square + dir;
        while (sq >= 0 && sq < 64) {
            if (dir == 1 || dir == -1) {
                if (abs(sq % 8 - (sq - dir) % 8) != 1) break;
            }
            Piece p = squares[sq];
            if (p == enemy_rook || p == enemy_queen) return true;
            if (p != EMPTY) break;
            sq += dir;
        }
    }

    for (int dir : {7, -7, 9, -9}) {
        int sq = king_square + dir;
        while (sq >= 0 && sq < 64) {
            if (abs(sq % 8 - (sq - dir) % 8) != 1) break;
            Piece p = squares[sq];
            if (p == enemy_bishop || p == enemy_queen) return true;
            if (p != EMPTY) break;
            sq += dir;
        }
    }

    for (int dir : {-17, -15, -10, -6, 17, 15, 10, 6}) {
        int sq = king_square + dir;
        if (sq >= 0 && sq < 64) {
            if (abs(sq % 8 - king_square % 8) == 1 || abs(sq % 8 - king_square % 8) == 2) {
                if (squares[sq] == enemy_knight) return true;
            }
        }
    }

    int pawn_dir = is_white ? -8 : 8;
    for (int dir : {pawn_dir - 1, pawn_dir + 1}) {
        int sq = king_square + dir;
        if (sq >= 0 && sq < 64) {
            if (abs(sq % 8 - king_square % 8) == 1) {
                if (squares[sq] == enemy_pawn) return true;
            }
        }
    }

    for (int dir : {1, -1, 8, -8, 7, -7, 9, -9}) {
        int sq = king_square + dir;
        if (sq >= 0 && sq < 64) {
            if (dir != 8 && dir != -8) {
                if (abs(sq % 8 - king_square % 8) != 1) continue;
            }
            if (squares[sq] == enemy_king) return true;
        }
    }

    return false;

}