import time
import threading
import pygame
from game import Game
from constants import PLAYER_1, PLAYER_2
from ui import SenetGUI
from senet_ai import SenetAI


class GameController:
    def __init__(self):
        self.game = Game()
        self.ai = SenetAI(depth=3)
        self.gui = SenetGUI(self.game, self.ai)

    def _update_movable_pieces(self, player, roll):
        moves = self.game.get_valid_moves(player, roll)
        self.gui.movable_pieces = set(m[0] for m in moves)
        return moves

    def show_hint(self):
        if self.game.current_player != PLAYER_1 or not self.gui.dice_rolled:
            self.gui.hint_message = "Roll the dice first!"
            self.gui.hint_timer = 120
            self.gui.hint_move = None
            return

        moves = self.game.get_valid_moves(PLAYER_1, self.gui.current_roll)
        if not moves:
            self.gui.hint_message = "No valid moves available!"
            self.gui.hint_timer = 120
            self.gui.hint_move = None
            return

        temp_game = self.game.copy()
        temp_game.current_player = PLAYER_1
        best_move = self.ai.get_best_move_for_player(temp_game, self.gui.current_roll, PLAYER_1)

        if best_move:
            self.gui.hint_move = best_move
            if best_move[1] >= 30:
                self.gui.hint_message = f"Hint: Move from {best_move[0]+1} to EXIT"
            else:
                self.gui.hint_message = f"Hint: Move from {best_move[0]+1} to {best_move[1]+1}"
            self.gui.hint_timer = 90
        else:
            self.gui.hint_message = "No good moves found!"
            self.gui.hint_timer = 120
            self.gui.hint_move = None

    def handle_click(self, pos):
        if self.gui.restart_rect.collidepoint(pos):
            self.reset_game()
            return
        if self.gui.hint_rect.collidepoint(pos):
            self.show_hint()
            return
        if self.gui.game_over:
            return

        if self.gui.exit_available and self.gui.exit_button_rect.collidepoint(pos) and self.gui.selected_piece is not None:
            for move in self.gui.valid_moves:
                if move[0] == self.gui.selected_piece and move[1] >= 30:
                    self.game.make_move(self.gui.selected_piece, move[1])
                    self.end_turn()
                    return

        if self.gui.depth_minus_rect.collidepoint(pos):
            self.ai.max_depth = max(1, self.ai.max_depth - 1)
            return
        if self.gui.depth_plus_rect.collidepoint(pos):
            self.ai.max_depth = min(6, self.ai.max_depth + 1)
            return

        if self.game.current_player == PLAYER_1:
            if not self.gui.dice_rolled:
                return
            else:
                index = self.gui.get_index_from_pos(pos)

                move_made = False
                for move in self.gui.valid_moves:
                    if move[1] == index:
                        self.game.make_move(self.gui.selected_piece, index)
                        self.end_turn()
                        move_made = True
                        break

                if move_made:
                    return

                if index is not None and self.game.board.squares[index] == PLAYER_1:
                    self.gui.selected_piece = index
                    all_moves = self.game.get_valid_moves(PLAYER_1, self.gui.current_roll)
                    self.gui.valid_moves = [m for m in all_moves if m[0] == index]
                    self.gui.exit_available = any(m[1] >= 30 for m in self.gui.valid_moves)
                else:
                    self.gui.selected_piece = None
                    self.gui.valid_moves = []
                    self.gui.exit_available = False

    def end_turn(self):
        self.gui.selected_piece = None
        self.gui.valid_moves = []
        self.gui.dice_rolled = False
        self.gui.exit_available = False

        self.gui.movable_pieces = set()

        self.game.current_player = 3 - self.game.current_player

        if self.game.current_player == PLAYER_1:
            self.gui.message = "Your Turn. Press SPACE to Roll."
        else:
            self.gui.message = "AI Turn..."

    def reset_game(self):
        self.game = Game()
        if hasattr(self.ai, "tt"):
            self.ai.tt.clear()
        self.gui.game = self.game
        self.gui.selected_piece = None
        self.gui.valid_moves = []
        self.gui.message = "Press SPACE to Roll Dice"
        self.gui.dice_rolled = False
        self.gui.current_roll = 0
        self.gui.game_over = False
        self.gui.exit_available = False
        self.gui.hint_message = ""
        self.gui.hint_timer = 0
        self.gui.hint_move = None
        self.gui.ai_move_display = ""
        self.gui.ai_move_display_timer = 0

        self.gui.movable_pieces = set()

    def run(self):
        running = True
        while running:
            self.gui.draw_board()
            pygame.display.flip()
            self.gui.clock.tick(30)

            winner = self.game.check_winner()
            if winner:
                self.gui.game_over = True
                self.gui.message = f"Game Over! {'Human' if winner == PLAYER_1 else 'AI'} Wins!"

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(pygame.mouse.get_pos())
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if not self.gui.game_over and not self.gui.dice_rolled and self.game.current_player == PLAYER_1:
                            self.gui.current_roll = self.game.throw_sticks()
                            self.game.apply_start_turn_rules(PLAYER_1, self.gui.current_roll)
                            self.gui.dice_rolled = True

                            moves = self._update_movable_pieces(PLAYER_1, self.gui.current_roll)

                            if not moves:
                                self.game.apply_end_turn_rules(PLAYER_1)
                                self.gui.message = f"Rolled {self.gui.current_roll}. No moves! Press SPACE for AI."
                                self.game.current_player = PLAYER_2
                                self.gui.dice_rolled = False
                                self.gui.movable_pieces = set()
                            else:
                                self.gui.message = f"Rolled {self.gui.current_roll}. Select a piece."
                    elif event.key == pygame.K_r:
                        self.reset_game()

            if not self.gui.game_over and self.game.current_player == PLAYER_2:
                pygame.event.pump()
                time.sleep(0.3)

                self.gui.current_roll = self.game.throw_sticks()
                self.game.apply_start_turn_rules(PLAYER_2, self.gui.current_roll)

                self.gui.movable_pieces = set()

                self.gui.message = f"AI Rolled {self.gui.current_roll}..."
                self.gui.draw_board()
                pygame.display.flip()
                time.sleep(0.3)

                self.gui.message = f"AI Thinking (Roll {self.gui.current_roll})..."
                self.gui.draw_board()
                pygame.display.flip()

                result = {"move": None}
                snapshot_game = self.game.copy()
                snapshot_roll = self.gui.current_roll

                def ai_worker():
                    result["move"] = self.ai.get_best_move(snapshot_game, snapshot_roll)

                t = threading.Thread(target=ai_worker, daemon=True)
                t.start()

                while t.is_alive():
                    pygame.event.pump()
                    self.gui.draw_board()
                    pygame.display.flip()
                    self.gui.clock.tick(30)

                move = result["move"]

                if move:
                    self.game.make_move(move[0], move[1])
                    if move[1] >= 30:
                        self.gui.ai_move_display = f"AI moved from {move[0]+1} to EXIT"
                    else:
                        self.gui.ai_move_display = f"AI moved from {move[0]+1} to {move[1]+1}"
                    self.gui.ai_move_display_timer = 180
                    self.gui.message = f"AI moved from {move[0]+1} to {move[1]+1}"
                else:
                    self.game.apply_end_turn_rules(PLAYER_2)
                    self.gui.message = f"AI has no moves!"

                time.sleep(0.3)
                self.end_turn()
