import pygame
from math import sqrt
from queue import PriorityQueue
from time import sleep

# time delay to slow down the algorithm visualization
STEP = 0.02

# pygame window size
WIN_LENGTH = 800
WIN_HEIGHT = 600

# size of a single square, ideally both win_length and win_height need to be divisible by sq_size
SQ_SIZE = 16

# row and column count in the whole window
ROWS = WIN_HEIGHT // SQ_SIZE
COLUMNS = WIN_LENGTH // SQ_SIZE

# set pygame window and caption
WIN = pygame.display.set_mode((WIN_LENGTH, WIN_HEIGHT))
pygame.display.set_caption('A* Path Finding Algorithm')

# colors
BLUE1 = (172, 216, 236)
BLUE2 = (80, 164, 214)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165 ,0)
GREY = (128, 128, 128)
TURQUOISE = (64, 224, 208)

# mapping of square status to color
STATUS2COLOR = {
    'new': WHITE,
    'closed': BLUE1,
    'open': BLUE2,
    'barrier': BLACK,
    'start': RED,
    'end': GREEN,
    'path': PURPLE
}


# this class defines a square type
class Square:

    # note that (0,0) is in the top left corner of the window, and x goes right and y goes left
    def __init__(self, row, col, total_rows, total_cols, size):
        self.row = row
        self.col = col

        # coordinates
        self.x = col * size
        self.y = row * size
        
        # neighbor list
        self.neighbors = []

        self.size = size
        self.total_rows = total_rows
        self.total_cols = total_cols

        # initial status is always 'new'
        self.status = 'new'
        self.color = STATUS2COLOR[self.status]

    # return the current position of a square
    def get_pos(self):
        return self.row, self.col

    # return the current status of a square
    def get_status(self):
        return self.status

    # change the type (status) of a square
    def set_status(self, status):
        self.status = status
        self.color = STATUS2COLOR[self.status]

    # draw the square using pygame
    def draw(self, win):
        pygame.draw.rect(win, self.color, (self.x, self.y, self.size, self.size))

    # this adds all applicable neighbor squares (no barriers) to each squares neighbor list
    def update_neighbors(self, grid):
        self.neighbors = []

        if self.row < self.total_rows - 1 and grid[self.row + 1][self.col].get_status() != 'barrier': # down
            self.neighbors.append((1, grid[self.row + 1][self.col]))

        if self.row > 0 and grid[self.row - 1][self.col].get_status() != 'barrier': # up
            self.neighbors.append((1, grid[self.row - 1][self.col]))

        if self.col < self.total_rows - 1 and grid[self.row][self.col + 1].get_status() != 'barrier': # right
            self.neighbors.append((1, grid[self.row][self.col + 1]))

        if self.col > 0 and grid[self.row][self.col - 1].get_status() != 'barrier': # left
            self.neighbors.append((1, grid[self.row][self.col - 1]))

        if self.row > 0 and self.col > 0 and grid[self.row - 1][self.col - 1].get_status() != 'barrier': # up left
            self.neighbors.append((sqrt(2), grid[self.row - 1][self.col - 1]))

        if self.row < self.total_rows - 1 and self.col < self.total_cols - 1 and grid[self.row + 1][self.col + 1].get_status() != 'barrier': # down right
            self.neighbors.append((sqrt(2), grid[self.row + 1][self.col + 1]))

        if self.row < self.total_rows - 1 and self.col > 0 and grid[self.row + 1][self.col - 1].get_status() != 'barrier': # down left
            self.neighbors.append((sqrt(2), grid[self.row + 1][self.col - 1]))

        if self.row > 0 and self.col < self.total_cols - 1 and grid[self.row - 1][self.col + 1].get_status() != 'barrier': # up right
            self.neighbors.append((sqrt(2), grid[self.row - 1][self.col + 1]))


# distance estimation function, I use euclidean distance for this
def h(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return sqrt((x1 - x2)**2 + (y1 - y2)**2)

# reconstruct the calculated path by going through the came_from dict
def reconstruct_path(came_from, current, draw):
    while current in came_from:
        current = came_from[current]
        current.set_status('path')
        draw()

# the a* algorithm
def algorithm(draw, grid, start, end):
    count = 0 # count is just a tie breaker
    open_set = PriorityQueue()
    open_set.put((0, count, start))
    came_from = {}

    # both g and f scores are initialized to +inf for all squares, then we change it to g=0 and f=h(start, end) for the starting square
    g_score = {sq: float('inf') for row in grid for sq in row}
    g_score[start] = 0
    f_score = {sq: float('inf') for row in grid for sq in row}
    f_score[start] = h(start.get_pos(), end.get_pos())
    
    # we need the hash for an easy lookup of which squares are currently in the open set
    open_set_hash = {start}

    while not open_set.empty():

        # time delay
        sleep(STEP)

        # this condition is needed in case the algorithm should be aborted
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        # getting the foremost square in the open set, the one with the lowest f-score
        current = open_set.get()[2]

        # if the current square is the end square, then the algorithm is finished and the reconstruction can be started
        if current == end:
            reconstruct_path(came_from, end, draw)

            # returning start and end to their original status and color
            end.set_status('end')
            start.set_status('start')

            return True

        # in this loop the algorithm looks at all neighbors of the current square
        for neighbor_t in current.neighbors:
            dist, neighbor = neighbor_t

            # assigning a temporary g score and checking if it is lower than the previously calculated g score
            temp_g_score = g_score[current] + dist

            if temp_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = temp_g_score
                f_score[neighbor] = temp_g_score + h(neighbor.get_pos(), end.get_pos())

                # adding the neighbor to the open set, to be looked at in a following iteration
                if neighbor not in open_set_hash:
                    count += 1
                    open_set.put((f_score[neighbor], count, neighbor))
                    open_set_hash.add(neighbor)
                    neighbor.set_status('open')
        
        # update drawing for the visualization
        draw()

        # all squares except start can be set to closed after they have been looked at
        if current != start:
            current.set_status('closed')

    return False

# this function creates a grid of squares
def make_grid(size, rows, columns, win_length, win_height):
    grid = []
    
    for i in range(rows):
        grid.append([])
        
        for j in range(columns):
            sq = Square(i, j, rows, columns, size)
            grid[i].append(sq)
    
    return grid

# this function draws lines at the borders of the squares for easier visualization
def draw_grid(win, size, rows, columns, win_length, win_height):
    for i in range(rows):
        pygame.draw.line(WIN, GREY, (0, i * size), (win_length, i * size,))
    for j in range(columns):
        pygame.draw.line(WIN, GREY, (j * size, 0), (j * size, win_height))

# this function draws the visualization
def draw(win, grid, size, rows, columns, win_length, win_height):
    # first filling the whole window with white, this is common practice with pygame
    win.fill(WHITE)

    # calling draw() for each square in the grid
    for row in grid:
        for sq in row:
            sq.draw(win)

    draw_grid(win, size, rows, columns, win_length, win_height)
    pygame.display.update()

# this function transforms click coordinates into grid row and col
def get_clicked_pos(pos, size):
    x, y = pos

    row = y // size
    col = x // size

    return row, col

# main function with pygame loop
def main():

    grid = make_grid(SQ_SIZE, ROWS, COLUMNS, WIN_LENGTH, WIN_HEIGHT)

    start = None
    end = None

    run = True

    while run:
        draw(WIN, grid, SQ_SIZE, ROWS, COLUMNS, WIN_LENGTH, WIN_HEIGHT)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                run = False

            if pygame.mouse.get_pressed()[0]: # left click to set squares
                pos = pygame.mouse.get_pos()
                row, col = get_clicked_pos(pos, SQ_SIZE)
                sq = grid[row][col]

                if not start and sq != end:
                    start = sq
                    start.set_status('start')

                elif not end and sq != start:
                    end = sq
                    end.set_status('end')

                elif sq != end and sq != start:
                    sq.set_status('barrier')

            elif pygame.mouse.get_pressed()[2]: # right click to reset squares
                pos = pygame.mouse.get_pos()
                
                row, col = get_clicked_pos(pos, SQ_SIZE)

                sq = grid[row][col]
                sq.set_status('new')

                if sq == start:
                    start = None
                elif sq == end:
                    end = None

            if event.type == pygame.KEYDOWN:

                # starting the algorithm; first updating all neighbors once
                if event.key == pygame.K_SPACE and start and end:
                    for row in grid:
                        for sq in row:
                            sq.update_neighbors(grid)
                    
                    algorithm(lambda: draw(WIN, grid, SQ_SIZE, ROWS, COLUMNS, WIN_LENGTH, WIN_HEIGHT), grid, start, end)

                # resetting the whole window (all squares)
                if event.key == pygame.K_c:
                    start = None
                    end = None
                    grid = make_grid(SQ_SIZE, ROWS, COLUMNS, WIN_LENGTH, WIN_HEIGHT)

                if event.key == pygame.K_r:
                    start = None
                    end = None

                    # resetting all squares except barriers
                    for row in grid:
                        for sq in row:
                            if sq.get_status() != 'barrier':
                                sq.set_status('new')

    pygame.quit()



main()