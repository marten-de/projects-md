# tweaked version that changes internal board (2d->1d), move (mixed->5-tuple) and piece (class->int) mechanics to be more compatible with planned C extension
# includes zobrist hash functionality, which was moved from bot module to here for potentially faster calculation
# this is the last "standalone"/ pure python version, the next versions will include C extensions

from collections import defaultdict
import json
import os
import random

# functions written in C
from chess_extension import check_possible_king_capt
from chess_extension import update_reachable
from chess_extension import pseudo_legal_moves

import cProfile # for timing and performance optimization

import chess # only for debugging


"""HELPER FUNCTIONS""" 
# region

# this helper function translates a chess notation (e.g. d4) to our internal board notation tuple (y,x)
def cnote2tuple(cnote):
    char, digit = cnote[0], cnote[1]
    y = int(digit) - 1
    x = "abcdefgh".index(char)
    return (y,x)

# converting a move of our own chess game to the uci notation used by python chess module
def move2uci(move):

    fy,fx,ty,tx,prom = move

    c_convert = "abcdefgh"
    uci_c_from, uci_c_to = c_convert[fx], c_convert[tx]
    uci_d_from, uci_d_to = fy+1, ty+1

    uci = [uci_c_from, str(uci_d_from), uci_c_to, str(uci_d_to)]

    # special case promotion, when our move tuple has a third component
    if prom != 0:
        uci.append(PIECE_PROMOTION[prom].lower())
    
    return "".join(uci)

# this function runs tests on pre-defined and known positions to see if our created board class works correctly. it is mainly an extension to the already existing Board.find_variations_compare, but allows to test multiple positions. i use it to test the class after each major change in the code
def test_module():
    # opening test file
    with open(TEST_POSITIONS_FILE) as json_file:
        tests = json.load(json_file)

    for test in tests:
        # preparing the test input
        debug_fen = test['fen']
        depth = test['depth']
        print(f"nodes should be: {test['nodes']}")
        
        # setting up the Board class
        b = Board()
        b.load_FEN(debug_fen)
        
        # setting up the benchmark
        c = chess.Board(debug_fen)

        # running the test and printing the result
        print(b.find_variations_compare(depth, c))

# endregion


"""CONSTANTS"""
# region

ABS_DIR_PATH = os.path.dirname(__file__)

TEST_POSITIONS_FILE = os.path.join(ABS_DIR_PATH, "testing/debug_positions.json")

ZOBRIST_FILE = os.path.join(ABS_DIR_PATH, "data/zobrist_mask.json")

# mapping of rank/file to internal board square number
YX2INT = {(0, 0): 0, (0, 1): 1, (0, 2): 2, (0, 3): 3, (0, 4): 4, (0, 5): 5, (0, 6): 6, (0, 7): 7, (1, 0): 8, (1, 1): 9, (1, 2): 10, (1, 3): 11, (1, 4): 12, (1, 5): 13, (1, 6): 14, (1, 7): 15, (2, 0): 16, (2, 1): 17, (2, 2): 18, (2, 3): 19, (2, 4): 20, (2, 5): 21, (2, 6): 22, (2, 7): 23, (3, 0): 24, (3, 1): 25, (3, 2): 26, (3, 3): 27, (3, 4): 28, (3, 5): 29, (3, 6): 30, (3, 7): 31, (4, 0): 32, (4, 1): 33, (4, 2): 34, (4, 3): 35, (4, 4): 36, (4, 5): 37, (4, 6): 38, (4, 7): 39, (5, 0): 40, (5, 1): 41, (5, 2): 42, (5, 3): 43, (5, 4): 44, (5, 5): 45, (5, 6): 46, (5, 7): 47, (6, 0): 48, (6, 1): 49, (6, 2): 50, (6, 3): 51, (6, 4): 52, (6, 5): 53, (6, 6): 54, (6, 7): 55, (7, 0): 56, (7, 1): 57, (7, 2): 58, (7, 3): 59, (7, 4): 60, (7, 5): 61, (7, 6): 62, (7, 7): 63}

# opposite mapping of board square to rank/file
INT2YX = {value: key for key, value in YX2INT.items()}

FEN_START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# pieces and colors have an integer assigned to speed up comparison processes. the combination of color+piece is uniquely identifiable
WHITE = 8
BLACK = 16
OPPOSITE = {WHITE: BLACK, BLACK: WHITE}

NO_PIECE = 0
KING = 1
PAWN = 2
KNIGHT = 3
BISHOP = 4
ROOK = 5
QUEEN = 6

# explicitly generating constants for all combinations to avoid multiple additions
WKING = WHITE+KING
WPAWN = WHITE+PAWN
WKNIGHT = WHITE+KNIGHT
WBISHOP = WHITE+BISHOP
WROOK = WHITE+ROOK
WQUEEN = WHITE+QUEEN
BKING = BLACK+KING
BPAWN = BLACK+PAWN
BKNIGHT = BLACK+KNIGHT
BBISHOP = BLACK+BISHOP
BROOK = BLACK+ROOK
BQUEEN = BLACK+QUEEN

# this dict is used to lookup piece generation for the Piece class
PIECE_INIT = {"K": WKING, "k": BKING, "Q": WQUEEN, "q": BQUEEN, "B": WBISHOP, "b": BBISHOP, "N": WKNIGHT, "n": BKNIGHT, "P": WPAWN, "p": BPAWN, "R": WROOK, "r": BROOK}

# faster lookup of color and piece type for python code, will be solved differently in C
PIECE_SPLIT = {WKING: (WHITE,KING), BKING: (BLACK,KING), WQUEEN: (WHITE,QUEEN), BQUEEN: (BLACK,QUEEN), WBISHOP: (WHITE,BISHOP), BBISHOP: (BLACK,BISHOP), WKNIGHT: (WHITE,KNIGHT), BKNIGHT: (BLACK, KNIGHT), WPAWN: (WHITE,PAWN), BPAWN: (BLACK,PAWN),WROOK: (WHITE,ROOK), BROOK: (BLACK,ROOK), NO_PIECE: (0,0)}

# the str equivalent of pieces in the Piece class
PIECE_STR = {value: key for key, value in PIECE_INIT.items()}
PIECE_STR[0] = "."

PIECE_PROMOTION = {WQUEEN: "Q", BQUEEN: "q", WROOK: "R", BROOK: "r", WBISHOP: "B", BBISHOP: "b", WKNIGHT: "N", BKNIGHT: "n"}

PIECE_MOVEMENT_PATTERNS = {
    ROOK: [[(1,0),(2,0),(3,0),(4,0),(5,0),(6,0),(7,0)],[(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7)],[(-1,0),(-2,0),(-3,0),(-4,0),(-5,0),(-6,0),(-7,0)],[(0,-1),(0,-2),(0,-3),(0,-4),(0,-5),(0,-6),(0,-7)]],
    BISHOP: [[(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7)],[(-1,-1),(-2,-2),(-3,-3),(-4,-4),(-5,-5),(-6,-6),(-7,-7)],[(1,-1),(2,-2),(3,-3),(4,-4),(5,-5),(6,-6),(7,-7)],[(-1,1),(-2,2),(-3,3),(-4,4),(-5,5),(-6,6),(-7,7)]],
    QUEEN: [[(1,0),(2,0),(3,0),(4,0),(5,0),(6,0),(7,0)],[(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7)],[(-1,0),(-2,0),(-3,0),(-4,0),(-5,0),(-6,0),(-7,0)],[(0,-1),(0,-2),(0,-3),(0,-4),(0,-5),(0,-6),(0,-7)],[(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7)],[(-1,-1),(-2,-2),(-3,-3),(-4,-4),(-5,-5),(-6,-6),(-7,-7)],[(1,-1),(2,-2),(3,-3),(4,-4),(5,-5),(6,-6),(7,-7)],[(-1,1),(-2,2),(-3,3),(-4,4),(-5,5),(-6,6),(-7,7)]],
    KING: [[(1,1)],[(0,1)],[(-1,1)],[(-1,0)],[(-1,-1)],[(0,-1)],[(1,-1)],[(1,0)]],
    KNIGHT: [[(2,1)],[(1,2)],[(-1,2)],[(-2,1)],[(-2,-1)],[(-1,-2)],[(1,-2)],[(2,-1)]],
    PAWN: {"move": [[(1,0)]], "double_move": [[(2,0)]], "capture": [[(1,-1)],[(1,1)]]}}

# lookup for everything related to the special move castle
CASTLE = {
    "empty": {WKING: [5,6], WQUEEN: [1,2,3],
            BKING: [61,62], BQUEEN: [57,58,59]},
    "kingmove": {WKING: (0,4,0,6,0), WQUEEN: (0,4,0,2,0),
            BKING: (7,4,7,6,0), BQUEEN: (7,4,7,2,0)},
    "rookmove": {(0,4,0,6,0): (0,7,0,5,0), (0,4,0,2,0): (0,0,0,3,0),
            (7,4,7,6,0): (7,7,7,5,0), (7,4,7,2,0): (7,0,7,3,0)},
    "check": {(0,4,0,6,0): [4,5,6], (0,4,0,2,0): [4,3,2],
            (7,4,7,6,0): [60,61,62], (7,4,7,2,0): [60,59,58]},
    "update": {(0,4,0,6,0): [4,5,6,7], (0,4,0,2,0): [4,3,2,0],
            (7,4,7,6,0): [60,61,62,63], (7,4,7,2,0): [60,59,58,56]},
    "rights": {0: WQUEEN, 7: WKING, 56: BQUEEN, 63: BKING}}

# lookup to handle everything related to special move promotion
PROMOTE = {
    "rank": {WHITE: 7, BLACK: 0},
    "options": {WHITE: [WQUEEN,WROOK,WBISHOP,WKNIGHT], BLACK: [BQUEEN,BROOK,BBISHOP,BKNIGHT]}}

# lookup for everything related to the special move en passant
EN_PASSANT = {WHITE: {"to_rank": 3, "from_rank": 1, "target": 2}, BLACK: {"to_rank": 4, "from_rank": 6, "target": 5}}

# the following dict keys will be used a lot for the undo_move functionality, and to speed it up slightly, we assign integer values
BOARD = 30
KINGS = 31
IN_CHECK = 32
THREEFOLD = 33
PIECE_LOC = 34
REACHABLE = 35
EN_PASSANT_TARGET = 36
HALF_MOVES = 37
FULL_MOVES = 38
CASTLING_RIGHTS = 39
GAMEOVER = 40
LAST_MOVE = 41
ADD = 42
REMOVE = 43
SUBTRACT = 44
REPLACE = 45
ZOBR_HASH = 46

# mapping the key string (which are needed for debugging) to the according integers
CHANGES_KEYS = {"board": BOARD, "kings": KINGS, "in_check": IN_CHECK, "threefold": THREEFOLD, "piece_loc": PIECE_LOC, "reachable": REACHABLE, "en_passant_target": EN_PASSANT_TARGET, "half_moves": HALF_MOVES, "full_moves": FULL_MOVES, "castling_rights": CASTLING_RIGHTS, "gameover": GAMEOVER, "last_move": LAST_MOVE, "add": ADD, "remove": REMOVE, "subtract": SUBTRACT, "replace": REPLACE, "zobr_hash": ZOBR_HASH}

# endregion


class Board:

    # note that some instance variables are initialized later, in their according functions
    def __init__(self):
        self.empty_board()
        self.kings = {}
        self.in_check = False
        self.threefold = defaultdict(int)
        self.piece_loc = {WHITE: set(), BLACK: set()}
        self.changes = [{}]
        self.reachable = {WHITE: {"all_direct": set(), "king_indirect_blocked": set()},
                        BLACK: {"all_direct": set(), "king_indirect_blocked": set()}}

        self.init_zobrist()

    # sets up a 1d-array with 0 as default to represent an empty field. this was changed from a previous 2d array. to interact with C, 1d arrays are much more suitable (at least in my opinion), and we can easily translate between the coordinate form (y,x) and the int form of a square with the according const dicts
    def empty_board(self):
        self.board = [0 for i in range(64)]

    # setting up a new game from the standard chess starting position
    def new_game(self):
        self.load_FEN(FEN_START)

    # loads in a standardized FEN string and sets up the board accordingly
    def load_FEN(self, fen):
        self.gameover = None

        # reset the board first
        self.empty_board()
        # split the FEN in its 6 components
        fen_fields = fen.split()
        
        # assigning global game variables
        self.to_move = WHITE if fen_fields[1] == "w" else BLACK
        self.opponent = OPPOSITE[self.to_move]

        self.castling_rights = {WHITE: [], BLACK: []}
        for c in fen_fields[2]:
            if c == "-":
                break
            if c.isupper():
                self.castling_rights[WHITE].append(PIECE_INIT[c])
            else:
                self.castling_rights[BLACK].append(PIECE_INIT[c])

        # making sure to only using int for this field, for compatibility with C
        self.en_passant_target = YX2INT[cnote2tuple(fen_fields[3])] if fen_fields[3] != "-" else -1
        self.half_moves = int(fen_fields[4])
        self.full_moves = int(fen_fields[5])
        
        # going through the main part of the FEN to assign the pieces to their respective fields
        sfen = fen_fields[0].split('/')[::-1]
        for y in range(8):
            x = 0
            for c in sfen[y]:
                if c.isalpha():
                    sq = YX2INT[(y,x)]
                    self.board[sq] = PIECE_INIT[c]
                    color = PIECE_SPLIT[self.board[sq]][0]
                    self.piece_loc[color].add(sq)
                    if c == "k":
                        self.kings[BLACK] = sq
                    if c == "K":
                        self.kings[WHITE] = sq
                    x += 1
                else:
                    x += int(c)

        # update reachable, only needed for the current opponent
        # C ext
        self.reachable[OPPOSITE[self.to_move]] = update_reachable(self.piece_loc[OPPOSITE[self.to_move]], self.board, OPPOSITE[self.to_move])

        # python
        #self.update_reachable(OPPOSITE[self.to_move])


        # lastly checking if the current player to move is standing in check
        self.update_in_check()

        # removing the current changes entry, because this is the special case of setup and we can not yet undo a move, because we havent made one. the appending to changes is a side effect of the functions we use here and it makes more sense to pop a useless item once, than to constantly track this special case
        self.changes.pop()

        # creating the zobrist hash for the current board position for the first time
        self.zobr_hash = self.hash_zobrist()

        # tracking the current position in case of a threefold repetition
        #snap = self.snapshot()
        self.threefold[self.zobr_hash] += 1

    # python version of the C ext. keep for debug
    def pseudo_legal_moves(self, color):
        noncaptures, captures = [],[]

        # looking only at the squares where the current players pieces are
        for sq in self.piece_loc[color]:
            
            y,x = INT2YX[sq]
            f = self.board[sq]
            piece_type = PIECE_SPLIT[f][1]

            # calculating all pieces except pawns
            if not piece_type == PAWN:
                pattern = PIECE_MOVEMENT_PATTERNS[piece_type]
                for direction in pattern:
                    for offset in direction:
                        new_field_coord = (y+offset[0],x+offset[1])

                        if new_field_coord not in YX2INT:
                            break
                        else:
                            new_field = YX2INT[new_field_coord]
                            target_color = PIECE_SPLIT[self.board[new_field]][0]
                        
                        # new field is empty and therefore a valid target field
                        if self.board[new_field] == NO_PIECE:
                            noncaptures.append((y,x,new_field_coord[0],new_field_coord[1],0))
                        # new field occupied by own piece, break this direction early
                        elif target_color == color:
                            break
                        # new field occupied by opponents piece, break, but allow this move (to capture)
                        elif target_color == OPPOSITE[color]:
                            captures.append((y,x,new_field_coord[0],new_field_coord[1],0))
                            break
            
            # calculating pawns separately because they have special move rules
            else:
                pattern = PIECE_MOVEMENT_PATTERNS[piece_type]['move']
                for direction in pattern:
                    for offset in direction:
                        new_field = (y+offset[0],x+offset[1]) if color == WHITE else (y-offset[0],x-offset[1])
                        
                        # we need to check out of bounds because the pawn can reach the edge of the board just before promoting
                        if new_field not in YX2INT:
                            break
                        # new field is empty and therefore a valid target field, all other cases are an illegal move because pawns capture sideways, which will be implemented in the third loop
                        elif self.board[YX2INT[new_field]] == NO_PIECE:
                            if new_field[0] == PROMOTE['rank'][color]:
                                for p in PROMOTE['options'][color]:
                                    noncaptures.append((y,x,new_field[0],new_field[1],p))
                            else:
                                noncaptures.append((y,x,new_field[0],new_field[1],0))

                # the special pawn move (forward by 2) is only possible if the pawn is on the 2nd rank for white or 7th rank for black, so we check this
                if (color == WHITE and y == 1) or (color == BLACK and y == 6):
                    pattern = PIECE_MOVEMENT_PATTERNS[piece_type]['double_move']
                    for direction in pattern:
                        for offset in direction:
                            new_field = (y+offset[0],x+offset[1]) if color == WHITE else (y-offset[0],x-offset[1])
                            through = (new_field[0]-1, new_field[1]) if color == WHITE else (new_field[0]+1, new_field[1])
                            
                            # new field is empty and therefore a valid target field AND the field before that is also empty
                            if self.board[YX2INT[new_field]] == NO_PIECE and self.board[YX2INT[through]] == NO_PIECE:
                                noncaptures.append((y,x,new_field[0],new_field[1],0))

                # implementation of the capturing move for pawns which goes sideways
                pattern = PIECE_MOVEMENT_PATTERNS[piece_type]['capture']
                for direction in pattern:
                    for offset in direction:
                        new_field = (y+offset[0],x+offset[1]) if color == WHITE else (y-offset[0],x-offset[1])
                        
                        # checking for out of bounds, which is possible with sideways capture
                        if new_field not in YX2INT:
                            break
                        # new field is occupied by an enemy piece and therefore a valid target field
                        elif PIECE_SPLIT[self.board[YX2INT[new_field]]][0] == OPPOSITE[color]:
                            if new_field[0] == PROMOTE['rank'][color]:
                                for p in PROMOTE['options'][color]:
                                    captures.append((y,x,new_field[0],new_field[1],p))
                            else:
                                captures.append((y,x,new_field[0],new_field[1],0))
                        elif YX2INT[new_field] == self.en_passant_target:
                            captures.append((y,x,new_field[0],new_field[1],0))

        # checking if special move castle is possible, seeing if own pieces are in the way, but not yet checking if we move through opponents check. this will be implemented in another function
        for c in self.castling_rights[color]:
            if all(self.board[sq] == NO_PIECE for sq in CASTLE['empty'][c]):
                noncaptures.append(CASTLE['kingmove'][c])

        return noncaptures, captures

    # this function creates a list of pseudo legal moves and then filters out all moves that would be illegal, e.g. if the move would put the own king in check by the opponent
    def legal_moves(self, onlycaptures=False):
        legal = []

        
        # C ext
        pseudo_noncaptures, pseudo_captures = pseudo_legal_moves(self.piece_loc[self.to_move],self.board,self.castling_rights[self.to_move],self.to_move,self.en_passant_target)

        # python
        #pseudo_noncaptures, pseudo_captures = self.pseudo_legal_moves(self.to_move)

        own_pseudo_legal = pseudo_captures if onlycaptures else pseudo_captures+pseudo_noncaptures

        opponents_pseudo_reachable = self.reachable[self.opponent]['all_direct']

        for move in own_pseudo_legal:

            fy,fx,ty,tx,prom = move
            from_sq, to_sq = YX2INT[(fy,fx)], YX2INT[(ty,tx)]
            moved_piece = self.board[from_sq]
            piece_type = PIECE_SPLIT[moved_piece][1]

            # checking if castles moves the king through a check
            if move in CASTLE["check"] and piece_type == KING:
                if all(sq not in opponents_pseudo_reachable for sq in CASTLE["check"][move]):
                    legal.append(move)

            # dealing with non-special moves by first simulating the move, then checking if our king is reachable by the opponent (aka in check) and then taking the move back via restoring a backup
            else:
                
                if self.in_check:

                    # simulating the move
                    self.move(move)

                    # move is legal and can be appended to list of legal moves
                    # C ext
                    if check_possible_king_capt(self.piece_loc[self.opponent],self.board,self.opponent) == 0:
                        legal.append(move)
            
                    # python
                    #if not self.check_possible_king_capt(self.opponent):
                        #legal.append(move)

                    # undoing the simulated move
                    self.undo_move()
                else:

                    if piece_type == KING:

                        if to_sq not in opponents_pseudo_reachable:
                            
                            legal.append(move)
                    else:
                        if from_sq not in self.reachable[self.opponent]['king_indirect_blocked'] and not (piece_type == PAWN and to_sq == self.en_passant_target):
                            legal.append(move)
                        else:
                            self.move(move)

                            # C ext
                            if check_possible_king_capt(self.piece_loc[self.opponent],self.board,self.opponent) == 0:
                                legal.append(move)
                            
                            # python
                            #if not self.check_possible_king_capt(self.opponent):
                                #legal.append(move)


                            self.undo_move()

        return legal

    # for the GUI we need to know if further user input is needed (in case of a promoting move). to easily distinguish the 2 cases, this function splits the legal moves into 2 lists.
    def split_legal_moves(self):
        legal_moves = self.legal_moves()
        normal_moves, promote_moves = [], []
        
        for m in legal_moves:
            if m[4] == 0:
                normal_moves.append(m)
            else:
                promote_moves.append(m)
        
        return (normal_moves, promote_moves)
    
    # executing a move on the board. this function provides no protection against passing illegal moves and must therefore be combined with a means of checking for legal moves
    def move(self, move, backup=True):

        # when attempting a move, we append a new item to the changes variable, that will allow us to undo each move without using more extensive backups
        if backup:
            self.changes.append({"board": [], 
                "piece_loc": {"remove": [], "add": []}, 
                "en_passant_target": None, 
                "castling_rights": [], 
                "kings": None})

        self.changes[-1]['last_move'] = move

        # setting up local variables
        fy,fx,ty,tx,prom = move
        from_sq, to_sq = YX2INT[(fy,fx)], YX2INT[(ty,tx)]
        moved_piece = self.board[from_sq]
        piece_color, piece_type = PIECE_SPLIT[self.board[from_sq]]
        capture = False if self.board[to_sq] == NO_PIECE else True

        # squares list is needed for the GUI, it has no function for the chess module itself
        squares = []

        # special case of en passant, where we need to update a square that is not directly visible in the fromto variable
        self.changes[-1]['en_passant_target'] = self.en_passant_target
        if piece_type == PAWN:
            if to_sq == self.en_passant_target:
                # clear the pawn that was taken en passant from the board and append squares
                en_passant_coord = INT2YX[self.en_passant_target]
                sq_clear_y = 3 if en_passant_coord[0] == 2 else 4
                sq_clear_x = en_passant_coord[1]
                sq_clear = YX2INT[(sq_clear_y,sq_clear_x)]

                self.changes[-1]['board'].append((sq_clear_y,sq_clear_x,self.board[sq_clear]))
                self.board[sq_clear] = 0
                
                self.changes[-1]['piece_loc']['add'].append((OPPOSITE[piece_color],sq_clear))
                self.piece_loc[OPPOSITE[piece_color]].remove(sq_clear)

                squares.append((sq_clear_y, sq_clear_x))
                capture = True
                
                self.en_passant_target = -1
            else:
                # update en passant target
                self.update_en_passant(moved_piece, move)
        else:
            self.en_passant_target = -1

        # special case castling, which is 2 moves in one, we process the rookmove first in a recursion layer and then proceed with the kingmove as a normal move. note we only need the squares of the rookmove as return value, the other 2 variables are unimportant at this step
        if piece_type == KING:
            if move in CASTLE['rookmove']:
                sq_rookmove, _, _ = self.move(CASTLE['rookmove'][move], backup=False)
                squares.extend(sq_rookmove)
                
                # re-updating the last move to be the kings move instead of the rooks move
                self.changes[-1]['last_move'] = move
            
            self.update_kings(moved_piece, move)

            for right in self.castling_rights[piece_color]:
                self.changes[-1]['castling_rights'].append((piece_color,right))
            self.castling_rights[piece_color] = []            

        # updating castling rights, depending on which rook was moved or if a rook was captured
        elif piece_type == ROOK or capture:
            self.update_castling(moved_piece, move, capture)

        # updating the from-square and the to-square, creating a new piece integer if we promote
        self.changes[-1]['board'].append((ty,tx,self.board[to_sq]))
        self.board[to_sq] = moved_piece if prom == 0 else prom
        self.changes[-1]['board'].append((fy,fx,self.board[from_sq]))
        self.board[from_sq] = 0

        self.changes[-1]['piece_loc']['remove'].append((piece_color,to_sq))
        self.piece_loc[piece_color].add(to_sq)
        
        if to_sq in self.piece_loc[OPPOSITE[piece_color]]:
            self.changes[-1]['piece_loc']['add'].append((OPPOSITE[piece_color],to_sq))
            self.piece_loc[OPPOSITE[piece_color]].remove(to_sq)
        
        self.changes[-1]['piece_loc']['add'].append((piece_color,from_sq))
        self.piece_loc[piece_color].remove(from_sq)

        # returning a list of squares that have been updated by this function
        squares.extend([(fy, fx), (ty, tx)])
        return (squares, capture, moved_piece)

    # this function first updates the board variables and then checks if any game over conditions have been met
    def commit(self, move, capture, moved_piece):

        fy,fx,ty,tx,_ = move
        from_sq, to_sq = YX2INT[(fy,fx)], YX2INT[(ty,tx)]
        piece_color, piece_type = PIECE_SPLIT[moved_piece]

        # when committing a move, it makes sense to update this variable, as it is the basis for the  calculation of next moves
        # C ext
        self.reachable[piece_color] = update_reachable(self.piece_loc[piece_color],self.board,piece_color)

        # python
        #self.update_reachable(piece_color)

        self.changes[-1]['half_moves'] = self.half_moves
        if capture or piece_type == PAWN:
            self.half_moves = 0
        else:
            self.half_moves += 1
        
        if piece_color == BLACK:
            self.changes[-1]['full_moves'] = self.full_moves
            self.full_moves += 1

        # changing who is to move at last
        self.to_move, self.opponent = self.opponent, self.to_move

        # backing up and updating the zobrist hash
        self.changes[-1]['zobr_hash'] = self.zobr_hash
        self.zobr_hash = self.hash_zobrist()

        # checking if the player that is now to move is standing in check
        self.update_in_check()

        # next we check for game_over conditions. checkmate and stalemate are the most common ones and are checked first. the others are more rare and are sequenced roughly in order of difficulty of checking

        self.changes[-1]['gameover'] = self.gameover

        # checkmate and stalemate
        if not self.legal_moves():
            if self.in_check:
                self.gameover = (1 if self.to_move == BLACK else 0, "checkmate")
            else:
                self.gameover = (0.5, "draw_stalemate")
        
        # draw by 50 move rule (reach 100 half-moves)
        if self.half_moves > 99:
            self.gameover = (0.5, "draw_50move")
        
        # threefold repetition
        self.check_threefold(capture, moved_piece)

        # insufficient material
        self.check_insufficient()

    # this function is a combination of move and commit, the first just executes the move itself and the second updates game variables. it is feasible to separate these into 2 functions because in order to check legal moves we need to "simulate" moves, in which case an update of game variables would be unnessecary and potentially cause bugs
    def commit_move(self, move):
        # executing the move
        sqlist, capture, moved_piece = self.move(move)
        # updating global game variables
        self.commit(move, capture, moved_piece)

        # passing the list of updated squares from the move function
        return sqlist

    # takes a snapshot of the board and the pieces, but NOT the according objects. this is to prevent the threefold repetition rule not triggering if pieces (e.g. 2 knights) are interchanged, which results in the same position on the board, but would not trigger a positive comparison of 2 snapshots, as the 2 knights are represented by different objects. note that it would also be possible and more efficient to do this via the zobrist hash that we use for the bot module, but for now lets keep it as is.
    #def snapshot(self):
        #return tuple(sq for sq in self.board)

    # updating the kings position, depending on which color king was moved and where
    def update_kings(self, moved_piece, move):
        piece_color = PIECE_SPLIT[moved_piece][0]
        new_sq = YX2INT[(move[2], move[3])]

        self.changes[-1]['kings'] = (piece_color,self.kings[piece_color])
        self.kings[piece_color] = new_sq

    # updating the possible en passant square, depending on which pawn moved and where
    def update_en_passant(self, moved_piece, move):
        from_rank, to_rank, col = move[0], move[2], move[1]
        piece_color = PIECE_SPLIT[moved_piece][0]
        
        if to_rank == EN_PASSANT[piece_color]['to_rank'] and from_rank == EN_PASSANT[piece_color]['from_rank']:
            self.en_passant_target = YX2INT[(EN_PASSANT[piece_color]['target'], col)]
        else:
            self.en_passant_target = -1

    # updating the castling rights (ONLY called if a rook moves or is captured, because king move sets the castling rights to zero always and does not need a function to handle)
    def update_castling(self, moved_piece, move, capture):
        from_sq, to_sq = YX2INT[(move[0],move[1])], YX2INT[(move[2],move[3])]
        piece_color = PIECE_SPLIT[moved_piece][0]
        
        # in case a piece is moved from one original rook square (must be a rook the first time this happens)
        if from_sq in CASTLE['rights']:
            if CASTLE['rights'][from_sq] in self.castling_rights[piece_color]:
                self.changes[-1]['castling_rights'].append((piece_color,CASTLE['rights'][from_sq]))
                self.castling_rights[piece_color].remove(CASTLE['rights'][from_sq])
        
        # in case a piece is captured on one original rook square (must be a rook the first time this happens)
        if capture:
            if to_sq in CASTLE['rights']:
                if CASTLE['rights'][to_sq] in self.castling_rights[OPPOSITE[piece_color]]:
                    self.changes[-1]['castling_rights'].append((OPPOSITE[piece_color],CASTLE['rights'][to_sq]))
                    self.castling_rights[OPPOSITE[piece_color]].remove(CASTLE['rights'][to_sq])  

    # simply returning if the king of the current player is standing in check
    def update_in_check(self):
        self.changes[-1]['in_check'] = self.in_check
        self.in_check = True if self.kings[self.to_move] in self.reachable[self.opponent]['all_direct'] else False

    # draw by insufficient material if both sides have no more than the following: k, k+b, k+n, in all other cases, the game will continue
    def check_insufficient(self):
        pieces = defaultdict(int)
        for v in self.piece_loc.values():
            for sq in v:
                f = self.board[sq]
                piece_type = PIECE_SPLIT[f][1]
                # if we see a rook, queen or pawn, we terminate early
                if piece_type == PAWN or piece_type == ROOK or piece_type == QUEEN:
                    return
                # counting pieces for each color
                pieces[f] += 1
        
        # checking the conditions after counting pieces and updating the game_over variable if necessary
        if pieces[WBISHOP]+pieces[WKNIGHT] < 2 and pieces[BBISHOP]+pieces[BKNIGHT] < 2:
            self.gameover = (0.5, "draw_insufficient")

    # keeping track of the current position and checking if it has already occured 2 times before. if a pawn is moved or a piece is captured, that means the position can never be the same, so all tracked positions are forgotten to prevent the tracking dict from growing too large
    def check_threefold(self, capture, moved_piece):
        if not capture and not PIECE_SPLIT[moved_piece][1] == PAWN:
            #snap = self.snapshot()
            self.changes[-1]['threefold'] = (SUBTRACT,self.zobr_hash)
            self.threefold[self.zobr_hash] += 1
            
            if self.threefold[self.zobr_hash] > 2:
                self.gameover = (0.5, "draw_threefold")
        else:
            self.changes[-1]['threefold'] = (REPLACE,self.threefold)
            self.threefold = defaultdict(int)

    # instead of backing up and restoring the whole board, we are appending change data to the changes variable. this function takes advantage of that and reverses all the changes that were made during the execution of a move, resulting in the undoing of that move. note that this function distinguishes between a move that was simulated ("move") or commited ("commit_move"). the undoing of moves via this function instead of backing up and restoring is only slightly faster, because we modify the changes data with every move. however, we gain the advantage of being able to take back unlimited moves in a row which was not possible with the backup method unless we stored multiple board backups
    def undo_move(self, commited=False):
        
        # getting the current moves change data
        change = self.changes.pop()
        
        # reversing all changes, depending on which key is given in the data. this works for different lengths, so the change data does not need to contain all keys every time. might need to be switched or C ext
        for key, value in change.items():
            key_map = CHANGES_KEYS[key]
            if key_map == BOARD:
                for t in value:
                    y,x,old_piece = t
                    self.board[YX2INT[(y,x)]] = old_piece
            elif key_map == PIECE_LOC:
                for key2, value2 in value.items():
                    key2_map = CHANGES_KEYS[key2]
                    if key2_map == REMOVE:
                        for t in value2:
                            color, sq = t
                            self.piece_loc[color].remove(sq)
                    elif key2_map == ADD:
                        for t in value2:
                            color, sq = t
                            self.piece_loc[color].add(sq)
            elif key_map == EN_PASSANT_TARGET:
                self.en_passant_target = value
            elif key_map == CASTLING_RIGHTS:
                for t in value:
                    color, right = t
                    self.castling_rights[color].append(right)
            elif key_map == KINGS:
                if value:
                    color, sq = value
                    self.kings[color] = sq
            elif key_map == REACHABLE:
                color, backup = value
                self.reachable[color] = backup
            elif key_map == HALF_MOVES:
                self.half_moves = value
            elif key_map == FULL_MOVES:
                self.full_moves = value
            elif key_map == IN_CHECK:
                self.in_check = value
            elif key_map == GAMEOVER:
                self.gameover = value
            elif key_map == THREEFOLD:
                action, item = value
                if action == REPLACE:
                    self.threefold = item
                elif action == SUBTRACT:
                    self.threefold[item] -= 1
            elif key_map == ZOBR_HASH:
                self.zobr_hash = value

        # the reason for the distinguishment between a simulated and a committed move is, that in a simulated move, the player that is to move stays the same, whereas in a committed move it switches 
        if commited:
            # no fancy backup necessary, just switch back
            self.to_move, self.opponent = self.opponent, self.to_move

    # this function creates a new zobrist mask by assigning each piece-square combination a random 64bit number, plus another 64bit number that is used if black is to move. it is optional, as a functional zobrist mask is provided as json file. note if you want to use a new mask, the openings database also has to be reloaded with that mask, otherwise a bot instance will not be able to associate zobrist hashes with the opening positions
    def create_new_zobrist(self):
        zobr = [{WKING: None, WQUEEN: None, WPAWN: None, WBISHOP: None, WKNIGHT: None, WROOK: None, BKING: None, BQUEEN: None, BPAWN: None, BBISHOP: None, BKNIGHT: None, BROOK: None} for i in range(64)]
        zobr_black = random.getrandbits(64)

        for sq in range(64):
                for key in zobr[sq]:
                    zobr[sq][key] = random.getrandbits(64)

        combined = {"black_mask": zobr_black, "board_mask": zobr}

        # serializing json
        json_object = json.dumps(combined, indent=4)
        
        # writing to sample.json
        with open("new_zobrist_mask.json", "w") as outfile:
            outfile.write(json_object)

    # loading in a previously created zobrist mask to make sure we use the same mask for all instances
    def init_zobrist(self):

        with open(ZOBRIST_FILE) as json_file:
            temp_zobr = json.load(json_file)

        self.zobr_black = temp_zobr['black_mask']
        self.zobr = [{int(key): value for key, value in d.items()} for d in temp_zobr['board_mask']]

    # this funciton creates a 64bit zobrist hash to represent the current state of the board. this is done by XORing every random number that gets a hit in the current configuration (e.g. if there is a black knight on e4, then the hash will be XORed with the black knight + e4 number). this function creates the hash from scratch, and it is possible to update it with each move. however, due to special moves en passant and castling, this is a bit tricky and we avoid it for now, since the computation is quite quick
    def hash_zobrist(self):
        h = 0
        if self.to_move == BLACK:
            h = h ^ self.zobr_black
        
        for sq in range(64):
                curr_piece = self.board[sq]
                if curr_piece != NO_PIECE:
                    h = h ^ self.zobr[sq][curr_piece]
        
        return h

    # goes through all possible variations to the given depth and compares to the python chess engine. in case there is a mismatch, this function will print some debug info and stop early. this is a pure debug function that is not needed for "normal" use of this class
    def find_variations_compare(self, depth, comparison_board):

        count= 0

        if depth == 0:
            return 1
        
        # generating legal moves for the current depth
        my_movelist = self.legal_moves()
        #print(my_movelist)
        true_movelist = list(comparison_board.legal_moves)

        # early termination in case of a mismatch and printing of debug info
        if len(my_movelist) != len(true_movelist):

            print(self) # our own board position

            print("pseudo legal:")
            
            # C ext
            pseudo_noncapt, pseudo_capt = pseudo_legal_moves(self.piece_loc[self.to_move],self.board,self.castling_rights[self.to_move],self.to_move,self.en_passant_target)

            # python
            #pseudo_noncapt, pseudo_capt = self.pseudo_legal_moves(self.to_move)
            
            print(len(pseudo_noncapt)+len(pseudo_capt)) # pseudo legal moves for own board
            print([move2uci(move) for move in pseudo_noncapt+pseudo_capt])

            print("legal:") # legal moves for own board
            print(len(my_movelist))
            print([move2uci(move) for move in my_movelist])

            print("reachable:")
            print(self.reachable)

            print("compare:")
            print(len(true_movelist))
            print(true_movelist) # legal moves for python chess board

            print(comparison_board) # python chess board position
            
            raise Exception("bug found!") # early termination by exception

        for move in my_movelist:
            # trying all possible moves one by one both for our own board and for python chess board
            self.commit_move(move)
            
            # note that we dont use moves from the true_movelist, because then we would not know if they are the same move as the one we chose from our movelist! instead, we translate our move to the uci notation of python chess and execute it in that way
            comparison_board.push(chess.Move.from_uci(move2uci(move)))
            
            # recursion for the next moves, depth decreases by 1 and the current state of the comparison board is also passed to the function
            count += self.find_variations_compare(depth-1, comparison_board)

            # taking the move back on both our own board and the python chess board
            self.undo_move(commited=True)
            comparison_board.pop()
        
        return count

    # python version of the C ext. keep for debug
    def check_possible_king_capt(self, color):

        for sq in self.piece_loc[color]:
            y,x = INT2YX[sq]
            f = self.board[sq]
            piece_type = PIECE_SPLIT[f][1]

            # calculating all pieces except pawns
            if not piece_type == PAWN:
                pattern = PIECE_MOVEMENT_PATTERNS[piece_type]
                for direction in pattern:
                    for offset in direction:
                        new_field_coord = (y+offset[0],x+offset[1])
                        
                        if new_field_coord not in YX2INT:
                            break
                        else:
                            new_field = YX2INT[new_field_coord]

                        # new field is empty and therefore a valid target field
                        if self.board[new_field] == NO_PIECE:
                            continue
                        # new field occupied by own piece, break this direction early
                        elif PIECE_SPLIT[self.board[new_field]][0] == color:
                            break
                        # new field occupied by opponents king
                        elif self.board[new_field] == OPPOSITE[color]+KING:
                            return True
                        # new field occupied by an enemy piece that is not the king
                        else:
                            break
   
            # calculating pawns separately because they have special move rules
            else:

                # implementation of the capturing move for pawns which goes sideways
                pattern = PIECE_MOVEMENT_PATTERNS[piece_type]['capture']
                for direction in pattern:
                    for offset in direction:
                        new_field = (y+offset[0],x+offset[1]) if color == WHITE else (y-offset[0],x-offset[1])
                        
                        # checking for out of bounds, which is possible with sideways capture
                        if new_field not in YX2INT:
                            break
                        # new field is occupied by an enemy piece and therefore a valid target field
                        elif self.board[YX2INT[new_field]] == OPPOSITE[color]+KING:
                            return True

        return False

    # python version of the C ext. keep for debug
    def update_reachable(self, color):

        self.changes[-1]['reachable'] = (color, self.reachable[color])
        self.reachable[color] = {"all_direct": set(), "king_indirect_blocked": set(), "pawn_attack": set()}

        for sq in self.piece_loc[color]:
            y,x = INT2YX[sq]
            f = self.board[sq]
            piece_type = PIECE_SPLIT[f][1]

            # calculating all pieces except pawns
            if not piece_type == PAWN:
                pattern = PIECE_MOVEMENT_PATTERNS[piece_type]
                for direction in pattern:
                    blocking_piece = None
                    for offset in direction:
                        new_field_coord = (y+offset[0],x+offset[1])
                        
                        if new_field_coord not in YX2INT:
                            break
                        else:
                            new_field = YX2INT[new_field_coord]
                            new_color = PIECE_SPLIT[self.board[new_field]][0]

                        if not blocking_piece:
                            
                            # new field is empty and therefore a valid target field
                            if self.board[new_field] == NO_PIECE:
                                self.reachable[color]['all_direct'].add(new_field)
                            # new field occupied by own piece, break this direction early, but add, since that means protecting the piece
                            elif new_color == color:
                                self.reachable[color]['all_direct'].add(new_field)
                                break
                            # new field occupied by opponents piece, allow this move (to capture) and then see if the fields behind the blocking piece are the opponents king location
                            elif new_color == OPPOSITE[color]:
                                self.reachable[color]['all_direct'].add(new_field)
                                blocking_piece = new_field
                        else:

                            # new field is empty, continue looking
                            if self.board[new_field] == NO_PIECE:
                                continue
                            # new field occupied by own piece, break this direction early
                            elif new_color == color:
                                break
                            # found the enemy king, this means a piece has a line towards the king that is blocked by the blocking_piece, which we therefore add to the dict and break
                            elif self.board[new_field] == OPPOSITE[color]+KING:
                                self.reachable[color]['king_indirect_blocked'].add(blocking_piece)
                                break
                            # in all other cases, e.g. finding another enemy piece, we break without adding anything to the dict
                            else:
                                break                       

            # calculating pawns separately because they have special move rules
            else:

                # only pawn captures need to be considered, as this is about seeing if we can beat the king
                pattern = PIECE_MOVEMENT_PATTERNS[piece_type]['capture']
                for direction in pattern:
                    for offset in direction:
                        new_field = (y+offset[0],x+offset[1]) if color == WHITE else (y-offset[0],x-offset[1])
                        
                        # checking for out of bounds, which is possible with sideways capture
                        if new_field not in YX2INT:
                            break
                        # new field is occupied by an enemy or own piece or empty and therefore a valid target field
                        else:
                            self.reachable[color]['all_direct'].add(YX2INT[new_field])
                            self.reachable[color]['pawn_attack'].add(YX2INT[new_field])
                            break

    # printing the board mainly for quick testing and debugging. a proper graphical interface is implemented separately
    def __str__(self):
        output = '\n'

        # need to reverse the board for printing or else it would be white against us, deviating from chess standard display and quite confusing.
        for y in range(7,-1,-1):
            str1 = ' '.join(f'{PIECE_STR[self.board[YX2INT[(y,x)]]]}' for x in range(8))
            # adding indices for easy reference
            output += str(y) + " | " + str1 + '\n'
        output += '--+----------------' + '\n' + "  | 0 1 2 3 4 5 6 7" + '\n'
        
        return output


if __name__ == "__main__":

    cProfile.run('test_module()')



"""
        self.reachable[color] = {"all_direct": set(), "king_indirect_blocked": set(), "pawn_attack": set()}

        for sq in self.piece_loc[color]:
            y,x = INT2YX[sq]
            f = self.board[sq]
            piece_type = PIECE_SPLIT[f][1]

            # calculating all pieces except pawns
            if not piece_type == PAWN:
                pattern = PIECE_MOVEMENT_PATTERNS[piece_type]
                for direction in pattern:
                    blocking_piece = None
                    for offset in direction:
                        new_field_coord = (y+offset[0],x+offset[1])
                        
                        if new_field_coord not in YX2INT:
                            break
                        else:
                            new_field = YX2INT[new_field_coord]
                            new_color = PIECE_SPLIT[self.board[new_field]][0]

                        if not blocking_piece:
                            
                            # new field is empty and therefore a valid target field
                            if self.board[new_field] == NO_PIECE:
                                self.reachable[color]['all_direct'].add(new_field)
                            # new field occupied by own piece, break this direction early, but add, since that means protecting the piece
                            elif new_color == color:
                                self.reachable[color]['all_direct'].add(new_field)
                                break
                            # new field occupied by opponents piece, allow this move (to capture) and then see if the fields behind the blocking piece are the opponents king location
                            elif new_color == OPPOSITE[color]:
                                self.reachable[color]['all_direct'].add(new_field)
                                blocking_piece = new_field
                        else:

                            # new field is empty, continue looking
                            if self.board[new_field] == NO_PIECE:
                                continue
                            # new field occupied by own piece, break this direction early
                            elif new_color == color:
                                break
                            # found the enemy king, this means a piece has a line towards the king that is blocked by the blocking_piece, which we therefore add to the dict and break
                            elif self.board[new_field] == OPPOSITE[color]+KING:
                                self.reachable[color]['king_indirect_blocked'].add(blocking_piece)
                                break
                            # in all other cases, e.g. finding another enemy piece, we break without adding anything to the dict
                            else:
                                break                       

            # calculating pawns separately because they have special move rules
            else:

                # only pawn captures need to be considered, as this is about seeing if we can beat the king
                pattern = PIECE_MOVEMENT_PATTERNS[piece_type]['capture']
                for direction in pattern:
                    for offset in direction:
                        new_field = (y+offset[0],x+offset[1]) if color == WHITE else (y-offset[0],x-offset[1])
                        
                        # checking for out of bounds, which is possible with sideways capture
                        if new_field not in YX2INT:
                            break
                        # new field is occupied by an enemy or own piece or empty and therefore a valid target field
                        else:
                            self.reachable[color]['all_direct'].add(YX2INT[new_field])
                            self.reachable[color]['pawn_attack'].add(YX2INT[new_field])
                            break
"""