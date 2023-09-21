# initial version of the GUI for the custom chess class, can only handle the game display itself so far

import PySimpleGUI as sg
import os

import chess_v3 as my_chess
import chess_bot_v2 as my_bot


"""HELPER FUNCTIONS"""
# region

# removes the dotted line around a pysimpleGUI button when it is selected
def block_focus(window):
    for key in window.key_dict:
        element = window[key]
        if isinstance(element, sg.Button):
            element.block_focus()

# endregion


"""CONSTANTS"""
# region

ABS_DIR_PATH = os.path.dirname(__file__)

IMAGE_PATH = os.path.join(ABS_DIR_PATH, "images/45px")

BPAWN_PATH = os.path.join(IMAGE_PATH, "bpawn.png")
WPAWN_PATH = os.path.join(IMAGE_PATH, "wpawn.png")
BKING_PATH = os.path.join(IMAGE_PATH, "bking.png")
WKING_PATH = os.path.join(IMAGE_PATH, "wking.png")
BQUEEN_PATH = os.path.join(IMAGE_PATH, "bqueen.png")
WQUEEN_PATH = os.path.join(IMAGE_PATH, "wqueen.png")
BKNIGHT_PATH = os.path.join(IMAGE_PATH, "bknight.png")
WKNIGHT_PATH = os.path.join(IMAGE_PATH, "wknight.png")
BROOK_PATH = os.path.join(IMAGE_PATH, "brook.png")
WROOK_PATH = os.path.join(IMAGE_PATH, "wrook.png")
BBISHOP_PATH = os.path.join(IMAGE_PATH, "bbishop.png")
WBISHOP_PATH = os.path.join(IMAGE_PATH, "wbishop.png")
NO_PIECE_PATH = os.path.join(IMAGE_PATH, "blank.png")

# lookup for the GUI to connect the piece integer code from the chess module with the according image path
PIECE_TILES = {my_chess.BPAWN: BPAWN_PATH, my_chess.WPAWN: WPAWN_PATH, my_chess.BKING: BKING_PATH, my_chess.WKING: WKING_PATH, my_chess.BQUEEN: BQUEEN_PATH, my_chess.WQUEEN: WQUEEN_PATH, my_chess.BKNIGHT: BKNIGHT_PATH, my_chess.WKNIGHT: WKNIGHT_PATH, my_chess.BROOK: BROOK_PATH, my_chess.WROOK: WROOK_PATH, my_chess.BBISHOP: BBISHOP_PATH, my_chess.WBISHOP: WBISHOP_PATH, my_chess.NO_PIECE: NO_PIECE_PATH}

# colors can be changed here, use pysimpleGUI colors
BOARD_COLORS = {"light": "burlywood3", "dark": "sienna4"}

# lookup for graphical board generation
BOARD_TILES = [[BOARD_COLORS['light'] if (x+y)%2 != 0 else BOARD_COLORS['dark'] for x in range(8)] for y in range(8)]

# lookup to handle everything related to special move promotion
PROMOTE = {
    "tiles": {my_chess.WHITE: [WQUEEN_PATH, WROOK_PATH, WBISHOP_PATH, WKNIGHT_PATH],
            my_chess.BLACK: [BQUEEN_PATH, BROOK_PATH, BBISHOP_PATH, BKNIGHT_PATH]},
    "keys": {WQUEEN_PATH: "Q", WROOK_PATH: "R", WBISHOP_PATH: "B", WKNIGHT_PATH: "N",
            BQUEEN_PATH: "q", BROOK_PATH: "r", BBISHOP_PATH: "b", BKNIGHT_PATH: "n"}}

# endregion


class Game:

    # setting up a game by creating a new empty board instance and a bot instance
    def __init__(self):
        self.bc = my_chess.Board()
        self.bot = my_bot.Chessbot(self.bc)
    
    # this function creates the window layout for pysimpleGUI by looking at the pieces on the board. each square is represented by a button, and if there is a piece on the square, it is loaded with the appropriate png image
    def setup_graphical_board(self):
        return [[sg.Button(border_width=0, image_filename=PIECE_TILES[self.bc.board[row][col].content], pad=(0,0), key=(row,col), button_color=(BOARD_TILES[row][col],)*2) for col in range(8)] for row in range(7,-1,-1)]

    # starting a game from the chess starting position
    def new_game(self, player_color):
        self.player_color = player_color
        self.bc.new_game()
        self.game_loop()

    # loading a custom FEN
    def game_from_FEN(self, fen, player_color):
        self.player_color = player_color
        self.bc.load_FEN(fen)
        self.game_loop()

    # this is the main function that runs as long as the game continues. it shows the graphical representation of the Board instance and allows the user to make moves by clicking
    def game_loop(self):

        # initial setup of the game window
        board_layout = self.setup_graphical_board()
        self.w = sg.Window("Board", location=(500,0), layout=board_layout, margins=(25,25), finalize=True)

        # blocking dotted lines around selected buttons
        block_focus(self.w)

        # setting up a variable that can buffer a clicked button key. this is necessary because a move requires 2 clicks by the user (from -> to)
        selected = None
        
        # the main loop for the game
        while True:
            
            # window is freezed once game over
            if self.bc.gameover:
                event, value = self.w.read()
                if event == sg.WIN_CLOSED:
                    break                

            # human player to move, waiting for input
            elif self.bc.to_move == self.player_color:
                event, value = self.w.read()
                if event == sg.WIN_CLOSED:
                    break
                elif event:
                    if selected:
                        # de-selection if the same square is selected twice in a row
                        if selected == event:
                            selected = None
                        else:
                            # making a move if possible, then updating the GUI, then resetting the selection. note that we have a special case of a move which can promote a pawn. to get this working we need to distinguish between normal and promotion moves and get a user input mid-game for the promotion move
                            normal_moves, promote_moves = self.bc.split_legal_moves()
                            
                            if (selected, event) in normal_moves:
                                new_move = (selected, event)
                                sqlist = self.bc.commit_move(new_move)
                                self.update_squares(sqlist)
                                selected = None
                            
                            elif (selected, event) in [(from_sq, to_sq) for (from_sq, to_sq, _) in promote_moves]:
                                promote = self.popup_promotion()
                                
                                # if no promotion is chosen, no move is executed
                                if promote:
                                    new_move = (selected, event, promote)
                                    sqlist = self.bc.commit_move(new_move)
                                    self.update_squares(sqlist)
                                    selected = None
                                else:
                                    selected = None

                            # TODO can still play after gameover, need to implement some stopping mechanism in the GUI
                            if self.bc.gameover:
                                print(f"gameover: {self.bc.gameover}")

                            
                            # changing the selection in case one own piece is selected after one own piece already being in the selection variable
                            else:
                                sq = self.bc.board[event[0]][event[1]]
                                selected = event if sq.color == self.bc.to_move else None

                    # no square yet selected means we just set variable selected to that square
                    else:
                        selected = event
            
            # bot to move
            else:
                bot_move = self.bot.search()
                if bot_move:
                    sqlist = self.bc.commit_move(bot_move)
                    self.update_squares(sqlist)

        self.w.close()

    # each time after a move is made, the pieces on the board change positions. this function loops over the squares that have been affected and updates the respective elements in the GUI
    def update_squares(self, sqlist):
        for sq in sqlist:
            val = self.bc.board[sq[0]][sq[1]]
            self.w[sq].update(image_filename=PIECE_TILES[val.content])
        self.w.refresh()

    # this function gets additional user input in case a promotion move is made and returns the choice
    def popup_promotion(self):

        # creating a new layout for the popup window
        layout = [[sg.Button(border_width=0, image_filename=tile, pad=(0,0), key=PROMOTE['keys'][tile], button_color=("#64778d",)*2) for tile in PROMOTE['tiles'][self.bc.to_move]]]
        
        # the popup window will block interaction with the game window until a choice is made, or the window is closed
        window = sg.Window("Promote to?", layout, use_default_focus=False, finalize=True, modal=True, location=(650, 250))
        
        # deactivating dotted lines around selected buttons
        block_focus(window)
        
        # only one time reading, after the choice is made, the window closes and the game goes on. if the window is manually closed, it counts as no choice being made
        event, values = window.read()
        window.close()
        return None if sg.WIN_CLOSED else event


if __name__ == "__main__":

    g = Game()
    g.new_game(my_chess.WHITE)
    #g.game_from_FEN("8/4k3/8/1R6/R7/3K4/8/8 w - - 0 1", my_chess.WHITE)


