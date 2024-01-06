import argparse
from dataclasses import dataclass
from typing import Optional

@dataclass
class Resolution:
    width: Optional[int]
    pixel_width: Optional[int]
    height: Optional[int]

    def __str__(self):
        res = ""
        if self.width is not None:
            res += str(self.width)
        if self.pixel_width is not None:
            res += f":{self.pixel_width}"
        res += "x"
        if self.height is not None:
            res += str(self.height)
        return res

def width_spec_type(width_spec, *, width=None, pixel_width=None) -> Resolution:
    width_comp = width_spec.split(":")
    width_s = width_comp[0]
    pixel_width_s = ""

    if len(width_comp) == 2:
        pixel_width_s = width_comp[1]
    elif len(width_comp) > 2:
        raise ValueError(f"Invalid width spec: '{width_spec}'")

    if len(width_s) > 0:
        try:
            width = int(width_s)
        except ValueError:
            raise ValueError("Invalid width value: '{width_s}'")
    
    if len(pixel_width_s) > 0:
        try:
            pixel_width = int(pixel_width_s)
        except ValueError:
            raise ValueError("Invalid pixel width value: '{pixel_width_s}'")
        if pixel_width < 1:
            raise ValueError("Pixel width can't be < 1.")

    return Resolution(width, pixel_width, None)

def resolution(res, *, width=None, pixel_width=None, height=None) -> Resolution:
    res_comp = res.split("x")
    if len(res_comp) != 2:
        raise ValueError(f"Invalid resolution: '{res}'")
    
    [width_spec, height_s] = res_comp
    value = width_spec_type(width_spec, width=width, pixel_width=pixel_width)

    if len(height_s) > 0:
        try:
            height = int(height_s)
        except ValueError:
            raise ValueError(f"Invalid height value: '{height_s}'")

    value.height = height
    return value

def get_resolution_format():
    return "[[width][:[pixel_width]]]x[height]"

@dataclass
class Position:
    x: Optional[int]
    y: Optional[int]

    def __str__(self):
        res = ""
        if self.x is not None:
            res += str(self.x)
        res += "p"
        if self.y is not None:
            res += str(self.y)
        return res

def position(pos, *, x=1, y=1) -> Position:
    pos_comp = pos.split("p")
    if len(pos_comp) != 2:
        raise ValueError(f"Invalid position: '{pos}'")
    [x_s, y_s] = pos_comp
    
    value = Position(x, y)
    if len(x_s) > 0:
        try:
            value.x = int(x_s)
        except ValueError:
            raise ValueError(f"Invalid x value: '{x_s}'")
    if len(y_s) > 0:
        try:
            value.y = int(y_s)
        except ValueError:
            raise ValueError(f"Invalid y value: '{y_s}'")

    return value

def get_position_format():
    return "[x]p[y]"
