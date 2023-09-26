#include <Python.h>

// CONSTANTS

// piece and color constant ints
int WHITE = 8;
int BLACK = 16;

int NO_PIECE = 0;
int KING = 1;
int PAWN = 2;
int KNIGHT = 3;
int BISHOP = 4;
int ROOK = 5;
int QUEEN = 6;


// array of coord structs, that lets us convert board squares to (y,x) coordinates
struct coord {int y; int x;};
struct coord INT2YX[64] = {
    {0,0},{0,1},{0,2},{0,3},{0,4},{0,5},{0,6},{0,7},
    {1,0},{1,1},{1,2},{1,3},{1,4},{1,5},{1,6},{1,7},
    {2,0},{2,1},{2,2},{2,3},{2,4},{2,5},{2,6},{2,7},
    {3,0},{3,1},{3,2},{3,3},{3,4},{3,5},{3,6},{3,7},
    {4,0},{4,1},{4,2},{4,3},{4,4},{4,5},{4,6},{4,7},
    {5,0},{5,1},{5,2},{5,3},{5,4},{5,5},{5,6},{5,7},
    {6,0},{6,1},{6,2},{6,3},{6,4},{6,5},{6,6},{6,7},
    {7,0},{7,1},{7,2},{7,3},{7,4},{7,5},{7,6},{7,7}
 };

// the opposite array, to convert (y,x) to sq integer
int YX2INT[8][8] = {
    {0,1,2,3,4,5,6,7},
    {8,9,10,11,12,13,14,15},
    {16,17,18,19,20,21,22,23},
    {24,25,26,27,28,29,30,31},
    {32,33,34,35,36,37,38,39},
    {40,41,42,43,44,45,46,47},
    {48,49,50,51,52,53,54,55},
    {56,57,58,59,60,61,62,63}
};

// piece split array to be able to access color and type separately. note that this is a "hack", because I want a dict, but C doesnt have dicts, so I index into an array with integers, but I dont need the whole array for that
struct piece_tuple {int color; int type;};
struct piece_tuple PIECE_SPLIT[23] = {
    {0,0},{-1,-1},{-1,-1},{-1,-1},{-1,-1},{-1,-1},{-1,-1},{-1,-1},{-1,-1},{8,1},{8,2},{8,3},{8,4},{8,5},{8,6},{-1,-1},{-1,-1},{16,1},{16,2},{16,3},{16,4},{16,5},{16,6}
};

// defining structs that can accomodate piece movement pattern offsets and initializing an according array
struct offsets {int num_off; struct coord offset[7];};
struct directions {int num_dir; struct offsets direction[8];};

// assembling all move patterns except for pawns in one array. note the empty fillings at index 0 and 2
struct directions PIECE_MOVEMENT_PATTERNS[7] = {
    {8,{{7,{{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}}},{7,{{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}}},{7,{{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}}},{7,{{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}}},{7,{{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}}},{7,{{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}}},{7,{{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}}},{7,{{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}}}}},
    {8,{{1,{{1,1}}},{1,{{0,1}}},{1,{{-1,1}}},{1,{{-1,0}}},{1,{{-1,-1}}},{1,{{0,-1}}},{1,{{1,-1}}},{1,{{1,0}}}}},
    {8,{{7,{{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}}},{7,{{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}}},{7,{{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}}},{7,{{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}}},{7,{{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}}},{7,{{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}}},{7,{{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}}},{7,{{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}}}}},
    {8,{{1,{{2,1}}},{1,{{1,2}}},{1,{{-1,2}}},{1,{{-2,1}}},{1,{{-2,-1}}},{1,{{-1,-2}}},{1,{{1,-2}}},{1,{{2,-1}}}}},
    {4,{{7,{{1,1},{2,2},{3,3},{4,4},{5,5},{6,6},{7,7}}},{7,{{-1,-1},{-2,-2},{-3,-3},{-4,-4},{-5,-5},{-6,-6},{-7,-7}}},{7,{{-1,1},{-2,2},{-3,3},{-4,4},{-5,5},{-6,6},{-7,7}}},{7,{{1,-1},{2,-2},{3,-3},{4,-4},{5,-5},{6,-6},{7,-7}}}}},
    {4,{{7,{{1,0},{2,0},{3,0},{4,0},{5,0},{6,0},{7,0}}},{7,{{0,1},{0,2},{0,3},{0,4},{0,5},{0,6},{0,7}}},{7,{{-1,0},{-2,0},{-3,0},{-4,0},{-5,0},{-6,0},{-7,0}}},{7,{{0,-1},{0,-2},{0,-3},{0,-4},{0,-5},{0,-6},{0,-7}}}}},
    {8,{{7,{{1,1},{2,2},{3,3},{4,4},{5,5},{6,6},{7,7}}},{7,{{-1,-1},{-2,-2},{-3,-3},{-4,-4},{-5,-5},{-6,-6},{-7,-7}}},{7,{{-1,1},{-2,2},{-3,3},{-4,4},{-5,5},{-6,6},{-7,7}}},{7,{{1,-1},{2,-2},{3,-3},{4,-4},{5,-5},{6,-6},{7,-7}}},{7,{{1,0},{2,0},{3,0},{4,0},{5,0},{6,0},{7,0}}},{7,{{0,1},{0,2},{0,3},{0,4},{0,5},{0,6},{0,7}}},{7,{{-1,0},{-2,0},{-3,0},{-4,0},{-5,0},{-6,0},{-7,0}}},{7,{{0,-1},{0,-2},{0,-3},{0,-4},{0,-5},{0,-6},{0,-7}}}}}
};

// defining movement patterns for paws (move, double-move, capture)
struct directions PAWN_MOVE = {1,{{1,{{1,0}}}}};
struct directions PAWN_DOUBLE_MOVE = {1,{{1,{{2,0}}}}};
struct directions PAWN_CAPTURE = {2,{{1,{{1,-1}}},{1,{{1,1}}}}};

// promotion options for either color
int PROMOTE_WHITE[4] = {14,13,12,11};
int PROMOTE_BLACK[4] = {22,21,20,19};

// castles empty field arrays
int CASTLE_EMPTY_WKING[2] = {5,6};
int CASTLE_EMPTY_WQUEEN[3] = {1,2,3};
int CASTLE_EMPTY_BKING[2] = {61,62};
int CASTLE_EMPTY_BQUEEN[3] = {57,58,59};


// HELPER FUNCTIONS

// out of bounds check for the chessboard
int outofbounds(int y, int x){
    return (y < 0 || y > 7|| x < 0 || x > 7);
}

// just flipping the colors white <-> black
int oppositecolor(int color){
    if (color == WHITE){
        return BLACK;
    }
    else if (color == BLACK){
        return WHITE;
    }

    printf("no valid color given");
    return 0; // shouldnt happen
}

// loading in the board array from python. this functionality is needed multiple times and so we outsource it to this function. caller needs to malloc the array, pass in the pointer to it, and free memory after processing
int load_board(PyObject* py_board, int* board){

    // loading the board as array by first loading it as an iterator, then iterating through it and copying the values to a C array
    PyObject *board_iter = PyObject_GetIter(py_board);
    if (!board_iter) {
        printf("board is not iterable!");
        return 1; // error in case no iterator
    }    
    int p; // declaring before loop
    for (int i = 0; i < 64; i++) {
        PyObject *next_p = PyIter_Next(board_iter);
        if (!next_p) {
            printf("board did not have 64 squares!");
            // nothing left in the iterator
            return 1;
        }

        if (!PyLong_Check(next_p)) {
            printf("board values are not integer!");
            return 1;
            // error, we were expecting an int value. note that PyLong_Check checks for long and int, there is no "PyInt_Check"
        }

        p = PyLong_AsLong(next_p);
        Py_DECREF(next_p); // need to decref this object, otherwise we get a memory leak
        board[i] = p;
    }

    Py_DECREF(board_iter); // also decref the whole iterator after finishing

    if (PyErr_Occurred()) {
        return 1;
        /* propagate error */
    }

    return 0; // function execution successful
}


// PYTHON EXTENSION FUNCTIONS

// this function works almost identical to pseudo_legal_moves, but instead of appending all moves to a list, it just checks whether the enemy king can be captured or not and returns as early as possible to save time.
static PyObject* king_capt(PyObject* self, PyObject* args) {
    // declare arguments as C type
    PyObject *piece_loc, *py_board; // these are borrowed references! we dont need to decref them
    int color;

    // reading in the passed arguments, note that color is referenced directly because it is an int, but for the PyObjects we need more work
    if (!PyArg_ParseTuple(args, "OOi", &piece_loc, &py_board, &color))
        return NULL;

    // loading in the chess board
    int* board = malloc(64*sizeof(int));
    if (!board) {
        printf("memory allocation for board failed!");
        return NULL;
    }
    if (load_board(py_board, board) != 0) {
        printf("board could not be copied to array!");
        return NULL;
    }

    // loading piece_loc as an iterator
    PyObject *piece_loc_iter = PyObject_GetIter(piece_loc);
    if (!piece_loc_iter) {
        printf("piece_loc is not iterable!");
        return NULL; // error in case no iterator
    }

    // declaring as many variables as possible before the loop
    int sq,y,x,f,piece_type,new_field;
    struct coord yx,offset,new_field_coord;
    struct directions pattern;

    // iterating through piece_loc (all squares that contain a piece)
    while (1) {
        PyObject *next_sq = PyIter_Next(piece_loc_iter);
        if (!next_sq) {
            // nothing left in the iterator
            break;
        }

        if (!PyLong_Check(next_sq)) {
            printf("piece_loc values are not integer!");
            return NULL;
            // error, we were expecting an int value. note that PyLong_Check checks for long and int, there is no "PyInt_Check"
        }

        sq = PyLong_AsLong(next_sq);
        Py_DECREF(next_sq);
        
        yx = INT2YX[sq];
        y = yx.y;
        x = yx.x;
        f = board[sq];
        piece_type = PIECE_SPLIT[f].type;

        // calculating all pieces except pawns
        if (piece_type != PAWN) {
            pattern = PIECE_MOVEMENT_PATTERNS[piece_type];
            for (int i = 0; i < pattern.num_dir; i++) {
                for (int j = 0; j < pattern.direction[i].num_off; j++) {
                    offset = pattern.direction[i].offset[j];
                    new_field_coord = (struct coord){.y= y+offset.y, .x= x+offset.x};

                    if (outofbounds(new_field_coord.y,new_field_coord.x)) {
                        break;
                    }
                    else {
                        new_field = YX2INT[new_field_coord.y][new_field_coord.x];
                    }

                    // new field is empty and therefore a valid target field
                    if (board[new_field] == NO_PIECE) {
                        continue;
                    }
                    // new field occupied by own piece, break this direction early
                    else if (PIECE_SPLIT[board[new_field]].color == color) {
                        break;
                    }
                    // new field occupied by opponents king
                    else if (board[new_field] == oppositecolor(color)+KING){
                        free(board);

                        Py_DECREF(piece_loc_iter);
                        if (PyErr_Occurred()) {
                            return NULL;
                            /* propagate error */
                        }

                        return Py_BuildValue("i", 1);
                    }
                    // new field occupied by an enemy piece that is not the king
                    else {
                        break;
                    }
                }
            }
        }
        // calculating pawns separately because they have special move rules
        else {
            // implementation of the capturing move for pawns which goes sideways
            pattern = PAWN_CAPTURE;
            for (int i = 0; i < pattern.num_dir; i++) {
                for (int j = 0; j < pattern.direction[i].num_off; j++) {
                    offset = pattern.direction[i].offset[j];

                    if (color == WHITE) {
                        new_field_coord = (struct coord){.y=y+offset.y, .x=x+offset.x};
                    }
                    else {
                        new_field_coord = (struct coord){.y= y-offset.y, .x= x-offset.x};
                    }

                    // checking for out of bounds, which is possible with sideways capture
                    if (outofbounds(new_field_coord.y,new_field_coord.x)) {
                        break;
                    }
                    // new field is occupied by enemy king
                    else if (board[YX2INT[new_field_coord.y][new_field_coord.x]] == oppositecolor(color)+KING) {
                        free(board);

                        Py_DECREF(piece_loc_iter);
                        if (PyErr_Occurred()) {
                            return NULL;
                            /* propagate error */
                        }

                        return Py_BuildValue("i", 1);
                    }
                }
            }
        }
    
    }
    

    Py_DECREF(piece_loc_iter);
    if (PyErr_Occurred()) {
        return NULL;
        /* propagate error */
    }

    free(board);
    return Py_BuildValue("i", 0);
}

// this function keeps track of what the opponent can do on the board. it gives back a dict that is divided into a part that includes all directly reachable squares (by reachable it means takeable here) and a second part that checks if there are lines towards the king, that are currently blocked by enemy pieces. that way we can easily access this information to check if a move we want to make is legal or would result in our king standing in check
static PyObject* update_reachable(PyObject* self, PyObject* args) {
    // declare arguments as C type
    PyObject *piece_loc, *py_board;
    int color;

    // reading in the passed arguments, note that color is referenced directly because it is an int, but for the PyObjects we need more work
    if (!PyArg_ParseTuple(args, "OOi", &piece_loc, &py_board, &color))
        return NULL;

    // loading in the chess board
    int* board = malloc(64*sizeof(int));
    if (!board) {
        printf("memory allocation for board failed!");
        return NULL;
    }
    if (load_board(py_board, board) != 0) {
        printf("board could not be copied to array!");
        return NULL;
    }

    // creating an empty python dict, which we will process and then return later
    PyObject* reachable = PyDict_New();
    
    // these are the 3 sets that will make up the reachable dict in the end
    PyObject* all_direct = PySet_New(NULL);
    PyObject* king_indirect_blocked = PySet_New(NULL);
    PyObject* pawn_attack = PySet_New(NULL);

    // loading piece_loc as an iterator
    PyObject *piece_loc_iter = PyObject_GetIter(piece_loc);
    if (!piece_loc_iter) {
        printf("piece_loc is not iterable!");
        return NULL; // error in case no iterator
    }

    // declaring variables
    int sq,y,x,f,piece_type,blocking_piece,new_field;
    struct coord yx,offset,new_field_coord;
    struct directions pattern;
    PyObject *tmp;

    // iterating through piece_loc (all squares that contain a piece)
    while (1) {
        PyObject *next_sq = PyIter_Next(piece_loc_iter);
        if (!next_sq) {
            // nothing left in the iterator
            break;
        }

        if (!PyLong_Check(next_sq)) {
            printf("piece_loc values are not integer!");
            break;
            // error, we were expecting an int value. note that PyLong_Check checks for long and int, there is no "PyInt_Check"
        }

        sq = PyLong_AsLong(next_sq);
        Py_DECREF(next_sq);
        
        yx = INT2YX[sq];
        y = yx.y;
        x = yx.x;
        f = board[sq];
        piece_type = PIECE_SPLIT[f].type;

        // calculating all pieces except pawns
        if (piece_type != PAWN) {
            pattern = PIECE_MOVEMENT_PATTERNS[piece_type];
            for (int i = 0; i < pattern.num_dir; i++) {
                blocking_piece = -1;
                for (int j = 0; j < pattern.direction[i].num_off; j++) {
                    offset = pattern.direction[i].offset[j];
                    new_field_coord = (struct coord){.y= y+offset.y, .x= x+offset.x};

                    if (outofbounds(new_field_coord.y,new_field_coord.x)) {
                        break;
                    }
                    else {
                        new_field = YX2INT[new_field_coord.y][new_field_coord.x];
                    }

                    if (blocking_piece == -1) {
                        // new field is empty and therefore a valid target field
                        if (board[new_field] == NO_PIECE) {
                            tmp = Py_BuildValue("i",new_field);
                            PySet_Add(all_direct, tmp);
                            Py_DECREF(tmp);
                        }
                        // new field occupied by own piece, break this direction early, but add, since that means protecting the piece
                        else if (PIECE_SPLIT[board[new_field]].color == color) {
                            tmp = Py_BuildValue("i",new_field);
                            PySet_Add(all_direct, tmp);
                            Py_DECREF(tmp);
                            break;
                        }
                        // new field occupied by opponents piece, allow this move (to capture) and then see if the fields behind the blocking piece are the opponents king location
                        else if (PIECE_SPLIT[board[new_field]].color == oppositecolor(color)) {
                            tmp = Py_BuildValue("i",new_field);
                            PySet_Add(all_direct, tmp);
                            Py_DECREF(tmp);
                            blocking_piece = new_field;
                        }
                    }
                    else {
                        // new field is empty, continue looking
                        if (board[new_field] == NO_PIECE) {
                            continue;
                        }
                        // new field occupied by own piece, break this direction early
                        else if (PIECE_SPLIT[board[new_field]].color == color) {
                            break;
                        }
                        // found the enemy king, this means a piece has a line towards the king that is blocked by the blocking_piece, which we therefore add to the dict and break
                        else if (board[new_field] == oppositecolor(color)+KING) {
                            tmp = Py_BuildValue("i",blocking_piece);
                            PySet_Add(king_indirect_blocked, tmp);
                            Py_DECREF(tmp);
                            break;
                        }
                        // in all other cases, e.g. finding another enemy piece, we break without adding anything to the dict
                        else {
                            break;
                        }
                    }
                }
            }
        }

        // calculating pawns separately because they have special move rules
        else {
            // only pawn captures need to be considered, as this is about seeing if we can beat the king
            pattern = PAWN_CAPTURE;
            for (int i = 0; i < pattern.num_dir; i++) {
                for (int j = 0; j < pattern.direction[i].num_off; j++) {
                    offset = pattern.direction[i].offset[j];

                    if (color == WHITE) {
                        new_field_coord = (struct coord){.y=y+offset.y, .x=x+offset.x};
                    }
                    else {
                        new_field_coord = (struct coord){.y= y-offset.y, .x= x-offset.x};
                    }

                    // checking for out of bounds, which is possible with sideways capture
                    if (outofbounds(new_field_coord.y,new_field_coord.x)) {
                        break;
                    }
                    // new field is occupied by an enemy or own piece or empty and therefore a valid target field
                    else {
                        tmp = Py_BuildValue("i",YX2INT[new_field_coord.y][new_field_coord.x]);
                        PySet_Add(all_direct, tmp);
                        Py_DECREF(tmp);

                        tmp = Py_BuildValue("i",YX2INT[new_field_coord.y][new_field_coord.x]);
                        PySet_Add(pawn_attack, tmp);
                        Py_DECREF(tmp);
                    }
                }
            }
        }
    }
    Py_DECREF(piece_loc_iter);
    

    // placing all three reachable categories in the final dict before returning
    tmp = Py_BuildValue("s", "all_direct");
    PyDict_SetItem(reachable,tmp,all_direct);
    Py_DECREF(tmp);

    tmp = Py_BuildValue("s", "king_indirect_blocked");
    PyDict_SetItem(reachable,tmp,king_indirect_blocked);
    Py_DECREF(tmp);

    tmp = Py_BuildValue("s", "pawn_attack");
    PyDict_SetItem(reachable,tmp,pawn_attack);
    Py_DECREF(tmp);

    Py_DECREF(all_direct);
    Py_DECREF(king_indirect_blocked);
    Py_DECREF(pawn_attack);

    if (PyErr_Occurred()) {
        return NULL;
        /* propagate error */
    }

    // returning the newly created reachable dict
    free(board);
    return reachable;
}

// this function returns a list of all pseudo legal moves for the player of a certain color (white or black). pseudo legal means the pieces can move in that way, but checks or other "forcing" conditions are not yet looked at. it is quite a lot of code and it would be possible to distribute it to multiple functions, but having it in one place seems to make more sense to me in this case.
static PyObject* pseudo_legal(PyObject* self, PyObject* args) {
    // declare arguments as C type
    PyObject *piece_loc, *py_board, *castling_rights;
    int color,en_passant_target;

    // reading in the passed arguments, note that color and en_passant_target are referenced directly because they are an int, but for the PyObjects we need more work
    if (!PyArg_ParseTuple(args, "OOOii", &piece_loc, &py_board, &castling_rights, &color, &en_passant_target))
        return NULL;

    // loading in the chess board
    int* board = malloc(64*sizeof(int));
    if (!board) {
        printf("memory allocation for board failed!");
        return NULL;
    }
    if (load_board(py_board, board) != 0) {
        printf("board could not be copied to array!");
        return NULL;
    }

    // creating the list objects that we return later
    PyObject* noncaptures = PyList_New(0);
    PyObject* captures = PyList_New(0);

    // loading piece_loc as an iterator
    PyObject *piece_loc_iter = PyObject_GetIter(piece_loc);
    if (!piece_loc_iter) {
        printf("piece_loc is not iterable!");
        return NULL; // error in case no iterator
    }

    // declaring variables
    int sq,y,x,f,piece_type,new_field,c,blocked;
    struct coord yx,offset,new_field_coord,through_coord;
    struct directions pattern;
    PyObject *tmp, *tmp_return;

    // iterating through piece_loc (all squares that contain a piece for our own color)
    while (1) {
        PyObject *next_sq = PyIter_Next(piece_loc_iter);
        if (!next_sq) {
            // nothing left in the iterator
            break;
        }

        if (!PyLong_Check(next_sq)) {
            printf("piece_loc values are not integer!");
            break;
            // error, we were expecting an int value. note that PyLong_Check checks for long and int, there is no "PyInt_Check"
        }

        sq = PyLong_AsLong(next_sq);
        Py_DECREF(next_sq);
        
        yx = INT2YX[sq];
        y = yx.y;
        x = yx.x;
        f = board[sq];
        piece_type = PIECE_SPLIT[f].type;

        // calculating all pieces except pawns
        if (piece_type != PAWN) {
            pattern = PIECE_MOVEMENT_PATTERNS[piece_type];
            for (int i = 0; i < pattern.num_dir; i++) {
                for (int j = 0; j < pattern.direction[i].num_off; j++) {
                    offset = pattern.direction[i].offset[j];
                    new_field_coord = (struct coord){.y= y+offset.y, .x= x+offset.x};

                    if (outofbounds(new_field_coord.y,new_field_coord.x)) {
                        break;
                    }
                    else {
                        new_field = YX2INT[new_field_coord.y][new_field_coord.x];
                    }

                    // new field is empty and therefore a valid target field
                    if (board[new_field] == NO_PIECE) {
                        tmp = Py_BuildValue("(iiiii)",y,x,new_field_coord.y,new_field_coord.x,0);
                        PyList_Append(noncaptures, tmp);
                        Py_DECREF(tmp);
                    }
                    // new field occupied by own piece, break this direction early
                    else if (PIECE_SPLIT[board[new_field]].color == color) {
                        break;
                    }
                    // new field occupied by opponents piece, break, but allow this move (to capture)
                    else if (PIECE_SPLIT[board[new_field]].color == oppositecolor(color)) {
                        tmp = Py_BuildValue("(iiiii)",y,x,new_field_coord.y,new_field_coord.x,0);
                        PyList_Append(captures, tmp);
                        Py_DECREF(tmp);
                        break;
                    }
                }
            }
        }
        // calculating pawns separately because they have special move rules
        else {
            pattern = PAWN_MOVE;
            for (int i = 0; i < pattern.num_dir; i++) {
                for (int j = 0; j < pattern.direction[i].num_off; j++) {
                    offset = pattern.direction[i].offset[j];

                    if (color == WHITE) {
                        new_field_coord = (struct coord){.y=y+offset.y, .x=x+offset.x};
                    }
                    else {
                        new_field_coord = (struct coord){.y= y-offset.y, .x= x-offset.x};
                    }
                    
                    // we need to check out of bounds because the pawn can reach the edge of the board just before promoting
                    if (outofbounds(new_field_coord.y,new_field_coord.x)) {
                        break;
                    }
                    // new field is empty and therefore a valid target field, all other cases are an illegal move because pawns capture sideways, which will be implemented in the third loop
                    else if (board[YX2INT[new_field_coord.y][new_field_coord.x]] == NO_PIECE) {
                        if (new_field_coord.y == 7 && color == WHITE) {
                            for (int k = 0; k < 4; k++) {
                                tmp = Py_BuildValue("(iiiii)",y,x,new_field_coord.y,new_field_coord.x,PROMOTE_WHITE[k]);
                                PyList_Append(noncaptures, tmp);
                                Py_DECREF(tmp);
                            }
                        }
                        else if (new_field_coord.y == 0 && color == BLACK) {
                            for (int k = 0; k < 4; k++) {
                                tmp = Py_BuildValue("(iiiii)",y,x,new_field_coord.y,new_field_coord.x,PROMOTE_BLACK[k]);
                                PyList_Append(noncaptures, tmp);
                                Py_DECREF(tmp);
                            }
                        }
                        else {
                            tmp = Py_BuildValue("(iiiii)",y,x,new_field_coord.y,new_field_coord.x,0);
                            PyList_Append(noncaptures, tmp);
                            Py_DECREF(tmp);
                        }
                    }
                }
            }
            // the special pawn move (forward by 2) is only possible if the pawn is on the 2nd rank for white or 7th rank for black, so we check this
            if ((color == WHITE && y == 1) || (color == BLACK && y == 6)) {
                pattern = PAWN_DOUBLE_MOVE;
                for (int i = 0; i < pattern.num_dir; i++) {
                    for (int j = 0; j < pattern.direction[i].num_off; j++) {
                        offset = pattern.direction[i].offset[j];

                        if (color == WHITE) {
                            new_field_coord = (struct coord){.y=y+offset.y, .x=x+offset.x};
                        }
                        else {
                            new_field_coord = (struct coord){.y= y-offset.y, .x= x-offset.x};
                        }
                        // additional field that the pawn needs to move through
                        if (color == WHITE) {
                            through_coord = (struct coord){.y=new_field_coord.y-1, .x=new_field_coord.x};
                        }
                        else {
                            through_coord = (struct coord){.y=new_field_coord.y+1, .x=new_field_coord.x};
                        }

                        // new field is empty and therefore a valid target field AND the field before that is also empty
                        if (board[YX2INT[new_field_coord.y][new_field_coord.x]] == NO_PIECE && board[YX2INT[through_coord.y][through_coord.x]] == NO_PIECE) {
                            tmp = Py_BuildValue("(iiiii)",y,x,new_field_coord.y,new_field_coord.x,0);
                            PyList_Append(noncaptures, tmp);
                            Py_DECREF(tmp);
                        }
                    }
                }
            }
            // implementation of the capturing move for pawns which goes sideways
            pattern = PAWN_CAPTURE;
            for (int i = 0; i < pattern.num_dir; i++) {
                for (int j = 0; j < pattern.direction[i].num_off; j++) {
                    offset = pattern.direction[i].offset[j];

                    if (color == WHITE) {
                        new_field_coord = (struct coord){.y=y+offset.y, .x=x+offset.x};
                    }
                    else {
                        new_field_coord = (struct coord){.y= y-offset.y, .x= x-offset.x};
                    }

                    // checking for out of bounds, which is possible with sideways capture
                    if (outofbounds(new_field_coord.y,new_field_coord.x)) {
                        break;
                    }
                    // new field is occupied by an enemy piece and therefore a valid target field
                    else if (PIECE_SPLIT[board[YX2INT[new_field_coord.y][new_field_coord.x]]].color == oppositecolor(color)) {
                        if (new_field_coord.y == 7 && color == WHITE) {
                            for (int k = 0; k < 4; k++) {
                                tmp = Py_BuildValue("(iiiii)",y,x,new_field_coord.y,new_field_coord.x,PROMOTE_WHITE[k]);
                                PyList_Append(captures, tmp);
                                Py_DECREF(tmp);
                            }
                        }
                        else if (new_field_coord.y == 0 && color == BLACK) {
                            for (int k = 0; k < 4; k++) {
                                tmp = Py_BuildValue("(iiiii)",y,x,new_field_coord.y,new_field_coord.x,PROMOTE_BLACK[k]);
                                PyList_Append(captures, tmp);
                                Py_DECREF(tmp);
                            }
                        }
                        else {
                            tmp = Py_BuildValue("(iiiii)",y,x,new_field_coord.y,new_field_coord.x,0);
                            PyList_Append(captures, tmp);
                            Py_DECREF(tmp);
                        }
                    }
                    else if (YX2INT[new_field_coord.y][new_field_coord.x] == en_passant_target) {
                        tmp = Py_BuildValue("(iiiii)",y,x,new_field_coord.y,new_field_coord.x,0);
                        PyList_Append(captures, tmp);
                        Py_DECREF(tmp);
                    }
                }
            }
        }
    }
    Py_DECREF(piece_loc_iter);

    // checking if special move castle is possible, seeing if own pieces are in the way, but not yet checking if we move through opponents check. this will be implemented in another function

    // loading castling_rights as an iterator
    PyObject *castling_iter = PyObject_GetIter(castling_rights);
    if (!castling_iter) {
        printf("castling_rights is not iterable!");
        return NULL; // error in case no iterator
    }

    // iterating through castling_rights (the castling options that the currently to move king has)
    while (1) {
        PyObject *next_c = PyIter_Next(castling_iter);
        if (!next_c) {
            // nothing left in the iterator
            break;
        }

        if (!PyLong_Check(next_c)) {
            printf("castling_rights values are not integer!");
            break;
            // error, we were expecting an int value. note that PyLong_Check checks for long and int, there is no "PyInt_Check"
        }

        c = PyLong_AsLong(next_c);
        Py_DECREF(next_c);

        blocked = 0;
        // we use a switch case for the 4 different castle types
        switch (c) {
            case 9: // WKING
                for (int l = 0; l < 2; l++) {
                    if (board[CASTLE_EMPTY_WKING[l]] != NO_PIECE) {
                        blocked = 1;
                        break;
                    }
                }
                if (blocked == 0) {
                    tmp = Py_BuildValue("(iiiii)",0,4,0,6,0);
                    PyList_Append(noncaptures, tmp);
                    Py_DECREF(tmp);
                }
                break;
            case 14: // WQUEEN
                for (int l = 0; l < 3; l++) {
                    if (board[CASTLE_EMPTY_WQUEEN[l]] != NO_PIECE) {
                        blocked = 1;
                        break;
                    }
                }
                if (blocked == 0) {
                    tmp = Py_BuildValue("(iiiii)",0,4,0,2,0);
                    PyList_Append(noncaptures, tmp);
                    Py_DECREF(tmp);
                }
                break;
            case 17: // BKING
                for (int l = 0; l < 2; l++) {
                    if (board[CASTLE_EMPTY_BKING[l]] != NO_PIECE) {
                        blocked = 1;
                        break;
                    }
                }
                if (blocked == 0) {
                    tmp = Py_BuildValue("(iiiii)",7,4,7,6,0);
                    PyList_Append(noncaptures, tmp);
                    Py_DECREF(tmp);
                }
                break;
            case 22: // BQUEEN
                for (int l = 0; l < 3; l++) {
                    if (board[CASTLE_EMPTY_BQUEEN[l]] != NO_PIECE) {
                        blocked = 1;
                        break;
                    }
                }
                if (blocked == 0) {
                    tmp = Py_BuildValue("(iiiii)",7,4,7,2,0);
                    PyList_Append(noncaptures, tmp);
                    Py_DECREF(tmp);
                }
                break;
            default:
                printf("provided castling rights do not match any of the 4 castle possibilities!");
                return NULL;
        }
    }
    Py_DECREF(castling_iter);

    if (PyErr_Occurred()) {
        return NULL;
        /* propagate error */
    }

    tmp_return = Py_BuildValue("(OO)",noncaptures,captures);
    Py_DECREF(noncaptures);
    Py_DECREF(captures);

    // returning a tuple of both lists
    free(board);
    return tmp_return;
}


// MODULE INIT

static PyMethodDef ChessExtensionMethods[] = {
    {"check_possible_king_capt", king_capt, METH_VARARGS, "Checks if the king could be captured"},
    {"update_reachable", update_reachable, METH_VARARGS, "Updates the reachable dict and returns it"},
    {"pseudo_legal_moves", pseudo_legal, METH_VARARGS, "Returns 2 lists, that combine to all the pseudo legal moves in the position"},
    {NULL, NULL, 0, NULL} /* Sentinel */
};

static struct PyModuleDef chess_extension_module = {
    PyModuleDef_HEAD_INIT,
    "chess_extension", /* name of module */
    NULL,           /* module documentation, may be NULL */
    -1,             /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
    ChessExtensionMethods
};

PyMODINIT_FUNC PyInit_chess_extension(void) {
    return PyModule_Create(&chess_extension_module);
}