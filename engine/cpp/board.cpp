#include "board.h"
#include <sstream> 
#include <stdexcept> //for exceptions no assertion with cassert

//Time complexity of O(128) =~ O(1)
//Space Complexity of O(n) because of istringstream ss(fen) so I change to by passing reference for O(1) 

Board::Board() : white_turn(true), castle_wq(false), castle_wk(false), castle_bk(false), castle_bq(false), en_passant(-1){

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