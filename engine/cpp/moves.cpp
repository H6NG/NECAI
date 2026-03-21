#include "moves.h"
#include <vector>

MoveGenerator::MoveGenerator(Board& board) : board(board){}

std::vector<Move> MoveGenerator::generate_moves(){

    std::vector<Move> moves; 
    generate_legal_moves(moves);
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
        int curr_file = i % 8;
        int capture_left  = (curr_file > 0) ? i + direction - 1 : -1;
        int capture_right = (curr_file < 7) ? i + direction + 1 : -1;

        for (int capture : {capture_left, capture_right}) {
            if (capture < 0 || capture >= 64) continue;

            Piece target = board.get_piece(capture);

            if (target != EMPTY && is_white != (target < BLACK_PAWN)) {
                if (capture < 8 || capture > 55) {
                    moves.push_back(Move(from, capture, target, is_white ? WHITE_QUEEN : BLACK_QUEEN));
                    moves.push_back(Move(from, capture, target, is_white ? WHITE_ROOK : BLACK_ROOK));
                    moves.push_back(Move(from, capture, target, is_white ? WHITE_BISHOP : BLACK_BISHOP));
                    moves.push_back(Move(from, capture, target, is_white ? WHITE_KNIGHT : BLACK_KNIGHT));
                } else {
                    moves.push_back(Move(from, capture, target));
                }
            }
            else if (capture == board.get_en_passant()) {
                moves.push_back(Move(from, capture, is_white ? BLACK_PAWN : WHITE_PAWN, EMPTY, true));
            }
        }
    }

}
void MoveGenerator::generate_bishop_moves(std::vector<Move>& moves){

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
    //top_boundary is from 0 to 7. 
    //bottom_boundary is from 56 to 63.
    //it is not blocked by anything, it can capture any pieces except the king and your own pieces
    bool is_white = board.is_white_turn();
    Piece my_bishop = is_white ? WHITE_BISHOP : BLACK_BISHOP;
    int directions[4] = {-9, -7, +7, +9};

    for(auto i = 0; i < 64; i++) {

        if (board.get_piece(i) != my_bishop) continue;
        int from = i;

        for (int dir : directions) {
            int sq = from + dir;

            while (sq >= 0 && sq < 64) {

                int prev_file = (sq - dir) % 8;
                int curr_file = sq % 8;
                if (abs(curr_file - prev_file) != 1) break;

                Piece target = board.get_piece(sq);

                if (target == EMPTY) {
                    moves.push_back(Move(from, sq));

                } else {
                    bool is_enemy = is_white ? (target >= BLACK_PAWN) : (target < BLACK_PAWN && target != EMPTY);
                    if (is_enemy) {
                        moves.push_back(Move(from, sq, target));
                    }
                    break;
                }
                sq += dir;
            }
        }
    }

}
void MoveGenerator::generate_rook_moves(std::vector<Move>& moves){

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
    Piece my_rook = is_white ? WHITE_ROOK : BLACK_ROOK;
    int direction[4] = {1, -1, +8, -8}; 

    for(auto i = 0; i < 64; i++){

        if(board.get_piece(i) != my_rook) continue; 
        int from = i; 

        for(int dir : direction){

            int potential_move = i + dir;
            
            while (potential_move >= 0 && potential_move < 64) {

                if (dir == 1 || dir == -1) {
                    int prev_file = (potential_move - dir) % 8;
                    int curr_file = potential_move % 8;
                    if (abs(curr_file - prev_file) != 1) break;
                }

                Piece target = board.get_piece(potential_move);

                if (target == EMPTY) {
                    moves.push_back(Move(from, potential_move));

                } else {
                    bool is_enemy = is_white ? (target >= BLACK_PAWN) : (target < BLACK_PAWN && target != EMPTY);
                    if (is_enemy) {
                        moves.push_back(Move(from, potential_move, target));
                    }
                    break;
                }
                potential_move += dir;
            }
        }
    }
}
void MoveGenerator::generate_knight_moves(std::vector<Move>& moves){

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
      * 
      * it is a combination of bishop and rook moves.
      */
     
    bool is_white = board.is_white_turn(); 
    Piece my_knight = is_white ? WHITE_KNIGHT : BLACK_KNIGHT; 
    int direction[8] = {-17, -15, -10, -6, +17, +15, +10, +6};

    for(auto i = 0; i < 64; i++){
        if(board.get_piece(i) != my_knight) continue; 
        int from = i; 

        for(int dir : direction){

            int potential_move = i + dir;
            
            if (potential_move >= 0 && potential_move < 64) {

                int prev_file = (potential_move - dir) % 8;
                int curr_file = potential_move % 8;
                if (abs(curr_file - prev_file) != 1 && abs(curr_file - prev_file) != 2) continue;

                Piece target = board.get_piece(potential_move);

                if (target == EMPTY) {
                    moves.push_back(Move(from, potential_move));

                } else {
                    bool is_enemy = is_white ? (target >= BLACK_PAWN) : (target < BLACK_PAWN && target != EMPTY);
                    if (is_enemy) {
                        moves.push_back(Move(from, potential_move, target));
                    }
                }
            }
        }
    }
}
void MoveGenerator::generate_queen_moves(std::vector<Move>& moves){

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
      * 
      * it is a combination of bishop and rook moves.
      */

    bool is_white = board.is_white_turn();
    Piece my_queen = is_white ? WHITE_QUEEN : BLACK_QUEEN;
    int direction[8] = {1, -1, +8, -8, -9, -7, +7, +9}; 

    for(auto i = 0; i < 64; i++){

        if(board.get_piece(i) != my_queen) continue; 
        int from = i; 

        for(int dir : direction){

            int potential_move = i + dir;
            
            while (potential_move >= 0 && potential_move < 64) {

                if (dir != 8 && dir != -8) {
                    int prev_file = (potential_move - dir) % 8;
                    int curr_file = potential_move % 8;
                    if (abs(curr_file - prev_file) != 1) break;
                }

                Piece target = board.get_piece(potential_move);

                if (target == EMPTY) {
                    moves.push_back(Move(from, potential_move));

                } else {
                    bool is_enemy = is_white ? (target >= BLACK_PAWN) : (target < BLACK_PAWN && target != EMPTY);
                    if (is_enemy) {
                        moves.push_back(Move(from, potential_move, target));
                    }
                    break;
                }
                potential_move += dir;
            }
        }
    }
}
void MoveGenerator::generate_king_moves(std::vector<Move>& moves){

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
      * 
      * it is a combination of bishop and rook moves.
      */

    bool is_white = board.is_white_turn(); 
    Piece my_king = is_white ? WHITE_KING : BLACK_KING; 
    int direction[8] = {-1, +1, -8, +8, -9, +7, +9, -7}; 

    for(auto i = 0; i < 64; i++){

        if(board.get_piece(i) != my_king) continue; 
        int from = i; 

        for(int dir : direction){

            int potential_move = i + dir;
            
            if (potential_move >= 0 && potential_move < 64) {

                if (dir != 8 && dir != -8) {
                    int prev_file = (potential_move - dir) % 8;
                    int curr_file = potential_move % 8;
                    if (abs(curr_file - prev_file) != 1) continue;
                }

                Piece target = board.get_piece(potential_move);

                if (target == EMPTY) {
                    moves.push_back(Move(from, potential_move));

                } else {
                    bool is_enemy = is_white ? (target >= BLACK_PAWN) : (target < BLACK_PAWN && target != EMPTY);
                    if (is_enemy) {
                        moves.push_back(Move(from, potential_move, target));
                    }
                }
                potential_move += dir;
            }
        }
    }
}
void MoveGenerator::generate_castling_moves(std::vector<Move>& moves){
    if (board.is_white_turn()) {
        if (board.get_castling_wk()) {
            if (board.get_piece(61) == EMPTY && board.get_piece(62) == EMPTY) {
                moves.push_back(Move(60, 62, EMPTY, EMPTY, false, true));
            }
        }
        if (board.get_castling_wq()) {
            if (board.get_piece(57) == EMPTY && board.get_piece(58) == EMPTY && board.get_piece(59) == EMPTY) {
                moves.push_back(Move(60, 58, EMPTY, EMPTY, false, true));
            }
        }
    }
    else{

        if (board.get_castling_bk()) {
            if (board.get_piece(5) == EMPTY && board.get_piece(6) == EMPTY) {
                moves.push_back(Move(4, 6, EMPTY, EMPTY, false, true));
            }
        }
        
        if (board.get_castling_bq()) {
            if (board.get_piece(1) == EMPTY && board.get_piece(2) == EMPTY && board.get_piece(3) == EMPTY) {
                moves.push_back(Move(4, 2, EMPTY, EMPTY, false, true));
            }
        }
    }
}

void MoveGenerator::generate_legal_moves(std::vector<Move>& moves){
    std::vector<Move> pseudo_legal;
    
    generate_pawn_moves(pseudo_legal);
    generate_rook_moves(pseudo_legal);
    generate_bishop_moves(pseudo_legal);
    generate_queen_moves(pseudo_legal);
    generate_king_moves(pseudo_legal);
    generate_knight_moves(pseudo_legal);
    generate_castling_moves(pseudo_legal);

    for (auto& move : pseudo_legal) {
    board.make_move(move);
    if (!board.is_in_check(!board.is_white_turn())) {
        moves.push_back(move);
    }
    board.unmake_move(move);
}
}