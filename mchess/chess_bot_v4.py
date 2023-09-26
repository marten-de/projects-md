# updated to work with chess_v4, zobrist hashing moved to chess module, last pure python version

from collections import defaultdict
from circular_dict import CircularDict
import random
import time
import datetime
import os
import csv
import json

import sys # for performance analysis
import cProfile # for timing and performance optimization

import chess_v5 as my_chess


"""HELPER FUNCTIONS"""
# region

# translating uci move notation to our internal move notation
def uci2move(uci):

    from_sq_uci, to_sq_uci = uci[0:2], uci[2:]
    from_sq, to_sq = my_chess.cnote2tuple(from_sq_uci), my_chess.cnote2tuple(to_sq_uci)

    if len(uci) == 5: #promotion move
        promotion = uci[4]
        if to_sq[0] == 7: # white has promoted
            promotion = promo.upper()

        move = (from_sq[0],from_sq[1],to_sq[0],to_sq[1],my_chess.PIECE_INIT[promotion])
    
    else:
        move = (from_sq[0],from_sq[1],to_sq[0],to_sq[1],0)

    return move

# this function lets the bot try a list of puzzles and tracks its performance. so far we only use a small sample of puzzles from the lichess database
def test_puzzles():

    # preparing results
    results = {"correct_num": 0, "incorrect_num": 0, "correct_rating": [], "incorrect_rating": []}

    with open(PUZZLES_FILE) as in1:
        in1c = csv.DictReader(in1, delimiter=',')

        for row in in1c:
            fen = row['FEN']
            rating = int(row['Rating'])
            moves = row['Moves'].split()

            first_move = uci2move(moves[0])
            solution = uci2move(moves[1])
    
            b = my_chess.Board()
            b.load_FEN(fen)

            # the first move in the csv is the last opponents move, so it has to be played before we use the bot
            b.commit_move(first_move)

            bot = Chessbot(b)
            botmove = bot.search()

            if botmove == solution:
                results['correct_num'] += 1
                results['correct_rating'].append(rating)
            else:
                results['incorrect_num'] += 1
                results['incorrect_rating'].append(rating)

            avg_corr_rating = sum(results['correct_rating'])/len(results['correct_rating']) if len(results['correct_rating']) > 0 else 0
            avg_incorr_rating = sum(results['incorrect_rating'])/len(results['incorrect_rating']) if len(results['incorrect_rating']) > 0 else 0

            highest = max(results['correct_rating']) if results['correct_rating'] else 0
            lowest = min(results['incorrect_rating']) if results['incorrect_rating'] else 0

            # we print the results after each puzzle, because we might want to terminate the function early

            print(f"\ncorrect: {results['correct_num']}, incorrect: {results['incorrect_num']}")
            print(f"avg correct rating: {avg_corr_rating:.2f}, avg incorrect rating: {avg_incorr_rating:.2f}")
            print(f"highest solved: {highest}, lowest failed: {lowest}")

    return results

# endregion


"""CONSTANTS"""
# region

ABS_DIR_PATH = os.path.dirname(__file__)

PUZZLES_FILE = os.path.join(ABS_DIR_PATH, "testing/puzzles_sample.csv")

# reference to chess class constants
WHITE = my_chess.WHITE
BLACK = my_chess.BLACK
OPPOSITE = my_chess.OPPOSITE

NO_PIECE = my_chess.NO_PIECE
KING = my_chess.KING
PAWN = my_chess.PAWN
KNIGHT = my_chess.KNIGHT
BISHOP = my_chess.BISHOP
ROOK = my_chess.ROOK
QUEEN = my_chess.QUEEN

WKING = my_chess.WKING
WPAWN = my_chess.WPAWN
WKNIGHT = my_chess.WKNIGHT
WBISHOP = my_chess.WBISHOP
WROOK = my_chess.WROOK
WQUEEN = my_chess.WQUEEN
BKING = my_chess.BKING
BPAWN = my_chess.BPAWN
BKNIGHT = my_chess.BKNIGHT
BBISHOP = my_chess.BBISHOP
BROOK = my_chess.BROOK
BQUEEN = my_chess.BQUEEN

PIECE_SPLIT = my_chess.PIECE_SPLIT
YX2INT = my_chess.YX2INT
INT2YX = my_chess.INT2YX

# piece values for materialcount evaluation
PIECE_VALUES = {PAWN: 100,
            KNIGHT: 300,
            BISHOP: 300,
            ROOK: 500,
            QUEEN: 900,
            KING: 0} # the king doesnt influence material count, as both sides always have one

# initial values for alpha-beta-pruning search
ALPHA_INITIAL = -float('inf')
BETA_INITIAL = float('inf')

BOT_THINKING_TIME = 3

FORCE_KING_WEIGHT = 10

# bonus values for piece positions in the opening
OPENING_BONUS_VALUES = {WHITE: 
    {KNIGHT:
            [0,5,5,5,5,5,5,0,
            0,10,15,25,25,15,10,5,
            5,15,35,40,40,35,15,5,
            5,25,40,50,50,40,25,5,
            5,25,40,50,50,40,25,5,
            5,15,35,40,40,35,15,5,
            5,10,15,25,25,15,10,0,
            0,5,5,5,5,5,5,0],
    KING:
            [40,50,15,5,5,15,50,40,
            35,35,10,5,5,10,35,35,
            30,15,5,0,0,5,15,30,
            20,10,0,0,0,0,10,20,
            10,5,5,0,0,5,5,10,
            10,5,5,0,0,5,5,10,
            5,5,5,0,0,5,5,5,
            5,5,5,0,0,5,5,5],
    QUEEN:
            [0,10,10,25,25,10,10,0,
            10,40,40,40,40,40,40,10,
            10,40,50,50,50,50,40,10,
            25,40,50,50,50,50,40,25,
            25,40,50,50,50,50,40,25,
            10,40,50,50,50,50,40,10,
            10,40,40,40,40,40,40,10,
            0,10,10,25,25,10,10,0],
    BISHOP:
            [15,10,10,10,10,10,10,15,
            10,35,15,15,15,15,35,10,
            10,35,35,35,35,35,35,10,
            10,15,50,35,35,50,15,10,
            10,20,20,35,35,20,20,10,
            10,15,20,35,35,20,15,10,
            10,15,15,15,15,15,15,10,
            0,10,10,10,10,10,10,0],
    ROOK:
            [15,15,20,35,35,20,15,15,
            0,15,15,15,15,15,15,0,
            0,15,15,15,15,15,15,0,
            0,15,15,15,15,15,15,0,
            0,15,15,15,15,15,15,0,
            0,15,15,15,15,15,15,0,
            35,50,50,50,50,50,50,35,
            25,25,25,25,25,25,25,25],
    PAWN:
            [0,0,0,0,0,0,0,0,
            35,35,35,0,0,35,35,35,
            30,10,10,25,25,10,10,30,
            15,5,5,40,40,5,5,15,
            15,5,5,35,35,5,5,15,
            5,5,5,30,30,5,5,5,
            25,25,25,25,25,25,25,25,
            0,0,0,0,0,0,0,0]}}

# reversing the square bonuses for the black color
#OPENING_BONUS_VALUES[BLACK] = {key: [x[:] for x in value[::-1]] for key, value in OPENING_BONUS_VALUES[WHITE].items()}

OPENING_BONUS_VALUES[BLACK] = {}
for key, value in OPENING_BONUS_VALUES[WHITE].items():
    new_bonus = []
    for i in range(56,-1,-1):
        new_bonus.extend(value[i:i+8])

    OPENING_BONUS_VALUES[BLACK][key] = new_bonus

# how strong we consider the bonuses given in the according table
OPENING_BONUS_WEIGHT = 1

# only king and pawn get endgame bonuses, but we still fill the dict with all other pieces because it is easier and faster than to check for the piece type
ENDGAME_BONUS_VALUES = {WHITE: 
    {KING:
            [0,0,5,5,5,5,0,0,
            0,0,5,10,10,5,0,0,
            0,5,15,30,30,15,5,0,
            0,10,35,45,45,35,10,0,
            0,10,40,50,50,40,10,0,
            0,10,30,40,40,30,10,0,
            0,0,10,15,15,10,0,0,
            0,0,5,5,5,5,0,0],
    PAWN:
            [0,0,0,0,0,0,0,0,
            5,5,5,5,5,5,5,5,
            5,5,5,5,5,5,5,5,
            15,15,15,15,15,15,15,15,
            25,25,25,25,25,25,25,25,
            35,35,35,35,35,35,35,35,
            50,50,50,50,50,50,50,50,
            0,0,0,0,0,0,0,0],
    
    BISHOP: [0 for i in range(64)],
    KNIGHT: [0 for i in range(64)],
    ROOK: [0 for i in range(64)],
    QUEEN: [0 for i in range(64)]}}

# reversing the square bonuses for the black color
#ENDGAME_BONUS_VALUES[BLACK] = {key: [x[:] for x in value[::-1]] for key, value in ENDGAME_BONUS_VALUES[WHITE].items()}

ENDGAME_BONUS_VALUES[BLACK] = {}
for key, value in ENDGAME_BONUS_VALUES[WHITE].items():
    new_bonus = []
    for i in range(56,-1,-1):
        new_bonus.extend(value[i:i+8])

    ENDGAME_BONUS_VALUES[BLACK][key] = new_bonus

ENDGAME_BONUS_WEIGHT = 0.8

# at this materialcount will we start to consider that we are in the endgame, going linearly from 0 to 1, with 1 being reached at a materialcount of 0
ENDGAME_INDICATOR = 1200

# raw files paths for the openings. loading these files takes time, so it should not be done unless you want to update something in the openings or use a larger database etc.
OPENINGS_DATABASE_PATH = os.path.join(ABS_DIR_PATH, "rawdata/openings")
OPENINGS_DATABASE_FILES = [os.path.join(OPENINGS_DATABASE_PATH, "a.tsv"),os.path.join(OPENINGS_DATABASE_PATH, "b.tsv"),os.path.join(OPENINGS_DATABASE_PATH, "c.tsv"),os.path.join(OPENINGS_DATABASE_PATH, "d.tsv"),os.path.join(OPENINGS_DATABASE_PATH, "e.tsv")]

# using this json file for quick loading of openings
OPENINGS_DATABASE_JSON = os.path.join(ABS_DIR_PATH, "data/openings_database.json")

EXTENSION_LIMIT = 8

KILLER_BIAS = 500

# endregion


class Chessbot:

    # connecting the bot with a board and also setting bot parameters and variables
    def __init__(self, board, thinking_time=BOT_THINKING_TIME):
        
        self.thinking_time = datetime.timedelta(seconds=thinking_time)
        self.killer_moves = set()

        # preparing circular dict for transposition table
        self.transpositions = CircularDict(maxlen=0.5 * 10**6)

        # loading openings database
        self.load_openings_database()

        self.board = board

    # random (legal) move, just for testing the bot initially
    def random_move(self):
        if self.board.legal_moves():
            time.sleep(1)
            return random.choice(self.board.legal_moves())

    def load_openings_database(self):
        with open(OPENINGS_DATABASE_JSON) as json_file:
            temp_db = json.load(json_file)

        self.openings_database = {int(key): [tuple(m) for m in value] for key, value in temp_db.items()}

    # loading a selection of openings from several tsv files and converting them to internal move notation, saving as json. this function only needs to be run if you change the zobrist mask. otherwise, just loading in the already existing json file is of course much faster
    def create_openings_database(self):
        openings_database = defaultdict(list)

        for filename in OPENINGS_DATABASE_FILES:

            with open(filename) as in1:
                in1c = csv.DictReader(in1, delimiter='\t')

                for row in in1c:
                    # resetting to the starting position for each opening
                    self.board = my_chess.Board()
                    self.board.load_FEN(my_chess.FEN_START)
                    current_hash = self.board.zobr_hash

                    uci_moves = row['uci'].strip('\n').split()
                    for m in uci_moves:

                        # converting to our internal move notation
                        move = uci2move(m)

                        # appending the move to the current position as a possibility
                        openings_database[current_hash].append(move)

                        self.board.commit_move(move)
                        current_hash = self.board.zobr_hash


        # serializing json
        json_object = json.dumps(openings_database, indent=4)
        
        # writing to sample.json
        with open("new_openings_database.json", "w") as outfile:
            outfile.write(json_object)
        # clearing board variable just in case
        
        del self.board

    # the main search function wrapper. it iteratively increases the search depth, taking the best previously found move as the starting move for the next iteration. so far it will stop the iteration after the thinking time is reached, but will still complete the last search iteration. it would also be possible to abort the search, but that is more tricky and the bot is not that fast anyways, so we use this implementation for now
    def search(self):

        # if we are still in the opening, lets select a random valid bookmove from the opening database, if we find the current position in it
        if self.board.full_moves <= 15:
            current_hash = self.board.zobr_hash
            if current_hash in self.openings_database:
                bookmoves = self.openings_database[current_hash]
                return random.choice(bookmoves)

        # setting the stop mark
        stop = datetime.datetime.now() + self.thinking_time

        depth = 1
        prev_best_move = None
        while datetime.datetime.now() < stop:
            
            best_eval, best_move = self.recursive_search(depth, ALPHA_INITIAL, BETA_INITIAL, start_move=prev_best_move)
            
            # print debug info
            print(depth)
            print(best_eval)
            print(best_move)

            # starting with the best found move for the next iteration to maximize alpha-beta-pruning
            prev_best_move = best_move

            depth += 1
        
        # when we move on from this search, the killer moves storage needs to be cleared
        self.killer_moves.clear()
        return best_move

    # the core search function. it goes through every possible move combination up until the depth limit and uses alpha-beta-pruning to save time. this means, that once a move is found that is better for the opponent, than any move that was previously looked at, then we will not consider this move at all (prune it!) because it gives us a worse position.
    def recursive_search(self, depth, alpha, beta, start_move=None, ext_count=0):

        best_move = None
        current_hash = self.board.zobr_hash

        # early termination if the position was already evaluated
        if current_hash in self.transpositions:
            if self.transpositions[current_hash][0] >= depth:
                return self.transpositions[current_hash][1]

        # if we dont include this condition, the bot can repeat moves in a winning position until the game is drawn
        if self.board.gameover:
            if self.board.gameover[0] == 0.5:
                return (0, None)

        # upon reaching the depth limit, we start another search, that only looks at captures
        if depth == 0:
            return self.search_all_captures(alpha, beta)
        
        # if the move list is empty, that means it must be checkmate (if we also stand in check at the same time). we dont need to check for stalemate, as this is already covered by the gameover == 0.5 condition earlier
        moves = self.board.legal_moves()
        if not moves:
            if self.board.in_check:
                return (-(10**6+depth), None)
        
        # the moves are ordered from best to worse to take maximum advantage of the alpha-beta-pruning
        ordered_moves = self.order_moves(moves, start_move)

        # trying every move and then returning the inverse of the opponents evaluation (note that we also pass the inverse of alpha and beta in switched positions for that), then undoing the move
        for move in ordered_moves:
            self.board.commit_move(move)

            # certain move types are more promising than others and can warrant an extension of search depth
            extension = self.calculate_extension(move, ext_count)

            evaluation, _ = self.recursive_search(depth-1+extension, -beta, -alpha, ext_count=(ext_count+extension))
            evaluation = -evaluation
            self.board.undo_move(commited=True)

            # move was too good, opponent will avoid this position (alpha-beta-pruning)
            if evaluation >= beta:
                # adding this move to the killer move set, for later consideration
                self.killer_moves.add(move)
                return (beta, None)
        
            # move is better than previously found move
            if evaluation > alpha:
                alpha = evaluation
                best_move = move
            
        # storing the newly found evaluation and best move in the transposition table before returning
        self.transpositions[current_hash] = (depth,(alpha, best_move))
        return (alpha, best_move)

    # this search only considers capture moves. the rest of the functionality is identical to the search function, but notably this one doesnt have a depth limit and will continue until there are no more captures possible
    def search_all_captures(self, alpha, beta):

        # see if any good non-captures exist first, otherwise we might return a bad evaluation of a good position if only bad captures are available
        evaluation = self.rel_evaluate()
        if evaluation >= beta:
            return (beta, None)

        alpha = max(alpha, evaluation)

        capture_moves = self.board.legal_moves(onlycaptures=True)
        ordered_capture_moves = self.order_moves(capture_moves)

        for move in ordered_capture_moves:
            self.board.commit_move(move)
            evaluation, _ = self.search_all_captures(-beta, -alpha)
            evaluation = -evaluation
            self.board.undo_move(commited=True)

            if evaluation >= beta:
                self.killer_moves.add(move)
                return (beta, None)
            
            alpha = max(alpha, evaluation)

        return (alpha, None)

    # this function orders moves from best to worse and is a support function for our search. of course we dont know in advance how good a move is, so we need to guess.
    def order_moves(self, movelist, start_move=None):

        ordered_moves = []

        for move in movelist:
            y_from, x_from, y_to, x_to, prom = move

            move_score_guess = 0
            moved_piece_type = PIECE_SPLIT[self.board.board[YX2INT[(y_from,x_from)]]][1]
            captured_piece_type = PIECE_SPLIT[self.board.board[YX2INT[(y_to,x_to)]]][1]

            # capturing a high value piece with a low value piece is usually good
            if captured_piece_type != NO_PIECE:
                move_score_guess += PIECE_VALUES[captured_piece_type] - PIECE_VALUES[moved_piece_type]
            
            # promoting a pawn is usually also strong
            if prom != 0:
                move_score_guess += PIECE_VALUES[PIECE_SPLIT[prom][1]]
            
            # moving into opponents pawn capture range with a piece other than a pawn is often bad
            if YX2INT[(y_to, x_to)] in self.board.reachable[self.board.opponent]['pawn_attack']:
                move_score_guess -= PIECE_VALUES[moved_piece_type]

            # killer moves are potentially really strong moves, that might be playable, even if the position changed slightly. this means we should consider them with high priority in the search
            if move in self.killer_moves:
                move_score_guess += KILLER_BIAS

            ordered_moves.append((move_score_guess, move))
        
        ordered_moves.sort(reverse=True)
        
        # if a move is manually passed to the function, that means we want this exact move to be at the very start of the list
        if start_move:
            list1 = [x[1] for x in ordered_moves]
            list1.remove(start_move)
            return [start_move] + list1
        else:
            return [x[1] for x in ordered_moves]

    # we want to extend our search depth for promising moves. so far, checks and pawns that are about to promote are implemented. there is also a limit to how far these extensions can go.
    def calculate_extension(self, move, ext_count):

        from_y, from_x, to_y, _, _ = move

        moved_piece = PIECE_SPLIT[self.board.board[YX2INT[(from_y,from_x)]]][1]

        extension = 0
        if ext_count < EXTENSION_LIMIT:

            if self.board.in_check:
                extension = 1
            elif moved_piece == PAWN and (to_y == 6 or to_y == 1):
                extension = 1
            
        return extension

    # this function combines all evaluations such as materialcount and other bonuses into a final relative evaluation. that means, if the bot thinks its own side is winning, the evaluation will be positive. the reason is, it is easier to implement the search that way, and should we be interested in the "standard" way of evaluating (white is better -> positive, black is better -> negative), then we can give back the relative evaluation and factor in the played color
    def rel_evaluate(self):
        
        evaluation = self.materialcount() + self.king_to_corner_endgame() + self.opening_positioning() + self.endgame_positioning()

        return evaluation

    # counting the material according to the piece values. note that this count is relative (instead of based on the color), meaning if the player that is to move is leading in material, the count will come back positive
    def materialcount(self):
        sumown = sum([PIECE_VALUES[PIECE_SPLIT[self.board.board[sq]][1]] for sq in self.board.piece_loc[self.board.to_move]])
        sumopp = sum([PIECE_VALUES[PIECE_SPLIT[self.board.board[sq]][1]] for sq in self.board.piece_loc[self.board.opponent]])
        
        materialcount = (sumown - sumopp)

        # updating endgame weight. if the materialcount of the opponent is 12 or higher, it will be 0, but between 12 and 0 it will linearly go up to 1
        self.endgame_weight = 0 if 1 - (sumopp / ENDGAME_INDICATOR) < 0 else 1 - (sumopp / ENDGAME_INDICATOR)

        return materialcount

    # this function attempts to give bonus evaluation if the opponents king is forced towards the corner of the board in an endgame. the parameters are arbitrary and could probably be improved by extensive testing
    def king_to_corner_endgame(self):
        evaluation = 0

        oppo_rank, oppo_file = INT2YX[self.board.kings[self.board.opponent]]

        # the further the opponent is from the center, the higher the bonus evaluation gets
        oppo_dist_rank = max(3-oppo_rank,oppo_rank-4)
        oppo_dist_file = max(3-oppo_file,oppo_file-4)
        oppo_dist_center = oppo_dist_rank + oppo_dist_file
        evaluation += oppo_dist_center * 3
        
        own_rank, own_file = INT2YX[self.board.kings[self.board.to_move]]

        # we also assign a bonus if our own king is closer to the opponents king. the reason for this is, that in the endgame, the own king can greatly help to limit the opponents kings maneuverability
        dist_between_rank = abs(own_rank-oppo_rank)
        dist_between_file = abs(own_file-oppo_file)
        dist_between_kings = dist_between_rank + dist_between_file
        evaluation += 14 - dist_between_kings

        # the bonus evaluation gets weighted, if we are not in the endgame yet (based on opponents materialcount), the bonus will be zero
        return evaluation * FORCE_KING_WEIGHT * self.endgame_weight

    # evaluating bonus values for how the pieces are positioned on the board in the opening stage (until midgame). once the endgame is reached, these bonuses will become zero
    def opening_positioning(self):
        sumown = sum([OPENING_BONUS_VALUES[self.board.to_move][PIECE_SPLIT[self.board.board[sq]][1]][sq] for sq in self.board.piece_loc[self.board.to_move]])
        sumopp = sum([OPENING_BONUS_VALUES[self.board.opponent][PIECE_SPLIT[self.board.board[sq]][1]][sq] for sq in self.board.piece_loc[self.board.opponent]])
        
        opening_bonus = (sumown - sumopp)

        return opening_bonus * OPENING_BONUS_WEIGHT * (1 - self.endgame_weight)

    # evaluating bonus values for how the pieces are positioned on the board in the endgame stage. if we are not in the endgame yet, the bonuses will be zero
    def endgame_positioning(self):
        sumown = sum([ENDGAME_BONUS_VALUES[self.board.to_move][PIECE_SPLIT[self.board.board[sq]][1]][sq] for sq in self.board.piece_loc[self.board.to_move]])
        sumopp = sum([ENDGAME_BONUS_VALUES[self.board.opponent][PIECE_SPLIT[self.board.board[sq]][1]][sq] for sq in self.board.piece_loc[self.board.opponent]])
        
        endgame_bonus = (sumown - sumopp)

        return endgame_bonus * ENDGAME_BONUS_WEIGHT * self.endgame_weight


if __name__ == "__main__":
    
    cProfile.run('test_puzzles()')
