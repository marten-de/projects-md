# "mchess" - A Custom Chess Module Incl. Bot/ Engine and GUI for Python
<br />

### Introduction:

The goal of this project is to program a playable chess game in Python. It will include a chess module that represents the game mechanics (1st part), a simple GUI that allows a human to play (2nd part), and a bot/ engine that will play as the opponent (3rd part). My main objective is to learn as much as I can by working on this project. That means I will program everything from scratch and I will only ever use existing chess packages (such as Python's chess module) for debugging my own code, but I won't include them in any of my program's functionalities, nor will I knowingly copy details of their implementation. I am mostly interested in finding out how strong the bot can become, so the focus will be on that part, with the chess module and the GUI being only prerequisites. Note that this project is not meant as a serious alternative to current chess games and/ or websites, it is inferior to those and should only be viewed as an experiment of how far Python can take me in a few week's programming time.

### Quick Start Guide

Python3 needs to be already installed on your system and your system must know its path. Updating the PATH if that is not the case will differ depending on your system, so I can't describe it here.

All modules used by this project also need to be installed. If you don't already have them, you can run the following code from the console while in the mchess directory:

```
pip install -r requirements.txt
```

To start the game, run the following command from the console: (Depending on your system you might need to use "python" instead of "python3")

```
python3 main.py
```

A game where you play as white will start, the bot will play black in this case. Once the game ends, a message about the result will be printed to the console (not the GUI) and no further action will be possible in the GUI. So just close the window and re-launch "main.py" for another game!

If you want to play as black, you need to change the parameter "my_chess.WHITE" to "my_chess.BLACK" in the main function. Note that this is not recommended in the current version, because the board display can not be flipped yet.

If you want to play from a position other than the standard chess starting position, you need to replace the parameter "my_chess.FEN_START" with a custom FEN as string. Note that it must be a full FEN, with 6 parts (containing information about who is to move, castling rights, etc.), not the short form with only 1 part.

### Acknowledgements

The idea for this project came from a two-part Youtube series by Sebastian Lague, called "Coding Adventure", in which he creates a similar (though much better) program in C#:

Part1: https://www.youtube.com/watch?v=U4ogK0MIzqk
Part2: https://www.youtube.com/watch?v=_vqlIPDR2TU

I got a lot of inspiration from these videos (especially the first part), and even though my implementation deviates from Sebastian's approach on many of occasions, the step-by-step explanations he gives were a huge help to me in getting this project going.

I also used a collection of chess positions that was collected by Peter Jones for debugging my module:

https://gist.github.com/peterellisjones/8c46c28141c162d1d8a0f0badbc9cff9

Without these helpful positions, it would have taken me much more time to find and correct bugs in my module.

The piece tiles I use for the GUI have been created by Colin M.L. Burnett (Cburnett) and are available here:

https://en.wikipedia.org/wiki/User:Cburnett/GFDL_images/Chess

Lastly, I used opening data that was assembled by Lichess, and puzzle data which is available on the Lichess database:

https://github.com/lichess-org/chess-openings
https://database.lichess.org/#puzzles

### How Does mchess Work?

I try to annotate my code well, so I am only giving a brief overview here. If you are interested in the details of a particular function or feature, please check it in the Python files directly.

The main part of the project is the chess module. It is programmed as a board class and a piece class. The piece class holds information about what type of piece (and color) it is, and all the other information (such as which piece is standing where on the board, whose turn it is, is the king standing in check, etc.) is held by the board class.

The board is represented by a 2d-array, and each square points to a piece instance, even those that don't hold a piece. The representation of a given chess position like that is easy, and the loading of a position by custom FEN (as can be output e.g. by Lichess board editor) is not a problem. The first challenge is to find out which moves can be played in a position. To do that, a loop goes through all the pieces of the player that is to move, accesses their movement patterns, and then sees if those moves can be played on the board. Multiple cases need to be considered here, such as squares occupied by enemy or own pieces, out of bounds (not on the board any more). Also, chess has special moves, namely En Passant and Castles, which come with their own prerequisites and consequences and were responsible for a major amount of bugs in development, because they need an extensive amount of properly sequenced conditions to handle them correctly.

Once these moves are found, we are not done. The playable moves on the board are only pseudo-legal, because any move that is playable, could potentially result in a position that puts the own king in check, which is illegal in chess. That means, the list of pseudo-legal moves need to be reduced by those moves that would put the king in check, and the most straightforward way to find out which moves those are, is to simulate them all (move -> take back). At this point it becomes clear, why the program does so many calculations and ends up being slow.

Another part of the board class, is that it constantly  maintains important game variables. One example is the threefold repetition rule in chess, which says that if the exact same board position is reached for the third time, the game will be a draw. To check this, the board class needs to keep track of the previously reached board positions in an efficient way. There are many more game variables that need to be tracked in order to keep within the rules of chess.

The next part of the project is the GUI. It is a game class that uses Python's module PySimpleGUI and really just does the bare minimum that is needed to interact with the program. The class creates a graphical board representation from the board class as an input and then displays this representation in a game loop, that can take in mouse click inputs from the user and updates the graphical board if a legal move was made. The game loop contains interactions with the board class to see if an attempted move is legal, and only commits that move if it is. It also lets one of the two sides be played by the bot, which is yet another separate class.

The bot class is the most interesting part of the project. It takes in a board class instance and then its task is to find the best (or at least a good) move in the current position. To find this move, a variety of techniques are used. First, the bot needs to be able to judge a position, that means it must understand if the black or white color are "better" in this position.

The evaluation consists of several factors, such as how many (and which) pieces does each side have, where are they positioned, and so on. This is challenging, and most likely the evaluation will differ from very strong chess engines such as stockfish.

Once the bot is capable of evaluation, it can use a recursive tree search, meaning it can simulate a move, and then look at all the opponent's responses from the resulting position. This can go on and on, in the case of my bot usually until it reaches a depth of 6-7 moves. The search algorithm itself employs alpha-beta-pruning, a technique that discards tree branches, as soon as it becomes clear that this branch will never be reached, because of a strong reply that the opponent could play. The idea of this technique is to profit from a pre-ordering of moves: If we went through a list of moves ordered from best to worst, then only the first move would be fully evaluated. All other moves would be discarded right after the first recursion, saving a large amount of time.

Of course the quality of moves is not known in advance, so the bot class uses certain parameters to guess which move could be good. One example would be, if a high-value piece such as the queen could be captured by a low-value piece such as a pawn. If the guessed move order is good, the following calculation effort in the tree search will be reduced by a lot.

The bot class contains various other methods to generate moves, such as an opening database for the first 5-10 moves, for which it will play a random move from a valid opening. This is reasonable, as openings in chess are well researched, and a calculation with tree search from the starting position is almost pointless, as it would require a very high depth of 20-30 moves to come up with a reasonable move. This depth is not attainable for the bot at the current stage. The opening database on the other hand allows for an instant move through lookup (in case the position is found).

Lastly, I also included an unrelated script "bot_vs_bot.py" in this repository, because it could be useful at some later stage. It pitches two bot instances against each other and gives back their match results. Whenever I make major changes in the bot class, I will use this script to let the new version play against the old version, and judge if it has improved or if I might have introduced bugs that make it play worse than before.

### Limits of mchess

The main weakness of the bot so far is speed. Especially compared to the inspiration for my project that was written in C#, the speed difference becomes very obvious. The playing strength of a chess bot comes from being able to calculate many moves deep, and so far my bot can only reasonably use a depth of 7-8 moves without taking an unreasonable amount of time. This is of course due to Python being an interpreted language. I think I can still optimize my code "in-Python" at some areas, but in the end it also means I need to find a way to bypass Python's weakness by using special extension modules such as NumPy, Cython, etc. or even writing my own extension in C. This will be one of the major next steps in this project. Note that it will affect both the bot as well as the chess module, because the slow speed of the bot originates in part from the slow move calculation of the chess module.

Another weakness is the reliance of the bot on human experience. So far, many of the evaluation factors that the bot uses as parameters to judge a certain board position, are given by me. I only have average playing strength, so this is certainly not ideal, but at least I can rely on extensive research in this field. However, even if I was a strong player, it would still not be clear if the parameters combine well, or if they would need to be tweaked in order to become more reasonable. This would need to be tested with massive simulations and different sets of parameters. It is certainly doable, but simulating a lot of games needs speed, so the previously given weakness needs to be addressed first. Another idea would be to try and eliminate the human factor completely by using a deep learning approach. This is something that I want to try in the future, especially to see how this AI-bot would compare against the algorithm-based (conventional) bot.

Lastly, I suspect that the issues given in the previous paragraph lead to some unpredictable behavior of the bot. This could explain the massive spread in puzzle performance: The bot is able to solve very hard puzzles of almost 2800 rating, but at the same time it fails some extremely easy puzzles of below 500 rating. I didn't look into this issue closely yet, it could also be possible that the bot finds a strong move in those positions, but since it is not the absolute best move (as found by stockfish engine), it is rejected and the puzzle counts as failed. This is more likely for easy puzzles, since very hard puzzles usually only have 1 good move, with all of the other moves being much worse. However, random unexplainable blunders also happened during game testing, and this is more concerning. It will be one of the next issues that I need to address.

### Developing Process:

In this chapter I will shortly explain some of the challenges that I encountered during the programming and how I solved them.

Even though it is not necessary for the function of the chess class, I included a way to dump the current board position to the console (ASCII representation). This proved to be very valuable for testing functions such as making or undoing a move and I relied upon this all the way through the development of the module.

However, testing for all possible errors manually is of course unfeasible and I would most likely forget many cases, so I included a function that goes through every possible move combination of a position, up to a specified depth, and counts these combinations. The result is then compared with the result that the already existent Python chess module would come up with. If the numbers match, great, and if not, I let the program print the board configuration incl. possible moves and other data internal to my module, to narrow down at which point the deviation happens. It was important to not just test the starting position, as many special cases can not arise at this early stage of the game. Instead, I used a collection of custom positions to cover a large number of cases and debugged until each of them could be processed correctly. Many times, bugs were related to the special move castles (which is implemented as 2 consecutive moves) or en passant (which affects 3 squares instead of 2 in case of a normal move). Lastly, the mechanic of taking moves back, which was first introduced as a simple backup->restore and then later refined to an "undo" function, also proved to be tricky, and I encountered many cases in which the board position was not properly reset and then the computer would attempt a move with a piece that was no longer there, leading to unrelated errors that had nothing to do with the underlying cause and were more difficult to track down.

Generally, v1 was the version that I just wanted to get working, I didn't care about speed yet. But when I adjusted the code to run faster, I had to introduce more and more special cases to discard calculations that would not be needed, and this made the code much more complicated to understand and to debug. With help of the above mentioned method however, I managed to track down all the bugs and speed up the runtime by a factor of 10x (judged on a single testcase 30s -> 3s). 

I decided which part of the code to focus on, by using cProfile, which gave me the runtime for each function and also how often that function was called. Here I saw that especially the search for pseudo-legal moves, then legal moves, and finally the initial backup-restore mechanic took a lot of runtime. There were also minor issues such as string comparisons and use of lower() or upper() method, which didn't take a lot of time, but were unnecessary, so I improved those as well and changed all comparisons to be with integers instead.

One of the major changes that I made to improve the class speed, was change the piece finding function from a loop over the whole board (64 squares) to a loop over a dict that held all the piece positions. Of course the additional challenge is to keep this dict constantly up to date, but after the implementation was complete, this gave a noticeable speed boost.

Another change concerned the legal move generation. In v1, all pseudo-legal moves would be simulated and then for each move I would find the list of pseudo-legal moves that the opponent could play, and then see if the own king's position square was in that list. If yes, that means this move was illegal and can not be appended to the list of legal moves. Here I implemented 2 different improvements. First, I am keeping a dict that holds all squares reachable by the opponent, and can just check if a king move would end on any of the squares contained in that dict (-> illegal move). This is not feasible for all moves, e.g. if not the king itself is moved, but rather a piece that was blocking a check, then this would also put our own king in check. To check for this, the dict also keeps track of "blocking pieces" and if such a scenario occurs, the move is simulated anyway. But instead of finding the whole list of the opponent's responses, the search will terminate early if the king can be captured, potentially saving a lot of non-needed computation work.

Lastly, the initial mechanic of taking back moves was solved by backing up the relevant variables of the board, then playing the move, and then resetting the board to the backed up state to undo the move. This approach is straightforward, but takes a lot of time, since some game variables are not simple integers, but multi-dimensional arrays of objects that need to be deepcopied, in order for the backup to be unchangable by future moves. These deepcopies are bad for performance, so I tried to find a way of maintaining the game variables, updating them if a move happened, and then simply doing the changes backwards to take that move back. This is done by using a special changes dict, that stores a way how to take each move back without needing deepcopies. The problem is, that the creation of this entry in the dict for each move, is also rather slow. I ended up with a minor performance improvement over the backup->restore mechanic, and so I kept it. Another advantage is, that with this new mechanic, all moves can be taken back in a row. Previously it was only possible to revert the most recent move, unless a backup for every single move was made. This is a better functionality, and combined with the slightly better speed, I think it was reasonable to keep it, even though the code is much more complicated (and prone to bugs that I had to fix) than the backup approach.

I didn't spend much time on the GUI, because it is not a priority for this project. My chess module is ultimately not intended to be played by humans, and so the GUI mainly serves demonstration and debug purposes. It was at times tricky to research the correct functions in the PySimpleGUI module, and in at least one case I only stumbled upon what I wanted to do by accident in an unrelated research. Nevertheless, the module seems to be the right tool for this job, and I didn't regret using it, even though I was first overwhelmed by the sheer number of Python modules that can help build a graphical interface. There were no big obstacles in this module, it works and speed is not an issue, since any game involving a human player will never be played at a pace that this would become a relevant factor.

The bot implementation was by far trickier, even though not as difficult as the chess class. I had to rely a lot on printing evaluation and search results to find out why the bot gives back nonsense moves and the tracking of it was not straightforward, as this always happened in a recursive function with many layers. Generally I could not rely on any kind of visualization tool for Python such as provided by pythontutor.com, for this reason and also for the fact that the bot generally runs millions of computations, that makes step-by-step tracking very difficult. Instead, I think I got a better intuition for what is going on in the code by evaluating the print statements and drawing conclusions to which function could cause abnormal behavior.

One example that I have not completely solved at this point, is the limitation of time per bot move. Since the search runs in an iterative deepening, that means almost certainly the time interrupt will happen when the bot is inside a recursion. Now one possibility is to discard all results from this iteration and just pick the best move that was discovered in a previous iteration, but this feels wasteful, since the search time rises quickly with deeper iterations and the bot might spend a lot of time in this depth, only to have the result discarded. Another idea is to pass the last best move as a starting point to the new iteration, and then waiting for a better move, and if none is found, just returning that starting move. This is implemented right now, but whenever I tried an early termination of the search by using datetime module, the bot would work in some positions, but play catastrophic blunders in others. Since I could not find the issue so far, and the behavior is difficult to track down, I opted for a min_time approach, in which the thinking time given to the bot as parameter is used, but then after reaching it, the bot will fully complete the iteration that it is at. It would also be possible to just pass a fixed iteration depth. Right now the bot is so slow, that I don't care about this behavior, but when I manage to speed it up, then it would be more important to properly implement this, to ultimately allow the bot to play faster time controls such as Blitz or Bullet chess.

Another unexpected behavior I ran into was when I set the evaluation value for a position of checkmate to -inf. This looks promising at first, since losing the game by checkmate should result in the worst possible evaluation. Practically, this causes problems, as this value can never be surpassed again. I would play against the bot in a losing position, and find out that the bot never played the forcing checkmate sequence, instead it just shuffled back and forth. I suspect the reason for this is that each move sequence that potentially leads to a forced checkmate (such as mate in 3) is then evaluated as inf by the bot. Since all of these moves are the same, it just arbitrarily picks the one it had first encountered. This means, that the position can switch back and forth from mate in 3 to mate in 2 and back to mate in 3 again, because the bot doesnt know which of the moves will bring it closer to actually delivering the checkmate. I solved this by picking a very high but non-infinite value for checkmate, and combining it with the depth of the current search recursion. By doing that, a move that will result in mate in 2 will have a value that is exactly 1 higher than a move that leads to mate in 3. Finally the bot can distinguish which move actually brings it closer to delivering checkmate, and this solved the problem.

The last issue I want to describe here for now, is that the zobrist hash that the bot uses to quickly find already encountered positions, is so far calculated anew each time. This is inefficient, especially since zobrist hashes are easily updateable after a position changes. However, implementing this would mean I had to implement the zobrist hash in the chess class instead of the bot class, so for now I will leave this issue. The performance loss is not big compared to other issues in the code, so addressing those first will make more sense.

### Version History Summary
Note that only the most recent version is published in this repository. The information in this chapter is just for reference.

*Chess Module*
- v1: The initial version of the chess module. It contained fully functional representation of the chess board with working rules. No speed optimization yet. GUI module was still included.
- v2: A vastly faster version. The module needs to do far less computation than v1, but has exactly the same features. GUI module still included.
- v3 (current): Introduces the "undo-move" mechanic that can take all moves back until the first move that was made. Also includes further speed improvements through better code design, but no optimization through extensions yet. Also, the GUI module is moved to a different file in this version.

*Bot*
- v1: The initial version of the chess bot. The main idea of this version was to create the link to the chess module and allow for some kind of move evaluation and recursive search to find the best move.
- v2 (current): Includes much more internal tweaks that help to find the best move than v1. Many ideas here revolve around prioritizing good moves to cut down on calculation time. No speed improvement through extensions yet.

*GUI*
- v1 (current): A simple GUI to represent the chess board and allow for play by mouse.

### Possible Future Tweaks and Changes

*Chess Module*
- Improve calculation speed of the bot and/ or chess module by using NumPy, Cython, Numba, Jax, PyPI, custom C extensions, ...
- Adjust instance variable status private/ public (so far all are public)
- Allow tracking of moves back and forth (so far only undoing moves is possible)

*Bot*
- Track down reason for big spread in puzzle performance and random blunders
- Try out Python's deep learning module to make the chess bot stronger through playing against itself
- Implement fixed movetime (currently minimum movetime plus a flexible amount)
- Program interface for Lichess and let the bot play there on a registered bot account

*GUI*
- Show square file and rank names
- Simple menu for selecting color and starting position (FEN)
- Allow flipped display of the board
- Find or create better tile images (currently a bit blurry)
- Implement time controls

