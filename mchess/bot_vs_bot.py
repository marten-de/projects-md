# a script that allows to pitch 2 bots against each other and gives back their match results

import chess_v3 as my_chess


# put in two different bot versions here to let them play against each other
#import chess_bot_v1 as my_bot1
import chess_bot_v2 as my_bot2

THINKING_TIME_STANDARD = 3

# note that in this version, it must always be white to move. if more positions should be tested, it would be feasible to put them in a json file, but for now the matches run very slowly, so 8 FENs are enough.
TEST_POSITIONS = ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "r3r2k/1pp3pp/pn1b1p2/7b/P2P4/2NBB2P/1P3PP1/R3R1K1 w - - 3 19",
                "2r2rk1/pp3pp1/1b6/3p2p1/BP1P4/P7/5PPP/2RR2K1 w - - 4 21",
                "2rq1knr/pp1n1ppp/4p3/1B1pP3/P2pb1P1/1P3N1P/2PN1P2/R2QK2R w KQ - 2 13",
                "r2qk2r/ppbnn1pp/2p2pb1/4p3/4P1P1/5N1P/PPPNQPBB/R3K2R w KQkq - 3 13",
                "r2q1rk1/pp3ppp/2n2n2/2bp4/6b1/P1N1PN2/1P2BPPP/R1BQK2R w KQ - 3 10",
                "rnbq1rk1/pp2bpp1/4p2p/2pn4/3P3B/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 9",
                "k6r/pp2q3/1r2bp1n/3pB1pp/2pP4/P1P4P/RP1N1PP1/3QR1K1 w - - 0 25"]

# this function starts a match between 2 bot instances from a custom FEN (needs to be white to move!) and gives back the match end result. setting the thinking time can be used to see if a bot gets disproportionally stronger/ weaker with more/ less time
def bot_match(fen, thinking_time=THINKING_TIME_STANDARD, player1=my_chess.WHITE):
    
    # setting up the board
    b = my_chess.Board()
    b.load_FEN(fen)

    # loading the board into 2 bot instances
    p1 = my_bot1.Chessbot(b, thinking_time=thinking_time)
    p2 = my_bot2.Chessbot(b, thinking_time=thinking_time)

    # setting the bot that will make the first move. if we want to allow FENs with black to move, then this line would need to be adjusted
    p = p1 if player1 == my_chess.WHITE else p2
    
    # running the match in a loop, switching the bot that is to move after each move
    while not b.gameover:
        b.commit_move(p.search())
        p = p1 if p==p2 else p2

    # creating the match result
    p1win, p2win, draw = 0,0,0
    if b.gameover[0] == 0.5:
        draw = 1
    elif b.gameover[0] == 1:
        if player1 == my_chess.WHITE:
            p1win = 1
        else:
            p2win = 1
    elif b.gameover[0] == 0:
        if player1 == my_chess.WHITE:
            p2win = 1
        else:
            p1win = 1

    return (p1win, p2win, draw)

# a function that runs matches for a list of FENs, for a specified number of matches per FEN. note that only even numbers should be chosen, otherwise one of the 2 bots will have the white color more often, which will bias the result in its favor
def bot_tournament(positions, matchcount=2, thinking_time=THINKING_TIME_STANDARD):
    
    results = {"p1win": 0, "p2win": 0, "draw": 0}

    for fen in TEST_POSITIONS:

        # setting the color that player1 bot will have in the beginning
        color1 = my_chess.WHITE
        for i in range(matchcount):

            p1win,p2win,draw = bot_match(fen,thinking_time,player1=color1)
            
            # documenting the results after the match
            results['p1win'] += p1win
            results['p2win'] += p2win
            results['draw'] += draw

            print(results)

            # switching colors for next match
            color1 = my_chess.BLACK if color1 == my_chess.WHITE else my_chess.WHITE

    return results


if __name__ == "__main__":

    final_results = bot_tournament(TEST_POSITIONS,matchcount=8)
    print(final_results)


