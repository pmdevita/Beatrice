import random

from .base import BaseNickname


class Greg(BaseNickname):
    async def transform_names(self, names: list[tuple[str, int]]) -> list[tuple[str, int]]:
        new_names = []
        for nick in names:
            new_names.append((random.choice(["Greg", "Greggert", "Gregory", "Gregget", "G. Reg.", "Greg", "Greg", "Gregretha", "Gregort", "Gregorian", "Greg"]), nick[1]))
        return new_names



