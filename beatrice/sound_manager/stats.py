import numpy as np


class RollingAverage:
    def __init__(self, size, weight):
        self.size = size
        self.weight = weight
        self.index = 0
        self.array = np.zeros(self.size, dtype=float)
        self.total_count = 0
        self.total_value = 0

    def add(self, value):
        self.total_value -= self.array[self.index]
        self.array[self.index] = value
        self.total_value += value

        self.index += 1
        if self.total_count < self.size:
            self.total_count += 1
        if self.index >= self.size:
            self.index = 0

    def average(self):
        return self.total_value / self.total_count
