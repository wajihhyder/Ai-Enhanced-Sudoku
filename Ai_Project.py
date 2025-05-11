import pygame
import random
import time
from copy import deepcopy

WIDTH, HEIGHT = 800, 600 
GRID_SIZE = 9
CELL_SIZE = 540 // GRID_SIZE
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (200, 200, 200)
BLUE = (0, 0, 255)
GREEN = (0, 200, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 153)
FLASH_COLOR = (255, 200, 200)
CYAN = (0, 255, 255)

# Initialize Pygame
pygame.init()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI-Enhanced Sudoku")
FONT = pygame.font.SysFont("comicsans", 40)
SMALL_FONT = pygame.font.SysFont("comicsans", 30)
TINY_FONT = pygame.font.SysFont("comicsans", 24)

status_message = ""

def is_valid(board, row, col, num):
    for i in range(9):
        if board[row][i] == num or board[i][col] == num:
            return False
        if board[row//3*3 + i//3][col//3*3 + i%3] == num:
            return False
    return True

def solve(board):
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                for num in range(1, 10):
                    if is_valid(board, row, col, num):
                        board[row][col] = num
                        if solve(board):
                            return True
                        board[row][col] = 0
                return False
    return True

class RLAgent:
    def __init__(self):
        self.q_table = {}
        self.actions = ['easy', 'medium', 'hard']
        self.last_state = None
        self.last_action = None

    def get_state(self, time_taken, mistakes):
        speed = 'fast' if time_taken is not None and time_taken < 300 else 'slow'
        accuracy = 'accurate' if mistakes < 5 else 'inaccurate'
        return (speed, accuracy)

    def choose_action(self, state):
        if state not in self.q_table:
            self.q_table[state] = {}
        for action in self.actions:
            if action not in self.q_table[state]:
                self.q_table[state][action] = 0
        action = max(self.q_table[state], key=self.q_table[state].get)
        self.last_state = state
        self.last_action = action
        return action

    def update(self, reward):
        if self.last_state and self.last_action:
            self.q_table[self.last_state][self.last_action] += reward

def fill_diagonal_boxes(board):
    for k in range(0, 9, 3):
        nums = list(range(1, 10))
        random.shuffle(nums)
        for i in range(3):
            for j in range(3):
                board[k+i][k+j] = nums.pop()

def generate_puzzle(difficulty='medium'):
    board = [[0 for _ in range(9)] for _ in range(9)]
    fill_diagonal_boxes(board)
    solve(board)
    puzzle = deepcopy(board)
    remove_count = 30 if difficulty == 'easy' else 40 if difficulty == 'medium' else 50
    while remove_count:
        r, c = random.randint(0, 8), random.randint(0, 8)
        if puzzle[r][c] != 0:
            puzzle[r][c] = 0
            remove_count -= 1
    return puzzle, board

def draw_grid():
    for i in range(GRID_SIZE + 1):
        thick = 4 if i % 3 == 0 else 1
        pygame.draw.line(WIN, BLACK, (0, i * CELL_SIZE), (540, i * CELL_SIZE), thick)
        pygame.draw.line(WIN, BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, 540), thick)

def draw_board(board, fixed, hint_limit, hints_used, selected, frozen, start_time, mistake_count, freeze_cooldown, last_freeze_time):
    WIN.fill(WHITE)
    if selected:
        row, col = selected
        pygame.draw.rect(WIN, YELLOW, (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    for row in range(9):
        for col in range(9):
            if frozen[row][col]:
                pygame.draw.rect(WIN, CYAN, (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            if board[row][col] != 0:
                color = BLACK if fixed[row][col] else BLUE
                text = FONT.render(str(board[row][col]), True, color)
                text_rect = text.get_rect(center=(col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2))
                WIN.blit(text, text_rect)

    draw_grid()

    # Sidebar background
    pygame.draw.rect(WIN, GREY, (540, 0, WIDTH - 540, HEIGHT))
    WIN.blit(SMALL_FONT.render("Game Stats", True, BLACK), (550, 20))
    WIN.blit(TINY_FONT.render(f"Time: {int(time.time() - start_time)}s", True, BLACK), (550, 70))
    WIN.blit(TINY_FONT.render(f"Mistakes: {mistake_count}", True, BLACK), (550, 110))
    WIN.blit(TINY_FONT.render(f"Hints left: {hint_limit - hints_used}", True, BLACK), (550, 150))
    cd = max(0, int(freeze_cooldown - (time.time() - last_freeze_time)))
    WIN.blit(TINY_FONT.render(f"Freeze cooldown: {cd}s", True, BLACK), (550, 190))
    WIN.blit(SMALL_FONT.render("Guide", True, BLACK), (550, 250))
    WIN.blit(TINY_FONT.render("Hint: 'H'", True, BLACK), (550, 300))
    WIN.blit(TINY_FONT.render("Freeze: 'F'", True, BLACK), (550, 340))
    WIN.blit(TINY_FONT.render(status_message, True, RED if "incorrect" in status_message.lower() or "hint" in status_message.lower() else GREEN), (550, HEIGHT - 50))
    pygame.display.update()

def reveal_hint(board, fixed, solution, hint_limit, hints_used):
    global status_message
    if hints_used >= hint_limit:
        status_message = "No hints available!"
        return False
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                board[row][col] = solution[row][col]
                fixed[row][col] = True
                status_message = "Hint revealed!"
                return True
    status_message = "No cells to reveal!"
    return False

def flash_warning():
    WIN.fill(FLASH_COLOR)
    pygame.display.update()
    pygame.time.delay(300)

def shift_cells(board, fixed, frozen):
    movable = [(r, c) for r in range(9) for c in range(9) if board[r][c] != 0 and not fixed[r][c] and not frozen[r][c]]
    random.shuffle(movable)
    selected = movable[:3]
    values = [board[r][c] for r, c in selected]
    random.shuffle(selected)
    for (new_r, new_c), val in zip(selected, values):
        board[new_r][new_c] = val

def is_board_solved(board, solution, fixed):
    return all(board[r][c] == solution[r][c] for r in range(9) for c in range(9))

def end_screen(score):
    WIN.fill(WHITE)
    msg = FONT.render(f"Your Score: {score}", True, GREEN)
    WIN.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 20))
    pygame.display.update()
    pygame.time.delay(3000)

def difficulty_menu():
    return 'medium'  # Static for simplicity

def main():
    global status_message
    running_game = True
    while running_game:
        chosen_level = difficulty_menu()
        clock = pygame.time.Clock()
        agent = RLAgent()
        start_time = time.time()
        mistake_count = 0
        hints_used = 0

        puzzle, solution = generate_puzzle(chosen_level)
        board = deepcopy(puzzle)
        fixed = [[puzzle[r][c] != 0 for c in range(9)] for r in range(9)]
        frozen = [[False for _ in range(9)] for _ in range(9)]
        selected = None
        hint_limit = 100
        correct_moves = 0
        freeze_cooldown = 10
        last_freeze_time = -freeze_cooldown

        running = True
        while running:
            clock.tick(FPS)
            draw_board(board, fixed, hint_limit, hints_used, selected, frozen, start_time, mistake_count, freeze_cooldown, last_freeze_time)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    running_game = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    if x < 540:
                        row, col = y // CELL_SIZE, x // CELL_SIZE
                        selected = (row, col)

                if event.type == pygame.KEYDOWN and selected:
                    r, c = selected
                    if event.key == pygame.K_f:
                        current_time = time.time()
                        if frozen[r][c]:
                            frozen[r][c] = False
                            status_message = f"Cell at ({r+1},{c+1}) unfrozen!"
                        elif not fixed[r][c]:
                            if current_time - last_freeze_time >= freeze_cooldown:
                                frozen[r][c] = True
                                last_freeze_time = current_time
                                status_message = f"Cell at ({r+1},{c+1}) frozen!"
                            else:
                                remaining = int(freeze_cooldown - (current_time - last_freeze_time))
                                status_message = f"Freeze on cooldown: wait {remaining}s"
                        else:
                            status_message = "Cannot freeze a fixed cell!"

                    elif not fixed[r][c] and not frozen[r][c]:
                        if event.unicode.isdigit():
                            num = int(event.unicode)
                            if 1 <= num <= 9:
                                if num != solution[r][c]:
                                    mistake_count += 1
                                    status_message = f"Incorrect move!"
                                else:
                                    correct_moves += 1
                                    status_message = "Correct move!"
                                    if correct_moves % 5 == 0:
                                        flash_warning()
                                        status_message = "Grid shifted!"
                                        shift_cells(board, fixed, frozen)
                                board[r][c] = num

                    if event.key == pygame.K_h:
                        if reveal_hint(board, fixed, solution, hint_limit, hints_used):
                            hints_used += 1

            if is_board_solved(board, solution, fixed):
                time_taken = time.time() - start_time
                state = agent.get_state(time_taken, mistake_count + hints_used)
                new_difficulty = agent.choose_action(state)
                agent.update(10 - mistake_count - hints_used)
                score = int(1000 - time_taken - 10 * (mistake_count + hints_used))
                end_screen(score)
                running = False

if __name__ == "__main__":
    try:
        main()
    finally:
        pygame.quit()
