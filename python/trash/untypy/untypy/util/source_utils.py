from typing import Tuple


class DisplayMatrix:
    chars: dict

    def __init__(self, src: str, max_lines=5):
        self.chars = {}
        self.max_lines = max_lines
        for y, line in enumerate(src.splitlines()):
            for x, char in enumerate(line):
                self.chars[(x, y)] = char

    def write(self, pos: Tuple[int, int], message: str):
        for y, line in enumerate(message.splitlines()):
            for x, char in enumerate(line):
                self.chars[(x + pos[0], y + pos[1])] = char

    def __str__(self):
        # Slow, but this is only in the "error" path
        max_y = 0
        max_x = 0
        for x, y in self.chars:
            max_y = max(max_y, y)
            max_x = max(max_x, x)

        max_y = min(max_y, self.max_lines)
        out = ""
        for y in range(max_y + 1):
            for x in range(max_x + 1):
                if (x, y) in self.chars:
                    out += self.chars[(x, y)]
                else:
                    out += " "
            out += "\n"
        return out
