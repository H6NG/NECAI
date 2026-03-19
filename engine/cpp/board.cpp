#include "board.h"
#include <sstream> 

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
 * [LAST PAWN MOVE] is used for the 50-move rule
 * 0 means something just happened (pawn move or capture)
 * 
 * [FULLMOVE number] tracks which move number the game is on. kinda useless
 * Move 1 = White plays + Black plays
 * Move 2 = next pair of moves
 * and so on and so on 
 * 
 */
void Board::load_fen(std::string fen){

    std::istringstream ss(fen);
    std::string section[8];

    //ss is going to read one word until it hits a space
    for(auto i = 0; i < 6; i++) ss >> section[i];
    parse_pieces(section[0]);
    parse_castling(section[1]); 
    parse_turn(section[2]); 
    parse_en_passant(section[3]); 
    parse_halfmove(section[4]);
    parse_fullmove(section[5]); 
}
bool Board::is_white_turn(){

}

void Board::parse_pieces(std::string board_part){

}
void Board::parse_turn(std::string turn_part){

}
void Board::parse_castling(std::string castle_part){

}
void Board::parse_en_passant(std::string ep_part){

}
void Board::parse_halfmove(std::string hm_part){

}

void Board::parse_fullmove(std::string fm_part){

}