#!/usr/bin/env python3

import chess_v4 as my_chess
import chess_GUI_v2 as my_gui
import chess_bot_v3 as my_bot


if __name__ == "__main__":

    # FEN format example
    # "8/4r3/2k5/8/8/3K4/8/8 w - - 0 1"

    g = my_gui.Game()
    g.game_from_FEN(my_chess.FEN_START, my_chess.WHITE)

