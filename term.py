from __future__ import annotations
from dataclasses import dataclass
from typing import TextIO, List
from sys import stdout

@dataclass
class Color:
    r: int
    g: int
    b: int

def set_foreground_color(c: Color, out: TextIO = stdout):
    out.write("\x1B[38;2;%d;%d;%dm" % (c.r, c.g, c.b))

def reset_foreground_color(out: TextIO = stdout):
    out.write("\x1B[39m")

def set_background_color(c: Color, out: TextIO = stdout):
    out.write("\x1B[48;2;%d;%d;%dm" % (c.r, c.g, c.b))

def reset_background_color(out: TextIO = stdout):
    out.write("\x1B[49m")

def set_cursor(x: int, y: int, out: TextIO = stdout):
    out.write("\x1B[%d;%dH" % (y, x))

def clear_all(out: TextIO = stdout):
    out.write("\x1B[2J")

@dataclass
class Pixel:
    ch: str
    fg: Color|None
    bg: Color|None

    def default() -> Pixel:
        return Pixel(" ", None, None)

class ScreenBuffer:
    ox: int
    oy: int
    width: int
    height: int
    buffer: List[Pixel]

    def __init__(self, ox: int, oy: int, width: int = 0, height: int = 0, init: Pixel = Pixel.default()):
        self.ox = ox
        self.oy = oy
        self.resize(width, height, init)
    
    def resize(self, width: int, height: int, init: Pixel = Pixel.default()):
        self.width = width
        self.height = height

        if self.width == 0 or self.height == 0:
            self.width = 0
            self.height = 0
            self.buffer = []
        else:
            self.buffer = [init] * (self.width * self.height)
    
    def get_pixel(self, x: int, y: int) -> Pixel|None:
        return self.buffer[y * self.width + x]
    
    def put_pixel(self, x: int, y: int, p: Pixel|None):
        self.buffer[y * self.width + x] = p

    def draw(self, out: TextIO = stdout):
        last_fg = None
        last_bg = None

        for y in range(self.height):
            set_cursor(self.ox+1, self.oy+1 + y, out)
            for x in range(self.width):
                pixel = self.get_pixel(x, y)
                if pixel.fg != last_fg:
                    last_fg = pixel.fg
                    if pixel.fg is None:
                        reset_foreground_color(out)
                    else:
                        set_foreground_color(pixel.fg, out)
                if pixel.bg != last_bg:
                    last_bg = pixel.bg
                    if pixel.bg is None:
                        reset_background_color(out)
                    else:
                        set_background_color(pixel.bg, out)
                out.write(pixel.ch)

        reset_foreground_color(out)
        reset_background_color(out)
