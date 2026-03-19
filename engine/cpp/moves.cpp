#include "moves.h"
#include <vector>

MoveGenerator::MoveGenerator(Board& board) : board(board){}

std::vector<Move> MoveGenerator::generate_moves(){

    std::vector<Move> moves; 
    generate_pawn_moves(moves);
    generate_knight_moves(moves);
    generate_bishop_moves(moves);
    generate_rook_moves(moves);
    generate_queen_moves(moves);
    generate_king_moves(moves);
    return moves;

}

void MoveGenerator::generate_pawn_moves(std::vector<Move>& moves){

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

    bool is_white = board.is_white_turn(); 
    int direction = (is_white ? -8 : +8);
    Piece my_pawn = is_white ? WHITE_PAWN : BLACK_PAWN; 
    for(auto i = 0; i < 64; i++){

        if(board.get_piece(i) != my_pawn) continue; 
        int from = i; 
        int to = i + direction; 

        //Possibility 1: pawn moves forward one square
        //Possibility 2: pawn moves forward two squares from starting rank
        //Possibility 3: Diagonal Captures
        //Possibility 4: Promotion then 4 new promotions are possible with diagonal captures or moving forward
        //Possibility 5: En-passant
        
        if (to >= 0 && to < 64 && board.get_piece(to) == EMPTY) {
            if (to < 8 || to > 55) {
                moves.push_back(Move(from, to, EMPTY, is_white ? WHITE_QUEEN : BLACK_QUEEN));
                moves.push_back(Move(from, to, EMPTY, is_white ? WHITE_ROOK : BLACK_ROOK));
                moves.push_back(Move(from, to, EMPTY, is_white ? WHITE_BISHOP : BLACK_BISHOP));
                moves.push_back(Move(from, to, EMPTY, is_white ? WHITE_KNIGHT : BLACK_KNIGHT));
            } else {
                moves.push_back(Move(from, to));
            }
            int start_rank_min = is_white ? 48 : 8;
            int start_rank_max = is_white ? 55 : 15;
            int two_forward = i + 2 * direction;
            if (i >= start_rank_min && i <= start_rank_max && board.get_piece(two_forward) == EMPTY) {
                moves.push_back(Move(from, two_forward));
            }
        }
        int capture_left  = i + direction - 1;
        int capture_right = i + direction + 1;

        for (int capture : {capture_left, capture_right}) {
            if (capture < 0 || capture >= 64) continue;

            Piece target = board.get_piece(capture);

            if (target != EMPTY && is_white != (target < BLACK_PAWN)) {
                if (capture < 8 || capture > 55) {
                    
                    moves.push_back(Move(from, capture, target, is_white ? WHITE_QUEEN  : BLACK_QUEEN));
                    moves.push_back(Move(from, capture, target, is_white ? WHITE_ROOK   : BLACK_ROOK));
                    moves.push_back(Move(from, capture, target, is_white ? WHITE_BISHOP : BLACK_BISHOP));
                    moves.push_back(Move(from, capture, target, is_white ? WHITE_KNIGHT : BLACK_KNIGHT));
                } else {
                    moves.push_back(Move(from, capture, target));
                }
            }
            if (capture == board.get_en_passant()) {
                moves.push_back(Move(from, capture, is_white ? BLACK_PAWN : WHITE_PAWN, EMPTY, true));
            }
        }
    }

}
void MoveGenerator::generate_bishop_moves(std::vector<Move>& moves){

}
void MoveGenerator::generate_rook_moves(std::vector<Move>& moves){

}
void MoveGenerator::generate_knight_moves(std::vector<Move>& moves){

}
void MoveGenerator::generate_queen_moves(std::vector<Move>& moves){

}
void MoveGenerator::generate_king_moves(std::vector<Move>& moves){

}