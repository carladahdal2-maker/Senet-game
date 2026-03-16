import hashlib
import math
from collections import OrderedDict  

from constants import BOARD_SIZE, PLAYER_1, PLAYER_2
from game import Game


class SenetAI:
    def __init__(self, depth=2):
        import os

        self.max_depth = depth
        self.nodes_visited = 0

        self.tt = OrderedDict()
        self.tt_max = 50000

        self.position_history = []

        self.probabilities = self.compute_stick_probabilities()

        env_level = os.environ.get("SENET_DEBUG", "").strip()
        if env_level == "":
            self.debug_level = 1
        else:
            try:
                self.debug_level = int(env_level)
            except ValueError:
                self.debug_level = 1

        self.trace_enabled = (self.debug_level >= 2)

        try:
            self.trace_node_limit = int(os.environ.get("SENET_TRACE_LIMIT", "5000"))
        except ValueError:
            self.trace_node_limit = 5000

        self._trace_printed = 0
        self._trace_root_depth = 0

    def initial_state(self):
        """Initial state for the search problem."""
        g = Game()
        return g

    def state(self, game, player, dice_roll):
        """A state representation: board + current player + dice roll (when relevant)."""
        return (tuple(game.board.squares), player, int(dice_roll))

    def actions(self, game, player, dice_roll):
        """Available actions from state."""
        return game.get_valid_moves(player, dice_roll)

    def transition(self, game, move):
        """State transition: apply action on a copy and return new game."""
        new_game = game.copy()
        new_game.make_move(move[0], move[1])
        return new_game

    @staticmethod
    def step_cost(move):
        """Uniform move cost (Req #1: cost)."""
        return 1

    @staticmethod
    def goal_test(game):
        """Goal test: terminal if winner exists."""
        return game.check_winner() is not None

    @staticmethod
    def compute_stick_probabilities():
        """
        4 sticks, each side equiprobable.
        Your dice mapping:
          dark_count == 0 -> roll 5
          dark_count == 4 -> roll 4
          else -> roll = dark_count (1..3)
        """
        import itertools

        counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total = 0

        for sticks in itertools.product([True, False], repeat=4):
            total += 1
            dark = sticks.count(False)

            if dark == 0:
                r = 5
            elif dark == 4:
                r = 4
            else:
                r = dark

            counts[r] += 1

        return {r: counts[r] / total for r in sorted(counts)}

    def _trace(self, msg, depth):
        if not self.trace_enabled:
            return
        if self._trace_printed >= self.trace_node_limit:
            if self._trace_printed == self.trace_node_limit:
                print("[TRACE] Limit reached. Further trace output suppressed.")
                self._trace_printed += 1
            return
        indent = "  " * max(0, (self._trace_root_depth - depth))
        print(f"{indent}{msg}")
        self._trace_printed += 1

    def _store_tt(self, key, value):
        self.tt[key] = value
        if len(self.tt) > self.tt_max:
            self.tt.popitem(last=False)

    def get_position_hash(self, board_squares, player, dice_roll):
        board_str = ''.join(map(str, board_squares)) + str(player) + str(dice_roll)
        return hashlib.md5(board_str.encode()).hexdigest()[:16]

    def order_moves(self, game, moves, player):
        scored_moves = []
        for move in moves:
            score = 0

            if move[1] < BOARD_SIZE:
                score += (move[1] - move[0])
            else:
                score += 100

            if move[1] < BOARD_SIZE and game.board.squares[move[1]] != 0 and game.board.squares[move[1]] != player:
                score += 50

            scored_moves.append((score, move))

        scored_moves.sort(reverse=True)
        return [m for s, m in scored_moves]

    def get_best_move(self, game, dice_roll):
        self.nodes_visited = 0
        self.position_history.clear()
        self._trace_printed = 0
        self._trace_root_depth = self.max_depth

        moves = game.get_valid_moves(PLAYER_2, dice_roll)

        if not moves:
            if self.debug_level >= 1:
                print("Nodes Visited: 0")
                print("Best Move: None | Best Value: -inf")
            return None

        moves = self.order_moves(game, moves, PLAYER_2)

        if len(moves) == 1:
            move = moves[0]
            new_game = game.copy()
            new_game.make_move(move[0], move[1])

            pos_hash = self.get_position_hash(new_game.board.squares, PLAYER_1, 0)
            self.position_history.append(pos_hash)

            val = self.expectiminimax(new_game, self.max_depth - 1, is_chance=True, is_maximizing=False)

            self.position_history.pop()

            if self.debug_level >= 1:
                print(f"Nodes Visited: {self.nodes_visited}")
                print(f"Best Move: {move} | Best Value: {val:.4f}")
            return move

        best_val = -math.inf
        best_move = None

        if self.trace_enabled:
            self._trace(f"[ROOT] AI evaluating {len(moves)} moves for roll={dice_roll}", self.max_depth)

        for move in moves:
            new_game = game.copy()
            new_game.make_move(move[0], move[1])

            pos_hash = self.get_position_hash(new_game.board.squares, PLAYER_1, 0)
            self.position_history.append(pos_hash)

            val = self.expectiminimax(new_game, self.max_depth - 1, is_chance=True, is_maximizing=False)

            self.position_history.pop()

            if self.trace_enabled:
                self._trace(f"[ROOT] move={move} -> value={val:.4f}", self.max_depth)

            if val > best_val:
                best_val = val
                best_move = move

        if self.debug_level >= 1:
            print(f"Nodes Visited: {self.nodes_visited}")
            print(f"Best Move: {best_move} | Best Value: {best_val:.4f}")

        return best_move

    def get_best_move_for_player(self, game, dice_roll, player):
        """
        Used for hints.
        evaluate() is from PLAYER_2 perspective (higher is better for AI),
        so PLAYER_1 chooses the move that MINIMIZES that score.
        """
        self.nodes_visited = 0
        self.position_history.clear()
        self._trace_printed = 0
        self._trace_root_depth = self.max_depth

        moves = game.get_valid_moves(player, dice_roll)
        if not moves:
            return None

        moves = self.order_moves(game, moves, player)

        if len(moves) == 1:
            return moves[0]

        best_move = None
        best_val = -math.inf if player == PLAYER_2 else math.inf

        for move in moves:
            new_game = game.copy()
            new_game.make_move(move[0], move[1])

            next_player = 3 - player
            pos_hash = self.get_position_hash(new_game.board.squares, next_player, 0)
            self.position_history.append(pos_hash)

            val = self.expectiminimax(
                new_game,
                self.max_depth - 1,
                is_chance=True,
                is_maximizing=(next_player == PLAYER_2)
            )

            self.position_history.pop()

            if player == PLAYER_2:
                if val > best_val:
                    best_val = val
                    best_move = move
            else:
                if val < best_val:
                    best_val = val
                    best_move = move

        return best_move

    def expectiminimax(self, game, depth, is_chance, is_maximizing, dice_roll=0):
        self.nodes_visited += 1

        node_type = "CHANCE" if is_chance else ("MAX(AI)" if is_maximizing else "MIN(HUMAN)")
        current_player = PLAYER_2 if is_maximizing else PLAYER_1

        pos_hash = self.get_position_hash(game.board.squares, current_player, dice_roll)
        key = (pos_hash, depth, is_chance, is_maximizing, dice_roll)

        # TT hit
        if key in self.tt:
            val = self.tt[key]
            self.tt.move_to_end(key)
            self._trace(f"[TT] {node_type} depth={depth} roll={dice_roll} -> {val:.4f}", depth)
            return val

        if pos_hash in self.position_history[:-1]:
            self._trace(f"[REPEAT] {node_type} depth={depth} roll={dice_roll} -> 0.0000", depth)
            return 0.0

        winner = game.check_winner()
        if winner == PLAYER_2:
            v = 10000.0
            self._store_tt(key, v)
            self._trace(f"[TERM] AI WIN depth={depth} -> {v:.1f}", depth)
            return v
        if winner == PLAYER_1:
            v = -10000.0
            self._store_tt(key, v)
            self._trace(f"[TERM] HUMAN WIN depth={depth} -> {v:.1f}", depth)
            return v

        if depth == 0:
            v = float(self.evaluate(game))
            self._store_tt(key, v)
            self._trace(f"[EVAL] depth=0 -> {v:.4f}", depth)
            return v

        self._trace(f"[ENTER] {node_type} depth={depth} roll={dice_roll}", depth)

        if is_chance:
            expected_value = 0.0
            child_depth = depth - 1  
            for roll, prob in self.probabilities.items():
                child_val = self.expectiminimax(
                    game,
                    child_depth,
                    is_chance=False,
                    is_maximizing=is_maximizing,
                    dice_roll=roll
                )
                expected_value += child_val * prob
                self._trace(f"[CHANCE] roll={roll} prob={prob:.4f} child={child_val:.4f}", depth)

            self._store_tt(key, expected_value)
            self._trace(f"[RETURN] CHANCE depth={depth} -> {expected_value:.4f}", depth)
            return expected_value

        if is_maximizing:
            base_game = game.copy()
            if hasattr(base_game, "apply_start_turn_rules"):
                base_game.apply_start_turn_rules(PLAYER_2, dice_roll)

            moves = base_game.get_valid_moves(PLAYER_2, dice_roll)
            if not moves:
                if hasattr(base_game, "apply_end_turn_rules"):
                    base_game.apply_end_turn_rules(PLAYER_2)

                v = self.expectiminimax(base_game, depth - 1, is_chance=True, is_maximizing=False)
                self._store_tt(key, v)
                self._trace(f"[PASS] MAX no-moves depth={depth} -> {v:.4f}", depth)
                return v

            moves = self.order_moves(base_game, moves, PLAYER_2)
            max_val = -math.inf

            for move in moves:
                new_game = base_game.copy()
                new_game.make_move(move[0], move[1])

                new_pos_hash = self.get_position_hash(new_game.board.squares, PLAYER_1, 0)
                self.position_history.append(new_pos_hash)

                val = self.expectiminimax(new_game, depth - 1, is_chance=True, is_maximizing=False)

                self.position_history.pop()

                self._trace(f"[MAX] move={move} -> {val:.4f}", depth)

                if val > max_val:
                    max_val = val
                if max_val > 5000:
                    break

            self._store_tt(key, max_val)
            self._trace(f"[RETURN] MAX depth={depth} -> {max_val:.4f}", depth)
            return max_val

        else:
            base_game = game.copy()
            if hasattr(base_game, "apply_start_turn_rules"):
                base_game.apply_start_turn_rules(PLAYER_1, dice_roll)

            moves = base_game.get_valid_moves(PLAYER_1, dice_roll)
            if not moves:
                if hasattr(base_game, "apply_end_turn_rules"):
                    base_game.apply_end_turn_rules(PLAYER_1)

                v = self.expectiminimax(base_game, depth - 1, is_chance=True, is_maximizing=True)
                self._store_tt(key, v)
                self._trace(f"[PASS] MIN no-moves depth={depth} -> {v:.4f}", depth)
                return v

            moves = self.order_moves(base_game, moves, PLAYER_1)
            min_val = math.inf

            for move in moves:
                new_game = base_game.copy()
                new_game.make_move(move[0], move[1])

                new_pos_hash = self.get_position_hash(new_game.board.squares, PLAYER_2, 0)
                self.position_history.append(new_pos_hash)

                val = self.expectiminimax(new_game, depth - 1, is_chance=True, is_maximizing=True)

                self.position_history.pop()

                self._trace(f"[MIN] move={move} -> {val:.4f}", depth)

                if val < min_val:
                    min_val = val
                if min_val < -5000:
                    break

            self._store_tt(key, min_val)
            self._trace(f"[RETURN] MIN depth={depth} -> {min_val:.4f}", depth)
            return min_val

    def evaluate(self, game):
        score = 0

        p2_pieces = 0
        p2_score = 0
        p1_pieces = 0
        p1_score = 0

        for i in range(BOARD_SIZE):
            if game.board.squares[i] == PLAYER_2:
                p2_pieces += 1
                p2_score += (i + 1)
                if i >= 25:
                    p2_score += 5
            elif game.board.squares[i] == PLAYER_1:
                p1_pieces += 1
                p1_score += (i + 1)
                if i >= 25:
                    p1_score += 5

        p2_borne_off = 7 - p2_pieces
        p1_borne_off = 7 - p1_pieces

        score += (p2_borne_off * 50) - (p1_borne_off * 50)
        score += (p2_score - p1_score)

        return score
