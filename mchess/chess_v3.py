# further improved version that is slightly faster and uses an "undo-move" mechanic to take back moves instead of backing up and restoring the Board class
# only contains the game mechanic, not the GUI

from collections import defaultdict
import json
import os

import cProfile # for timing and performance optimization

import chess # only for debugging


"""HELPER FUNCTIONS""" 
# region

# this helper function translates a chess notation (e.g. d4) to our internal board notation tuple
def cnote2tuple(cnote):
    char, digit = cnote[0], cnote[1]
    y = int(digit) - 1
    x = "abcdefgh".index(char)
    return (y,x)

# converting a move of our own chess game to the uci notation used by python chess module
def move2uci(move):
    y_from, x_from = move[0]
    y_to, x_to = move[1]

    c_convert = "abcdefgh"
    uci_c_from, uci_c_to = c_convert[x_from], c_convert[x_to]
    uci_d_from, uci_d_to = y_from+1, y_to+1

    uci = [uci_c_from, str(uci_d_from), uci_c_to, str(uci_d_to)]

    # special case promotion, when our move tuple has a third component
    if len(move) == 3:
        uci.append(move[-1].lower())
    
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

TEST_POSITIONS_FILE = os.path.join(ABS_DIR_PATH, "data/debug_positions.json")

# using this set for lookup is slightly faster than mathematically checking if a square is on the board
VALID_SQUARES = {(y,x) for y in range(8) for x in range(8)}

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

# the str equivalent of pieces in the Piece class
PIECE_STR = {value: key for key, value in PIECE_INIT.items()}
PIECE_STR[0] = "."

PIECE_MOVEMENT_PATTERNS = {
    ROOK: [[(1,0),(2,0),(3,0),(4,0),(5,0),(6,0),(7,0)],[(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7)],[(-1,0),(-2,0),(-3,0),(-4,0),(-5,0),(-6,0),(-7,0)],[(0,-1),(0,-2),(0,-3),(0,-4),(0,-5),(0,-6),(0,-7)]],
    BISHOP: [[(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7)],[(-1,-1),(-2,-2),(-3,-3),(-4,-4),(-5,-5),(-6,-6),(-7,-7)],[(1,-1),(2,-2),(3,-3),(4,-4),(5,-5),(6,-6),(7,-7)],[(-1,1),(-2,2),(-3,3),(-4,4),(-5,5),(-6,6),(-7,7)]],
    QUEEN: [[(1,0),(2,0),(3,0),(4,0),(5,0),(6,0),(7,0)],[(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7)],[(-1,0),(-2,0),(-3,0),(-4,0),(-5,0),(-6,0),(-7,0)],[(0,-1),(0,-2),(0,-3),(0,-4),(0,-5),(0,-6),(0,-7)],[(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7)],[(-1,-1),(-2,-2),(-3,-3),(-4,-4),(-5,-5),(-6,-6),(-7,-7)],[(1,-1),(2,-2),(3,-3),(4,-4),(5,-5),(6,-6),(7,-7)],[(-1,1),(-2,2),(-3,3),(-4,4),(-5,5),(-6,6),(-7,7)]],
    KING: [[(1,1)],[(0,1)],[(-1,1)],[(-1,0)],[(-1,-1)],[(0,-1)],[(1,-1)],[(1,0)]],
    KNIGHT: [[(2,1)],[(1,2)],[(-1,2)],[(-2,1)],[(-2,-1)],[(-1,-2)],[(1,-2)],[(2,-1)]],
    PAWN: {"move": [[(1,0)]], "double_move": [[(2,0)]], "capture": [[(1,-1)],[(1,1)]]}}

# lookup for everything related to the special move castle
CASTLE = {
    "empty": {"K": [(0,5),(0,6)], "Q": [(0,1),(0,2),(0,3)],
            "k": [(7,5),(7,6)], "q": [(7,1),(7,2),(7,3)]},
    "kingmove": {"K": ((0,4),(0,6)), "Q": ((0,4),(0,2)),
            "k": ((7,4),(7,6)), "q": ((7,4),(7,2))},
    "rookmove": {((0,4),(0,6)): ((0,7),(0,5)), ((0,4),(0,2)): ((0,0),(0,3)),
            ((7,4),(7,6)): ((7,7),(7,5)), ((7,4),(7,2)): ((7,0),(7,3))},
    "check": {((0,4),(0,6)): [(0,4),(0,5),(0,6)], ((0,4),(0,2)): [(0,4),(0,3),(0,2)],
            ((7,4),(7,6)): [(7,4),(7,5),(7,6)], ((7,4),(7,2)): [(7,4),(7,3),(7,2)]},
    "update": {((0,4),(0,6)): [(0,4),(0,5),(0,6),(0,7)], ((0,4),(0,2)): [(0,4),(0,3),(0,2),(0,0)],
            ((7,4),(7,6)): [(7,4),(7,5,(7,6),(7,7))], ((7,4),(7,2)): [(7,4),(7,3),(7,2),(7,0)]},
    "rights": {(0,0): "Q", (0,7): "K", (7,0): "q", (7,7): "k"}}

# lookup to handle everything related to special move promotion
PROMOTE = {
    "rank": {WHITE: 7, BLACK: 0},
    "options": {WHITE: "QRBN", BLACK: "qrbn"}}

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

# mapping the key string (which are needed for debugging) to the according integers
CHANGES_KEYS = {"board": BOARD, "kings": KINGS, "in_check": IN_CHECK, "threefold": THREEFOLD, "piece_loc": PIECE_LOC, "reachable": REACHABLE, "en_passant_target": EN_PASSANT_TARGET, "half_moves": HALF_MOVES, "full_moves": FULL_MOVES, "castling_rights": CASTLING_RIGHTS, "gameover": GAMEOVER, "last_move": LAST_MOVE, "add": ADD, "remove": REMOVE, "subtract": SUBTRACT, "replace": REPLACE}

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

    # sets up a 2d-array with "." as default to represent an empty field
    def empty_board(self):
        self.board = [[Piece() for i in range(8)] for j in range(8)]

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
                self.castling_rights[WHITE].append(c)
            else:
                self.castling_rights[BLACK].append(c)

        self.en_passant_target = cnote2tuple(fen_fields[3]) if fen_fields[3] != "-" else "-"
        self.half_moves = int(fen_fields[4])
        self.full_moves = int(fen_fields[5])
        
        # going through the main part of the FEN to assign the pieces to their respective fields
        sfen = fen_fields[0].split('/')[::-1]
        for y in range(8):
            x = 0
            for c in sfen[y]:
                if c.isalpha():
                    self.board[y][x] = Piece(c)
                    color = self.board[y][x].color
                    self.piece_loc[color].add((y,x))
                    if c == "k":
                        self.kings[BLACK] = (y, x)
                    if c == "K":
                        self.kings[WHITE] = (y, x)
                    x += 1
                else:
                    x += int(c)

        # update reachable, only needed for the current opponent
        self.update_reachable(OPPOSITE[self.to_move])

        # lastly checking if the current player to move is standing in check
        self.update_in_check()

        # removing the current changes entry, because this is the special case of setup and we can not yet undo a move, because we havent made one. the appending to changes is a side effect of the functions we use here and it makes more sense to pop a useless item once, than to constantly track this special case
        self.changes.pop()

        # tracking the current position in case of a threefold repetition
        snap = self.snapshot()
        self.threefold[snap] += 1

    # this function returns a list of all pseudo legal moves for the player of a certain color (white or black). pseudo legal means the pieces can move in that way, but checks or other "forcing" conditions are not yet looked at. it is quite a lot of code and it would be possible to distribute it to multiple functions, but having it in one place seems to make more sense to me in this case.
    def pseudo_legal_moves(self, color):
        non_captures, captures = [], []

        # looking only at the squares where the current players pieces are
        for y,x in self.piece_loc[color]:
            f = self.board[y][x]

            # calculating all pieces except pawns
            if not f.piece == PAWN:
                pattern = f.move_pattern()
                for direction in pattern:
                    for offset in direction:
                        new_field = (y+offset[0],x+offset[1])
                        
                        # new field out of bounds
                        if new_field not in VALID_SQUARES:
                            break
                        # new field is empty and therefore a valid target field
                        elif self.board[new_field[0]][new_field[1]].piece == NO_PIECE:
                            non_captures.append(((y,x),new_field))
                        # new field occupied by own piece, break this direction early
                        elif self.board[new_field[0]][new_field[1]].color == color:
                            break
                        # new field occupied by opponents piece, break, but allow this move (to capture)
                        elif self.board[new_field[0]][new_field[1]].color == OPPOSITE[color]:
                            captures.append(((y,x),new_field))
                            break
            
            # calculating pawns separately because they have special move rules
            else:
                pattern = f.move_pattern()['move']
                for direction in pattern:
                    for offset in direction:
                        new_field = (y+offset[0],x+offset[1]) if color == WHITE else (y-offset[0],x-offset[1])
                        
                        # we need to check out of bounds because the pawn can reach the edge of the board just before promoting
                        if new_field not in VALID_SQUARES:
                            break
                        # new field is empty and therefore a valid target field, all other cases are an illegal move because pawns capture sideways, which will be implemented in the third loop
                        elif self.board[new_field[0]][new_field[1]].piece == NO_PIECE:
                            if new_field[0] == PROMOTE['rank'][color]:
                                for p in PROMOTE['options'][color]:
                                    non_captures.append(((y,x),new_field,p))
                            else:
                                non_captures.append(((y,x),new_field))

                # the special pawn move (forward by 2) is only possible if the pawn is on the 2nd rank for white or 7th rank for black, so we check this
                if (color == WHITE and y == 1) or (color == BLACK and y == 6):
                    pattern = f.move_pattern()['double_move']
                    for direction in pattern:
                        for offset in direction:
                            new_field = (y+offset[0],x+offset[1]) if color == WHITE else (y-offset[0],x-offset[1])
                            through = (new_field[0]-1, new_field[1]) if color == WHITE else (new_field[0]+1, new_field[1])
                            
                            # new field is empty and therefore a valid target field AND the field before that is also empty
                            if self.board[new_field[0]][new_field[1]].piece == NO_PIECE and self.board[through[0]][through[1]].piece == NO_PIECE:
                                non_captures.append(((y,x),new_field))

                # implementation of the capturing move for pawns which goes sideways
                pattern = f.move_pattern()['capture']
                for direction in pattern:
                    for offset in direction:
                        new_field = (y+offset[0],x+offset[1]) if color == WHITE else (y-offset[0],x-offset[1])
                        
                        # checking for out of bounds, which is possible with sideways capture
                        if new_field not in VALID_SQUARES:
                            break
                        # new field is occupied by an enemy piece and therefore a valid target field
                        elif self.board[new_field[0]][new_field[1]].color == OPPOSITE[color]:
                            if new_field[0] == PROMOTE['rank'][color]:
                                for p in PROMOTE['options'][color]:
                                    captures.append(((y,x),new_field,p))
                            else:
                                captures.append(((y,x),new_field))
                        elif (new_field[0],new_field[1]) == self.en_passant_target:
                            captures.append(((y,x),new_field))

        # checking if special move castle is possible, seeing if own pieces are in the way, but not yet checking if we move through opponents check. this will be implemented in another function
        for c in self.castling_rights[color]:
            if all(self.board[sq[0]][sq[1]].piece == NO_PIECE for sq in CASTLE['empty'][c]):
                non_captures.append(CASTLE['kingmove'][c])

        return non_captures, captures

    # this function creates a list of pseudo legal moves and then filters out all moves that would be illegal, e.g. if the move would put the own king in check by the opponent
    def legal_moves(self, onlycaptures=False):
        legal = []

        if onlycaptures:
            _, own_pseudo_legal = self.pseudo_legal_moves(self.to_move)
        else:
            non_captures, captures = self.pseudo_legal_moves(self.to_move)
            own_pseudo_legal = non_captures + captures
        opponents_pseudo_reachable = self.reachable[self.opponent]['all_direct']

        for move in own_pseudo_legal:
            
            from_y, from_x = move[0]
            to_y, to_x = move[1]
            moved_piece = self.board[from_y][from_x]

            # checking if castles moves the king through a check
            if move in CASTLE["check"] and moved_piece.piece == KING:
                if all(sq not in opponents_pseudo_reachable for sq in CASTLE["check"][move]):
                    legal.append(move)

            # dealing with non-special moves by first simulating the move, then checking if our king is reachable by the opponent (aka in check) and then taking the move back via restoring a backup
            else:
                
                if self.in_check:
                    # simulating the move
                    self.move(move)
                    
                    # move is legal and can be appended to list of legal moves
                    if not self.check_possible_king_capt(self.opponent):
                        legal.append(move)
            
                    # undoing the simulated move
                    self.undo_move()
                else:
                    if moved_piece.piece == KING:
                        if (to_y,to_x) not in opponents_pseudo_reachable:
                            legal.append(move)
                    else:
                        if (from_y,from_x) not in self.reachable[self.opponent]['king_indirect_blocked'] and not (moved_piece.piece == PAWN and (to_y,to_x) == self.en_passant_target):
                            legal.append(move)
                        else:
                            self.move(move)

                            if not self.check_possible_king_capt(self.opponent):
                                legal.append(move)
                            
                            self.undo_move()

        return legal

    # for the GUI we need to know if further user input is needed (in case of a promoting move). to easily distinguish the 2 cases, this function splits the legal moves into 2 lists
    def split_legal_moves(self):
        legal_moves = self.legal_moves()
        normal_moves, promote_moves = [], []
        for m in legal_moves:
            L = len(m)
            if L == 2:
                normal_moves.append(m)
            elif L == 3:
                promote_moves.append(m)
        
        return (normal_moves, promote_moves)

    # this function works almost identical to pseudo_legal_moves, but instead of appending all moves to a list, it just checks whether the enemy king can be captured or not and returns as early as possible to save time
    def check_possible_king_capt(self, color):

        for y,x in self.piece_loc[color]:
            f = self.board[y][x]

            # calculating all pieces except pawns
            if not f.piece == PAWN:
                pattern = f.move_pattern()
                for direction in pattern:
                    for offset in direction:
                        new_field = (y+offset[0],x+offset[1])
                        
                        # new field out of bounds
                        if new_field not in VALID_SQUARES:
                            break
                        # new field is empty and therefore a valid target field
                        elif self.board[new_field[0]][new_field[1]].piece == NO_PIECE:
                            continue
                        # new field occupied by own piece, break this direction early
                        elif self.board[new_field[0]][new_field[1]].color == color:
                            break
                        # new field occupied by opponents king
                        elif self.board[new_field[0]][new_field[1]].content == OPPOSITE[color]+KING:
                            return True
                        # new field occupied by an enemy piece that is not the king
                        else:
                            break
   
            # calculating pawns separately because they have special move rules
            else:

                # implementation of the capturing move for pawns which goes sideways
                pattern = f.move_pattern()['capture']
                for direction in pattern:
                    for offset in direction:
                        new_field = (y+offset[0],x+offset[1]) if color == WHITE else (y-offset[0],x-offset[1])
                        
                        # checking for out of bounds, which is possible with sideways capture
                        if new_field not in VALID_SQUARES:
                            break
                        # new field is occupied by an enemy piece and therefore a valid target field
                        elif self.board[new_field[0]][new_field[1]].content == OPPOSITE[color]+KING:
                            return True

        return False
    
    # executing a move on the board. this function provides no protection against passing illegal moves and must therefore be combined with a means of checking for legal moves
    def move(self, fromto, backup=True):

        # when attempting a move, we append a new item to the changes variable, that will allow us to undo each move without using extensive backups
        if backup:
            self.changes.append({"board": [], 
                "piece_loc": {"remove": [], "add": []}, 
                "en_passant_target": None, 
                "castling_rights": [], 
                "kings": None})

        self.changes[-1]['last_move'] = fromto

        # setting up local variables
        from_y, from_x = fromto[0][0], fromto[0][1]
        to_y, to_x = fromto[1][0], fromto[1][1]
        promote = None if len(fromto) == 2 else fromto[2]
        squares = []
        capture = False if self.board[to_y][to_x].piece == NO_PIECE else True
        moved_piece = self.board[from_y][from_x]

        # special case of en passant, where we need to update a square that is not directly visible in the fromto variable
        self.changes[-1]['en_passant_target'] = self.en_passant_target
        if moved_piece.piece == PAWN:
            if (to_y, to_x) == self.en_passant_target:
                # clear the pawn that was taken en passant from the board and append squares
                sq_clear_y = 3 if self.en_passant_target[0] == 2 else 4
                sq_clear_x = self.en_passant_target[1]

                self.changes[-1]['board'].append((sq_clear_y,sq_clear_x,self.board[sq_clear_y][sq_clear_x]))
                self.board[sq_clear_y][sq_clear_x] = Piece()
                
                self.changes[-1]['piece_loc']['add'].append((OPPOSITE[moved_piece.color],(sq_clear_y,sq_clear_x)))

                self.piece_loc[OPPOSITE[moved_piece.color]].remove((sq_clear_y,sq_clear_x))

                squares.append((sq_clear_y, sq_clear_x))
                capture = True
                
                self.en_passant_target = "-"
            else:
                # update en passant target
                self.update_en_passant(moved_piece, fromto)
        else:
            self.en_passant_target = "-"

        # special case castling, which is 2 moves in one, we process the rookmove first in a recursion layer and then proceed with the kingmove as a normal move. note we only need the squares of the rookmove as return value, the other 2 variables are unimportant at this step
        if moved_piece.piece == KING:
            if fromto in CASTLE['rookmove']:
                sq_rookmove, _, _ = self.move(CASTLE['rookmove'][fromto], backup=False)
                squares.extend(sq_rookmove)
                
                # re-updating the last move to be the kings move instead of the rooks move
                self.changes[-1]['last_move'] = fromto
            
            self.update_kings(moved_piece, fromto)

            for right in self.castling_rights[moved_piece.color]:
                self.changes[-1]['castling_rights'].append((moved_piece.color,right))
            self.castling_rights[moved_piece.color] = []            

        # updating castling rights, depending on which rook was moved or if a rook was captured
        elif moved_piece.piece == ROOK or capture:
            self.update_castling(moved_piece, fromto, capture)

        # updating the from-square and the to-square, creating a new Piece object if we promote
        self.changes[-1]['board'].append((to_y,to_x,self.board[to_y][to_x]))
        self.board[to_y][to_x] = moved_piece if not promote else Piece(promote)
        self.changes[-1]['board'].append((from_y,from_x,self.board[from_y][from_x]))
        self.board[from_y][from_x] = Piece()

        self.changes[-1]['piece_loc']['remove'].append((moved_piece.color,(to_y,to_x)))
        self.piece_loc[moved_piece.color].add((to_y,to_x))
        
        if (to_y,to_x) in self.piece_loc[OPPOSITE[moved_piece.color]]:
            self.changes[-1]['piece_loc']['add'].append((OPPOSITE[moved_piece.color],(to_y,to_x)))
            self.piece_loc[OPPOSITE[moved_piece.color]].remove((to_y,to_x))
        
        self.changes[-1]['piece_loc']['add'].append((moved_piece.color,(from_y,from_x)))
        self.piece_loc[moved_piece.color].remove((from_y,from_x))

        # returning a list of squares that have been updated by this function
        squares.extend([(from_y, from_x), (to_y, to_x)])
        return (squares, capture, moved_piece)

    # this function first updates the board variables and then checks if any game over conditions have been met
    def commit(self, fromto, capture, moved_piece):

        # when committing a move, it makes sense to update this variable, as it is the basis for the  calculation of next moves
        self.update_reachable(moved_piece.color)

        to_y, to_x = fromto[1][0], fromto[1][1]
        
        self.changes[-1]['half_moves'] = self.half_moves
        if capture or moved_piece.piece == PAWN:
            self.half_moves = 0
        else:
            self.half_moves += 1
        
        if moved_piece.color == BLACK:
            self.changes[-1]['full_moves'] = self.full_moves
            self.full_moves += 1

        # changing who is to move at last
        self.to_move, self.opponent = self.opponent, self.to_move

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
    def commit_move(self, fromto):
        # executing the move
        sqlist, capture, moved_piece = self.move(fromto)
        # updating global game variables
        self.commit(fromto, capture, moved_piece)

        # passing the list of updated squares from the move function
        return sqlist

    # takes a snapshot of the board and the pieces, but NOT the according objects. this is to prevent the threefold repetition rule not triggering if pieces (e.g. 2 knights) are interchanged, which results in the same position on the board, but would not trigger a positive comparison of 2 snapshots, as the 2 knights are represented by different objects. note that it would also be possible and more efficient to do this via the zobrist hash that we use for the bot module, but for now lets keep it as is.
    def snapshot(self):
        return tuple(tuple(str(sq) for sq in row) for row in self.board)

    # updating the kings position, depending on which color king was moved and where
    def update_kings(self, moved_piece, fromto):
        new_y, new_x = fromto[1][0], fromto[1][1]
        self.changes[-1]['kings'] = (moved_piece.color,self.kings[moved_piece.color])
        self.kings[moved_piece.color] = (new_y,new_x)

    # updating the possible en passant square, depending on which pawn moved and where
    def update_en_passant(self, moved_piece, fromto):
        from_rank, to_rank, col = fromto[0][0], fromto[1][0], fromto[0][1]
        
        if to_rank == EN_PASSANT[moved_piece.color]['to_rank'] and from_rank == EN_PASSANT[moved_piece.color]['from_rank']:
            self.en_passant_target = (EN_PASSANT[moved_piece.color]['target'], col)
        else:
            self.en_passant_target = "-"

    # updating the castling rights (ONLY called if a rook moves or is captured, because king move sets the castling rights to zero always and does not need a function to handle)
    def update_castling(self, moved_piece, fromto, capture):
        from_sq, to_sq = fromto[0], fromto[1]
        
        # in case a piece is moved from one original rook square (must be a rook the first time this happens)
        if from_sq in CASTLE['rights']:
            if CASTLE['rights'][from_sq] in self.castling_rights[moved_piece.color]:
                self.changes[-1]['castling_rights'].append((moved_piece.color,CASTLE['rights'][from_sq]))
                self.castling_rights[moved_piece.color].remove(CASTLE['rights'][from_sq])
        
        # in case a piece is captured on one original rook square (must be a rook the first time this happens)
        if capture:
            if to_sq in CASTLE['rights']:
                if CASTLE['rights'][to_sq] in self.castling_rights[OPPOSITE[moved_piece.color]]:
                    self.changes[-1]['castling_rights'].append((OPPOSITE[moved_piece.color],CASTLE['rights'][to_sq]))
                    self.castling_rights[OPPOSITE[moved_piece.color]].remove(CASTLE['rights'][to_sq])  

    # this function keeps track of what the opponent can do on the board. it gives back a dict that is divided into a part that includes all directly reachable squares (by reachable it means takeable here) and a second part that checks if there are lines towards the king, that are currently blocked by enemy pieces. that way we can easily access this information to check if a move we want to make is legal or would result in our king standing in check
    def update_reachable(self, color):

        self.changes[-1]['reachable'] = (color, self.reachable[color])
        self.reachable[color] = {"all_direct": set(), "king_indirect_blocked": set(), "pawn_attack": set()}

        for y,x in self.piece_loc[color]:
            f = self.board[y][x]

            # calculating all pieces except pawns
            if not f.piece == PAWN:
                pattern = f.move_pattern()
                for direction in pattern:
                    blocking_piece = None
                    for offset in direction:
                        new_field = (y+offset[0],x+offset[1])
                        
                        if not blocking_piece:
                            
                            # new field out of bounds
                            if new_field not in VALID_SQUARES:
                                break
                            # new field is empty and therefore a valid target field
                            elif self.board[new_field[0]][new_field[1]].piece == NO_PIECE:
                                self.reachable[color]['all_direct'].add(new_field)
                            # new field occupied by own piece, break this direction early, but add, since that means protecting the piece
                            elif self.board[new_field[0]][new_field[1]].color == color:
                                self.reachable[color]['all_direct'].add(new_field)
                                break
                            # new field occupied by opponents piece, allow this move (to capture) and then see if the fields behind the blocking piece are the opponents king location
                            elif self.board[new_field[0]][new_field[1]].color == OPPOSITE[color]:
                                self.reachable[color]['all_direct'].add(new_field)
                                blocking_piece = new_field
                        else:
                            # new field out of bounds
                            if new_field not in VALID_SQUARES:
                                break
                            # new field is empty, continue looking
                            elif self.board[new_field[0]][new_field[1]].piece == NO_PIECE:
                                continue
                            # new field occupied by own piece, break this direction early
                            elif self.board[new_field[0]][new_field[1]].color == color:
                                break
                            # found the enemy king, this means a piece has a line towards the king that is blocked by the blocking_piece, which we therefore add to the dict and break
                            elif self.board[new_field[0]][new_field[1]].content == OPPOSITE[color]+KING:
                                self.reachable[color]['king_indirect_blocked'].add(blocking_piece)
                                break
                            # in all other cases, e.g. finding another enemy piece, we break without adding anything to the dict
                            else:
                                break                       

            
            # calculating pawns separately because they have special move rules
            else:

                # only pawn captures need to be considered, as this is about seeing if we can beat the king
                pattern = f.move_pattern()['capture']
                for direction in pattern:
                    for offset in direction:
                        new_field = (y+offset[0],x+offset[1]) if color == WHITE else (y-offset[0],x-offset[1])
                        
                        # checking for out of bounds, which is possible with sideways capture
                        if new_field not in VALID_SQUARES:
                            break
                        # new field is occupied by an enemy or own piece or empty and therefore a valid target field
                        else:
                            self.reachable[color]['all_direct'].add(new_field)
                            self.reachable[color]['pawn_attack'].add(new_field)
                            break

    # simply returning if the king of the current player is standing in check
    def update_in_check(self):
        self.changes[-1]['in_check'] = self.in_check
        self.in_check = True if self.kings[self.to_move] in self.reachable[self.opponent]['all_direct'] else False

    # draw by insufficient material if both sides have no more than the following: k, k+b, k+n, in all other cases, the game will continue
    def check_insufficient(self):
        pieces = defaultdict(int)
        for v in self.piece_loc.values():
            for y,x in v:
                f = self.board[y][x]
                # if we see a rook, queen or pawn, we terminate early
                if f.piece == PAWN or f.piece == ROOK or f.piece == QUEEN:
                    return
                # counting pieces for each color
                pieces[f.content] += 1
        
        # checking the conditions after counting pieces and updating the game_over variable if necessary
        if pieces[WBISHOP]+pieces[WKNIGHT] < 2 and pieces[BBISHOP]+pieces[BKNIGHT] < 2:
            self.gameover = (0.5, "draw_insufficient")

    # keeping track of the current position and checking if it has already occured 2 times before. if a pawn is moved or a piece is captured, that means the position can never be the same, so all tracked positions are forgotten to prevent the tracking dict from growing too large
    def check_threefold(self, capture, moved_piece):
        if not capture and not moved_piece.piece == PAWN:
            snap = self.snapshot()
            self.changes[-1]['threefold'] = (SUBTRACT,snap)
            self.threefold[snap] += 1
            
            if self.threefold[snap] > 2:
                self.gameover = (0.5, "draw_threefold")
        else:
            self.changes[-1]['threefold'] = (REPLACE,self.threefold)
            self.threefold = defaultdict(int)

    # instead of backing up and restoring the whole board, we are appending change data to the changes variable. this function takes advantage of that and reverses all the changes that were made during the execution of a move, resulting in the undoing of that move. note that this function distinguishes between a move that was simulated ("move") or commited ("commit_move"). the undoing of moves via this function instead of backing up and restoring is only slightly faster, because we modify the changes data with every move. however, we gain the advantage of being able to take back unlimited moves in a row which was not possible with the backup method unless we stored multiple board backups
    def undo_move(self, commited=False):
        
        # getting the current moves change data
        change = self.changes.pop()
        
        # reversing all changes, depending on which key is given in the data. this works for different lengths, so the change data does not need to contain all keys every time
        for key, value in change.items():
            key_map = CHANGES_KEYS[key]
            if key_map == BOARD:
                for t in value:
                    y,x,old_piece = t
                    self.board[y][x] = old_piece
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

        # the reason for the distinguishment between a simulated and a committed move is, that in a simulated move, the player that is to move stays the same, whereas in a committed move it switches 
        if commited:
            # no fancy backup necessary, just switch back
            self.to_move, self.opponent = self.opponent, self.to_move

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
            print(len(self.pseudo_legal_moves(self.to_move))) # pseudo legal moves for own board
            print([move2uci(move) for move in self.pseudo_legal_moves(self.to_move)])
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

    # printing the board mainly for quick testing and debugging. a proper graphical interface is implemented separately
    def __str__(self):
        output = '\n'
        
        # need to reverse the board for printing or else it would be white against us, deviating from chess standard display
        for i, rank in enumerate(self.board[::-1]):
            str1 = ' '.join(f'{x}' for x in rank)
            # adding indices for easy reference
            output += "76543210"[i] + " | " + str1 + '\n'
        output += '--+----------------' + '\n' + "  | 0 1 2 3 4 5 6 7" + '\n'
        
        return output


class Piece:

    # we have multiple options for finding out what piece we are dealing with. if we just want to know the color, we access color, if we just want to know the type of piece, we access piece, but if we want to know specifically that it is e.g. a black knight, then we access content
    def __init__(self, code=None):
        if code:
            self.content = PIECE_INIT[code]
            self.color = BLACK if self.content >= 16 else WHITE
            self.piece = self.content - self.color
        else:
            # assigning 0 to color which is neither black nor white, so that we can check for it, even if the square is empty. note that we should never check by inequality (!=), because there are 3 options for the color and this will lead to bugs
            self.color = 0
            self.content = NO_PIECE
            self.piece = NO_PIECE
            
    # this method returns all possible move offsets (regardless of piece position) for the current piece. the offsets will be converted in a potential target field in the Board class
    def move_pattern(self):
        return PIECE_MOVEMENT_PATTERNS[self.piece]

    def __str__(self):
        return PIECE_STR[self.content]


if __name__ == "__main__":

    cProfile.run('test_module()')

