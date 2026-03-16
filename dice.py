import random

class SticksDice:
    def __init__(self):
        self.sticks = [False, False, False, False]
        self.last = 0

    def roll(self):
        self.sticks = [random.choice([True, False]) for _ in range(4)]
        dark = self.sticks.count(False)
        if dark == 0:
            self.last = 5
        elif dark == 4:
            self.last = 4
        else:
            self.last = dark
        return self.last
