from typing import TextIO
from sys import stdout

def set_background_color(r: int, g: int, b: int, out: TextIO = stdout):
    out.write(f"\x1B[48;2;{r};{g};{b}m")

def reset_background_color(out: TextIO = stdout):
    out.write("\x1B[49m")

def set_cursor(x: int, y: int, out: TextIO = stdout):
    out.write(f"\x1B[{y};{x}H")

def next_line(n: int = 1, out: TextIO = stdout):
    out.write(f"\x1B[{n}E")

def clear_all(out: TextIO = stdout):
    out.write("\x1B[2J")
