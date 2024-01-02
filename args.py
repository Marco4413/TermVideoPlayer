import argparse
    
def width_spec_type(width_spec, *, width=None, pixel_width=None):
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

    return argparse.Namespace(width=width, pixel_width=pixel_width)

def resolution(res, *, width=None, pixel_width=2, height=None):
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

    setattr(value, "height", height)
    return value

def get_resolution_format():
    return "[[width][:[pixel_width]]]x[height]"

def position(pos, *, x=1, y=1):
    pos_comp = pos.split("p")
    if len(pos_comp) != 2:
        raise ValueError(f"Invalid position: '{pos}'")
    [x_s, y_s] = pos_comp
    
    value = argparse.Namespace(x=x, y=y)
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
