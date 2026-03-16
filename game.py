from constants import (
    BOARD_SIZE,
    HOUSE_OF_REBIRTH,
    HOUSE_OF_HAPPINESS,
    HOUSE_OF_WATER,
    HOUSE_OF_THREE_TRUTHS,
    HOUSE_OF_RE_ATOUM,
    HOUSE_OF_HORUS,
    PLAYER_1,
    PLAYER_2,
)
from dice import SticksDice


class Board:
    def __init__(self):
        self.squares = [0] * BOARD_SIZE
        for i in range(14):
            self.squares[i] = PLAYER_1 if i % 2 == 0 else PLAYER_2

    def copy(self):
        b = Board()
        b.squares = self.squares[:]
        return b


class Game:
    def __init__(self):
        self.board = Board()
        self.current_player = PLAYER_1
        self.dice = SticksDice()
        self.last_roll = 0

        self.pending_trap_returns = {
            PLAYER_1: [],
            PLAYER_2: [],
        }

    @property
    def sticks(self):
        return self.dice.sticks

    def throw_sticks(self):
        self.last_roll = self.dice.roll()
        return self.last_roll

    def apply_start_turn_rules(self, player, dice_roll):
        """
        If player has a piece on Three Truths or Re-Atoum at the start of the turn,
        mark it as "must return at end of turn if not exited".
        """
        self.pending_trap_returns[player] = []

        if self.board.squares[HOUSE_OF_THREE_TRUTHS] == player:
            self.pending_trap_returns[player].append(HOUSE_OF_THREE_TRUTHS)

        if self.board.squares[HOUSE_OF_RE_ATOUM] == player:
            self.pending_trap_returns[player].append(HOUSE_OF_RE_ATOUM)

    def apply_end_turn_rules(self, player):
        pending = self.pending_trap_returns.get(player, [])
        if not pending:
            return

        for idx in pending:
            if 0 <= idx < BOARD_SIZE and self.board.squares[idx] == player:
                self._send_to_rebirth(player, idx)

        self.pending_trap_returns[player] = []

    def get_valid_moves(self, player, dice_roll):
        moves = []
        for i in range(BOARD_SIZE):
            if self.board.squares[i] == player:
                target = i + dice_roll
                if self.can_move(i, target, player, dice_roll):
                    moves.append((i, target))
        return moves

    def can_move(self, current, target, player, dice_roll):
       
        if current == HOUSE_OF_THREE_TRUTHS:
            return target >= BOARD_SIZE and dice_roll == 3

        if current == HOUSE_OF_RE_ATOUM:
            return target >= BOARD_SIZE and dice_roll == 2

        if target >= BOARD_SIZE:
            if current == HOUSE_OF_HORUS:
                return True
            if current == HOUSE_OF_HAPPINESS:
                return dice_roll == 5
            return False

        if current < HOUSE_OF_HAPPINESS and target > HOUSE_OF_HAPPINESS:
            return False

        if self.board.squares[target] == 0:
            return True

        if self.board.squares[target] == player:
            return False

        return True

    def make_move(self, current, target):
        player = self.board.squares[current]
        if player == 0:
            return

        if self.board.squares[HOUSE_OF_HORUS] == player and current != HOUSE_OF_HORUS:
            self._send_to_rebirth(player, HOUSE_OF_HORUS)

        if target >= BOARD_SIZE:
            self.board.squares[current] = 0
            self.apply_end_turn_rules(player)
            return

        t = self.board.squares[target]
        if t != 0 and t != player:
            self.board.squares[target] = player
            self.board.squares[current] = t
        else:
            self.board.squares[target] = player
            self.board.squares[current] = 0

        if target == HOUSE_OF_WATER and self.board.squares[target] == player:
            self._send_to_rebirth(player, HOUSE_OF_WATER)

        self.apply_end_turn_rules(player)

    def check_winner(self):
        p1 = self.board.squares.count(PLAYER_1)
        p2 = self.board.squares.count(PLAYER_2)
        if p1 == 0:
            return PLAYER_1
        if p2 == 0:
            return PLAYER_2
        return None

    def copy(self):
        g = Game()
        g.board = self.board.copy()
        g.current_player = self.current_player
        g.dice.sticks = self.dice.sticks[:]
        g.dice.last = self.dice.last
        g.last_roll = self.last_roll
        g.pending_trap_returns = {
            PLAYER_1: self.pending_trap_returns[PLAYER_1][:],
            PLAYER_2: self.pending_trap_returns[PLAYER_2][:],
        }
        return g

    def _send_to_rebirth(self, player, from_index):
        if self.board.squares[from_index] == player:
            self.board.squares[from_index] = 0

        pos = HOUSE_OF_REBIRTH
        while pos >= 0 and self.board.squares[pos] != 0:
            pos -= 1

        if pos >= 0:
            self.board.squares[pos] = player
        else:
            for back in range(HOUSE_OF_REBIRTH, -1, -1):
                if self.board.squares[back] == 0:
                    self.board.squares[back] = player
                    break
