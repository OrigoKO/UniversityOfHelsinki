class Mazebuilder:

    # Mazebuilder is a class with a sole purpose of building a randomized maze
    # This is done using 'randomized depth-first search' (https://en.wikipedia.org/wiki/Maze_generation_algorithm)
    # The method build_maze() returns a matrix of 1's and 0's representing the maze
    # where 1 is a wall and 0 is a corridor

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.maze = [[1 for i in range(height)] for i in range(width)] # a maze with only walls
    
    def build_maze(self):
        pos = 0,0 # starting position of a mazebuilder
        cells = [pos] # all the steps taken by the Mazebuilder are stored according to the building procedure
        self.corridor_build(pos, pos) # adds the first piece of a corridor
        while True:
            new_pos = self.new_cell(pos)
            if pos == new_pos: # deadend, algorithm is backtracking and trying a new dierectoin
                cells.pop()
                if len(cells) == 0: # no new directions left, the maze is ready!
                    break
                pos = cells[-1]
            else:
                self.corridor_build(pos, new_pos)
                pos = new_pos
                cells.append(pos)
        return self.maze

    def new_cell(self, old_pos: tuple):
        # Randomly selects a new cell from available dierections
        directions = self.available_directions(old_pos)
        if len(directions) == 0: # no new directions available!
            return old_pos
        dir = randint(0,len(directions)-1)
        new_pos = directions[dir][0] + old_pos[0], directions[dir][1] + old_pos[1]
        return new_pos
        
    def available_directions(self, position: tuple):
        # Returns a list of directions around the current cell
        # where it's possible to continue according to the rules
        # Taking 2 steps as there's suppose to be a wall in between!
        steps = [(0, -2), (2, 0), (0, 2), (-2, 0)] # up, right, down, left
        directions = [dir for dir in steps if self.is_cell_ok(position, dir)]
        return directions

    def is_cell_ok(self, position: tuple, step: tuple):
        # A new piece of a corridor can only be built if its inside the borders
        # and there's not a corridor already  
        if position[0] + step[0] < 0 or position[0] + step[0] >= self.width:
            return False
        if position[1] + step[1] < 0 or position[1] + step[1] >= self.height:
            return False
        elif self.maze[position[0] + step[0]][position[1] + step[1]] == 0:
            return False
        else:
            return True

    def corridor_build(self, old_pos: tuple, new_pos: tuple):
        # Places a corridor in the current location, the new location and the wall in between
        self.maze[old_pos[0]][old_pos[1]] = 0
        self.maze[new_pos[0]][new_pos[1]] = 0
        inbetween_x = new_pos[0] + (old_pos[0] - new_pos[0]) // 2
        inbetween_y = new_pos[1] + (old_pos[1] - new_pos[1]) // 2
        self.maze[inbetween_x][inbetween_y] = 0
    
class Maze_game:

    # This is the main class running the game
    # Class variables are constants controlling how the game works

    coins_in_start = 40
    coin_init_value = 5
    frame_rate = 60
    ghost_level_rate = 25 * frame_rate # n of seconds per level * frame_rate
    player_moving_rate = frame_rate // 12 # how many moves per s

    def __init__(self, width: int, height: int):
        self.maze = Mazebuilder(width, height).build_maze()
        self.game_window = Maze_graphics(width, height)
        self.points = 0
        self.coins = self.coins_init()

    def run_game(self, menu: bool):
        # Main loop for the game
        if menu:
            self.game_window.draw_fill()
            self.new_game()
        clock = pygame.time.Clock()

        keys = {
            pygame.K_UP: (0,-1),
            pygame.K_DOWN: (0,1),
            pygame.K_LEFT: (-1,0),
            pygame.K_RIGHT: (1,0)
        }

        player_x = 0
        player_y = 0
        player_step = (0, 0)
        player_move_timer = 0
        # Places the ghost in the bottom right corner of the maze
        # If the maze dimensios are odd, this is never a wall
        ghost_x = len(self.maze) - 1  
        ghost_y = len(self.maze[0]) - 1
        ghost_step_x = 1
        ghost_step_y = 0
        ghost_timer = 0
        ghost_level = 0
        ghost_level_timer = 0
        game_over = False
        # List of pressed keys, for a better control of movement
        # when several keys are pressed at the same time
        keys_pressed = [] 

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()

                if event.type == pygame.KEYDOWN:
                    if event.key in keys:
                        keys_pressed.append(event.key)
                        player_step = keys[event.key]
                        player_move_timer = 0
                        player_x, player_y = self.move_player(player_x, player_y, player_step)
                
                if event.type == pygame.KEYUP:
                    if event.key in keys:
                        keys_pressed.remove(event.key)

            if player_move_timer > Maze_game.player_moving_rate and len(keys_pressed) > 0:
                player_move_timer = 0
                player_step = keys[keys_pressed[-1]]
                player_x, player_y = self.move_player(player_x, player_y, player_step)

            if self.is_ghost_moving(ghost_timer, ghost_level):
                ghost_timer = 0
                ghost_x, ghost_y, ghost_step_x, ghost_step_y = self.move_ghost(ghost_x, ghost_y, ghost_step_x, ghost_step_y)

            self.game_window.draw_score(self.points, ghost_level)
            self.game_window.draw_maze(self.maze)
            self.game_window.draw_coins(self.coins)
            self.game_window.draw_player(player_x,player_y)
            self.game_window.draw_ghost(ghost_x, ghost_y)

            ghost_timer += 1
            ghost_level_timer +=1
            player_move_timer +=1

            if ghost_level_timer > Maze_game.ghost_level_rate:
                ghost_level_timer = 0
                ghost_level += 1

            pygame.display.flip()
            game_over = self.is_game_over(player_x, player_y, ghost_x, ghost_y)
            clock.tick(Maze_game.frame_rate)

            if game_over:
                if not self.new_game(self.points, True):
                    exit()
                break 

    def corridors(self):
        # Returns a list of coordinates for all of the corridor cells in the maze
        corridors = []
        for i in range(len(self.maze)):
            for j in range(len(self.maze[0])):
                if self.maze[i][j] == 0:
                    corridors.append((i, j))
        return corridors
    
    def move_player(self, x: int, y: int, steps: tuple):
        # Moves the player to a new position if allowed
        if self.ok_to_move(x + steps[0], y + steps[1]):
            if (x + steps[0], y + steps[1]) in self.coins:
                self.points += 1
                self.coins.remove((x + steps[0], y + steps[1]))
                self.new_coin()
            return x + steps[0], y + steps[1]
        else:
            return x, y
       
    def ok_to_move(self, x: int, y: int):
        # Checks if the position is a corridor 
        if (x, y) in self.corridors():
            return True
        else:
            return False

    def move_ghost(self, x: int, y: int, x_step: int, y_step: int):
        # x_step and y_step are the forward direction at the moment
        # In a straight corridor, the ghost will move forward
        # In a crossing, a new direction is randomly selected
        # The ghost will only turn back if no other direction is available!

        directions = [(0,-1),(1,0),(0,1),(-1,0)] # up, right, down, left
        i = directions.index((x_step, y_step)) # right = i-3, left = i-1, back = i-2
        avail_dir = self.available_directions(x, y)

        if len(avail_dir) == 1: # if there's only one option, that is the chosen direction
            return x + avail_dir[0][0], y + avail_dir[0][1], avail_dir[0][0], avail_dir[0][1]
        
        if directions[i-2] in avail_dir: # with more than one option, turning back is removed
            avail_dir.remove(directions[i-2])

        new_step = choice(avail_dir) # a random choice of remaining alternatives
        return (x + new_step[0], y + new_step[1], new_step[0], new_step[1])
    
    def available_directions(self, x: int, y: int):
        # Returns a list of tuples, corresponding to available directions for movement
        directions = [(0,-1),(1,0),(0,1),(-1,0)]
        available_directions = [dir for dir in directions if self.ok_to_move(x + dir[0], y + dir[1])]
        return available_directions

    def coins_init(self):
        # Spreads the coins around the maze in the beginning of a game
        return sample(self.corridors(), Maze_game.coins_in_start)

    def new_coin(self):
        # Randomly places a new coin in a free spot in the maze
        available_places = [position for position in self.corridors() if position not in self.coins]
        self.coins.append(choice(available_places))

    def is_ghost_moving(self, timer: int, level: int):
        # Handles the timing and speed of the ghost's movement
        moves_per_s = [1, 2, 2.5, 3, 4, 5, 6, 7, 9, 10, 11, 12, 14, 17, 20, 30]
        if level >= len(moves_per_s):
            level = len(moves_per_s) - 1
        if timer > Maze_game.frame_rate / moves_per_s[level]:
            return True
        else:
            return False
    
    def is_game_over(self, p_x: int, p_y: int, g_x:int, g_y: int):
        # Checks if the player and the ghost are in the same position
        if p_x == g_x and p_y == g_y:
            return True
        else:
            return False
    
    def new_game(self, score = 0, show_scores = False):
        # Prints the score (if required) and asks if another game is wanted
        self.game_window.draw_menu(score, show_scores)
        pygame.display.flip()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        return False
                    if event.key == pygame.K_SPACE:
                        return True

class Maze_graphics:

    # This class handles all the graphical output of the game
    # Class variables to control general visuals of the game

    wall_color = (167,95,59)
    coin_color = (55,120,87)
    bg_color = (230,223,204)
    border_color = (65,37,23)
    coin_size = 7
    cell_size = 44
    border_size = 30

    def __init__(self, width: int, height: int):
        pygame.init()
        self.width = width
        self.height = height
        window_width = self.width * Maze_graphics.cell_size + 2 * Maze_graphics.border_size
        window_height = self.height * Maze_graphics.cell_size + 2 * Maze_graphics.border_size
        self.window = pygame.display.set_mode((window_width, window_height))
        self.ghost = pygame.image.load("hirvio.png")
        self.player = pygame.image.load("robo.png")
    
    def draw_fill(self):
        # Fills the window with background color
        self.window.fill(Maze_graphics.bg_color)
    
    def draw_score(self, points: int, level: int):
        # Shows the curren score in the caption of the window
        pygame.display.set_caption(f"LEVEL: {level} - POINTS: {points}")

    def draw_maze(self, maze: list):
        # Draws the maze walls
        self.draw_fill()
        for i in range(self.width):
            for j in range(self.height):
                if maze[i][j] == 1:
                    x = i * Maze_graphics.cell_size + Maze_graphics.border_size
                    y = j * Maze_graphics.cell_size + Maze_graphics.border_size
                    pygame.draw.rect(self.window, Maze_graphics.wall_color, pygame.Rect(x, y, Maze_graphics.cell_size, Maze_graphics.cell_size))
        pygame.draw.rect(self.window, Maze_graphics.border_color, pygame.Rect(Maze_graphics.border_size, Maze_graphics.border_size, self.width * Maze_graphics.cell_size, self.height * Maze_graphics.cell_size), 2)

    def draw_player(self, x: int, y: int):
        # Draws the player in the given position
        vertical_correction = self.player.get_height() // 12 
        x = x * Maze_graphics.cell_size + Maze_graphics.cell_size // 2 - self.player.get_width() // 2
        y = y * Maze_graphics.cell_size + Maze_graphics.cell_size // 2 - self.player.get_height() // 2 - vertical_correction
        x += Maze_graphics.border_size
        y += Maze_graphics.border_size
        self.window.blit(self.player, (x, y))
  
    def draw_coins(self, coins: list):
        # Draws the coins in the maze
        for coin in coins:
            size = self.coin_size
            center = Maze_graphics.cell_size // 2
            x = coin[0] * Maze_graphics.cell_size + center
            y = coin[1] * Maze_graphics.cell_size + center
            x += Maze_graphics.border_size
            y += Maze_graphics.border_size
            pygame.draw.circle(self.window, Maze_graphics.coin_color, (x, y), size)

    def draw_ghost(self, x: int, y: int):
        # Draws the ghost in the given position
        x = x * Maze_graphics.cell_size + Maze_graphics.cell_size // 2 - self.ghost.get_width() // 2
        y = y * Maze_graphics.cell_size + Maze_graphics.cell_size // 2 - self.ghost.get_height() // 2
        x += Maze_graphics.border_size
        y += Maze_graphics.border_size
        self.window.blit(self.ghost, (x, y))
    
    def draw_menu(self, score: int, print_scores: bool):
        # Draws the menu in the beginning and the end of the game
        box_width = 600
        box_height = 250
        x = self.width * Maze_graphics.cell_size // 2 - box_width // 2
        y = self.height * Maze_graphics.cell_size // 2 - box_height // 2
        instructions = f"Press space for a new game - Q to quit"
        pygame.draw.rect(self.window, (0,0,0), pygame.Rect(x, y, box_width, box_height))
        font = pygame.font.SysFont("Arial", 28)
        text_x = x + 50
        text_y = y + 65
        if print_scores:
            results = f"You scored {score} points"
            text = font.render(results, True, Maze_graphics.bg_color)
            self.window.blit(text, (text_x, text_y))
            text_y += 70

        text = font.render(instructions, True, Maze_graphics.bg_color)
        self.window.blit(text, (text_x, text_y))

import pygame
from random import randint, sample, choice
maze_x = 27
maze_y = 17
newgame = Maze_game(maze_x,maze_y)
newgame.run_game(True)
while True:
    newgame = Maze_game(maze_x,maze_y)
    newgame.run_game(False)