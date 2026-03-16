import pygame
from constants import PLAYER_1, PLAYER_2, BOARD_SIZE

COLOR_BG = (245, 222, 179) 
COLOR_BOARD = (210, 180, 140) 
COLOR_LINES = (139, 69, 19) 
COLOR_P1 = (255, 255, 255)
COLOR_P2 = (0, 0, 0)
COLOR_HIGHLIGHT = (0, 255, 0)
COLOR_TEXT = (0, 0, 0)
COLOR_SPECIAL = (255, 215, 0) 

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
SQUARE_SIZE = 80
BOARD_OFFSET_X = 100
BOARD_OFFSET_Y = 200

class SenetGUI:
    def __init__(self, game, ai):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Senet - Ancient Egyptian Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 24)
        self.large_font = pygame.font.SysFont('Arial', 40)

        self.game = game
        self.ai = ai

        self.selected_piece = None
        self.valid_moves = []
        self.message = "Press SPACE to Roll Dice"
        self.dice_rolled = False
        self.current_roll = 0
        self.game_over = False
        self.depth_minus_rect = pygame.Rect(800, 600, 40, 40)
        self.depth_plus_rect = pygame.Rect(850, 600, 40, 40)
        self.house_images = {}
        self.load_house_images()
        self.exit_button_rect = pygame.Rect(SCREEN_WIDTH - 140, SCREEN_HEIGHT - 90, 120, 40)
        self.exit_available = False
        self.restart_rect = pygame.Rect(40, SCREEN_HEIGHT - 90, 120, 40)
        self.hint_rect = pygame.Rect(170, SCREEN_HEIGHT - 90, 120, 40)

        self.movable_pieces = set()

        self.pos_map = {}
        for i in range(10):
            self.pos_map[i] = (0, i)
        for i in range(10):
            self.pos_map[10 + i] = (1, 9 - i)
        for i in range(10):
            self.pos_map[20 + i] = (2, i)

        self.hint_message = ""
        self.hint_timer = 0
        self.hint_move = None

        self.ai_move_display = ""
        self.ai_move_display_timer = 0

    def load_house_images(self):
        def load(path):
            return pygame.image.load(path).convert_alpha()
        self.house_images["horus"] = load("assets/image_3.png")           # square 30
        self.house_images["re_atoum"] = load("assets/image_4.png")        # square 29
        self.house_images["three_truths"] = load("assets/image_5.png")    # square 28
        self.house_images["water"] = load("assets/image_6.png")           # square 27
        self.house_images["happiness"] = load("assets/image_7.png")       # square 26
        self.house_images["rebirth"] = load("assets/image_8.png")         # square 15

    def get_screen_pos(self, index):
        if index >= BOARD_SIZE:
            return (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100) 
        row, col = self.pos_map[index]
        x = BOARD_OFFSET_X + col * SQUARE_SIZE
        y = BOARD_OFFSET_Y + row * SQUARE_SIZE
        return x, y

    def get_index_from_pos(self, pos):
        x, y = pos
        x -= BOARD_OFFSET_X
        y -= BOARD_OFFSET_Y

        if x < 0 or y < 0:
            return None

        col = x // SQUARE_SIZE
        row = y // SQUARE_SIZE

        if not (0 <= col < 10 and 0 <= row < 3):
            return None

        if row == 0:
            return col
        elif row == 1:
            return 19 - col
        elif row == 2:
            return 20 + col
        return None

    def draw_board(self):
        self.screen.fill(COLOR_BG)

        for i in range(BOARD_SIZE):
            x, y = self.get_screen_pos(i)
            rect = pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE)

            color = COLOR_BOARD
            if i == 14: color = (230, 210, 170)
            elif i == 25: color = (230, 210, 170)
            elif i == 26: color = (240, 240, 210)
            elif i == 27: color = (230, 210, 170)
            elif i == 28: color = (240, 240, 210)
            elif i == 29: color = (230, 210, 170)

            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, COLOR_LINES, rect, 2)

            text = self.font.render(str(i + 1), True, (100, 100, 100))
            self.screen.blit(text, (x + 5, y + 5))

            self.draw_symbols(i, x, y)

            piece = self.game.board.squares[i]
            if piece != 0:
                center = (x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2)
                p_color = COLOR_P1 if piece == PLAYER_1 else COLOR_P2
                pygame.draw.circle(self.screen, p_color, center, SQUARE_SIZE // 3)
                pygame.draw.circle(self.screen, (100, 100, 100), center, SQUARE_SIZE // 3, 2)

        for idx in self.movable_pieces:
            if 0 <= idx < BOARD_SIZE:
                x, y = self.get_screen_pos(idx)
                border_rect = pygame.Rect(x + 3, y + 3, SQUARE_SIZE - 6, SQUARE_SIZE - 6)
                pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, border_rect, width=6, border_radius=12)

        if self.selected_piece is not None:
            x, y = self.get_screen_pos(self.selected_piece)
            pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, (x, y, SQUARE_SIZE, SQUARE_SIZE), 3)

        for move in self.valid_moves:
            target = move[1]
            if target < BOARD_SIZE:
                x, y = self.get_screen_pos(target)
                pygame.draw.circle(self.screen, COLOR_HIGHLIGHT, (x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2), 10)
            else:
                text = self.font.render("Exit", True, COLOR_HIGHLIGHT)
                self.screen.blit(text, (SCREEN_WIDTH - 80, SCREEN_HEIGHT - 80))

        title = self.large_font.render("SENET", True, COLOR_TEXT)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - 50, 50))

        info = self.font.render(
            f"Current Player: {'Human (White)' if self.game.current_player == PLAYER_1 else 'AI (Black)'}",
            True, COLOR_TEXT
        )
        self.screen.blit(info, (50, 100))

        dice_text = self.font.render(f"Last Roll: {self.current_roll}", True, COLOR_TEXT)
        self.screen.blit(dice_text, (50, 140))

        msg = self.font.render(self.message, True, (0, 0, 150))
        self.screen.blit(msg, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 50))

        if self.ai_move_display and self.ai_move_display_timer > 0:
            ai_msg = self.font.render(self.ai_move_display, True, (200, 0, 0))
            ai_rect = ai_msg.get_rect(center=(SCREEN_WIDTH // 2, BOARD_OFFSET_Y + 3 * SQUARE_SIZE + 30))
            bg_rect = ai_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, (255, 230, 230), bg_rect)
            pygame.draw.rect(self.screen, (200, 0, 0), bg_rect, 2)
            self.screen.blit(ai_msg, ai_rect)
            self.ai_move_display_timer -= 1

        if self.hint_message and self.hint_timer > 0:
            hint_msg = self.font.render(self.hint_message, True, (0, 100, 200))
            hint_rect = hint_msg.get_rect(center=(SCREEN_WIDTH // 2, 190))
            bg_rect = hint_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, (200, 220, 255), bg_rect)
            pygame.draw.rect(self.screen, (0, 100, 200), bg_rect, 2)
            self.screen.blit(hint_msg, hint_rect)
            self.hint_timer -= 1

            if self.hint_move:
                x, y = self.get_screen_pos(self.hint_move[0])
                pygame.draw.rect(self.screen, (0, 150, 255), (x, y, SQUARE_SIZE, SQUARE_SIZE), 4)

                if self.hint_move[1] < BOARD_SIZE:
                    x, y = self.get_screen_pos(self.hint_move[1])
                    pygame.draw.circle(self.screen, (0, 150, 255), (x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2), 15)

        stick_y = 100
        stick_x = SCREEN_WIDTH - 200
        for i, is_light in enumerate(self.game.sticks):
            color = (255, 255, 255) if is_light else (50, 50, 50)
            pygame.draw.rect(self.screen, color, (stick_x + i * 30, stick_y, 20, 80))
            pygame.draw.rect(self.screen, (0, 0, 0), (stick_x + i * 30, stick_y, 20, 80), 2)

        depth_label = self.font.render(f"AI Depth: {self.ai.max_depth}", True, COLOR_TEXT)
        self.screen.blit(depth_label, (760, 560))
        pygame.draw.rect(self.screen, (180, 180, 180), self.depth_minus_rect)
        pygame.draw.rect(self.screen, (180, 180, 180), self.depth_plus_rect)
        minus_text = self.font.render("-", True, COLOR_TEXT)
        plus_text = self.font.render("+", True, COLOR_TEXT)
        self.screen.blit(minus_text, (810, 610))
        self.screen.blit(plus_text, (860, 610))

        if self.exit_available:
            pygame.draw.rect(self.screen, (60, 150, 60), self.exit_button_rect, border_radius=6)
            exit_text = self.font.render("Exit", True, (255, 255, 255))
            self.screen.blit(exit_text, (self.exit_button_rect.x + 35, self.exit_button_rect.y + 8))

        pygame.draw.rect(self.screen, (150, 60, 60), self.restart_rect, border_radius=6)
        restart_text = self.font.render("Restart", True, (255, 255, 255))
        self.screen.blit(restart_text, (self.restart_rect.x + 20, self.restart_rect.y + 8))

        pygame.draw.rect(self.screen, (60, 120, 60), self.hint_rect, border_radius=6)
        hint_text = self.font.render("Hint", True, (255, 255, 255))
        self.screen.blit(hint_text, (self.hint_rect.x + 35, self.hint_rect.y + 8))

        self.draw_piece_counts()

    def draw_piece_counts(self):
        white_count = self.game.board.squares.count(PLAYER_1)
        black_count = self.game.board.squares.count(PLAYER_2)

        board_height = 3 * SQUARE_SIZE
        panel_height = board_height

        panel_rect = pygame.Rect(10, BOARD_OFFSET_Y, 80, panel_height)
        pygame.draw.rect(self.screen, (220, 200, 160), panel_rect)
        pygame.draw.rect(self.screen, COLOR_LINES, panel_rect, 2)

        human_label = self.font.render("Human", True, COLOR_TEXT)
        human_rect = human_label.get_rect(center=(50, BOARD_OFFSET_Y + 30))
        self.screen.blit(human_label, human_rect)

        human_count_text = self.font.render(str(white_count), True, COLOR_TEXT)
        human_count_rect = human_count_text.get_rect(center=(50, BOARD_OFFSET_Y + 60))
        self.screen.blit(human_count_text, human_count_rect)

        pygame.draw.circle(self.screen, COLOR_P1, (50, BOARD_OFFSET_Y + 100), 16)
        pygame.draw.circle(self.screen, (100, 100, 100), (50, BOARD_OFFSET_Y + 100), 16, 2)

        separator_y = BOARD_OFFSET_Y + panel_height // 2
        pygame.draw.line(self.screen, COLOR_LINES, (20, separator_y), (80, separator_y), 2)

        ai_label = self.font.render("AI", True, COLOR_TEXT)
        ai_rect = ai_label.get_rect(center=(50, separator_y + 30))
        self.screen.blit(ai_label, ai_rect)

        ai_count_text = self.font.render(str(black_count), True, COLOR_TEXT)
        ai_count_rect = ai_count_text.get_rect(center=(50, separator_y + 60))
        self.screen.blit(ai_count_text, ai_count_rect)

        pygame.draw.circle(self.screen, COLOR_P2, (50, separator_y + 100), 16)
        pygame.draw.circle(self.screen, (100, 100, 100), (50, separator_y + 100), 16, 2)

    def draw_symbols(self, i, x, y):
        img = None
        if i == 14: img = self.house_images["rebirth"]
        elif i == 25: img = self.house_images["happiness"]
        elif i == 26: img = self.house_images["water"]
        elif i == 27: img = self.house_images["three_truths"]
        elif i == 28: img = self.house_images["re_atoum"]
        elif i == 29: img = self.house_images["horus"]
        if img:
            pad = 6
            scaled = pygame.transform.smoothscale(img, (SQUARE_SIZE - 2*pad, SQUARE_SIZE - 2*pad))
            bg_rect = pygame.Rect(x + 3, y + 3, SQUARE_SIZE - 6, SQUARE_SIZE - 6)
            pygame.draw.rect(self.screen, (245, 235, 215), bg_rect, border_radius=8)
            pygame.draw.rect(self.screen, (100, 100, 100), bg_rect, 1, border_radius=8)
            self.screen.blit(scaled, (x + pad, y + pad))
