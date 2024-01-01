import term
from play import play_audio, play_video

from os import path
from threading import Thread, Event
from sys import argv, stdout

def play_audio_thread(*args, **kwargs):
    try:
        play_audio(*args, **kwargs)
    except IndexError:
        # No Audio
        if "ready" in kwargs:
            kwargs["ready"].set()

def print_usage(program: str):
    print("Usage:")
    print(f"  `$ python {program} <path-to-video> [[width_spec]x[height][@[origin]] [...flags]`")
    print( "    width_spec: [width][:[pixel_width]]")
    print( "      pixel_width: default is 2")
    print( "    origin: [x]o[y]")
    print( "    flags:")
    print( "      -noaudio: disables audio playback")

def parse_width_spec(width_spec, width=None, pixel_width=None):
    width_comp = width_spec.split(":")
    width_s = width_comp[0]
    pixel_width_s = ""

    if len(width_comp) == 2:
        pixel_width_s = width_comp[1]
    elif len(width_comp) > 2:
        print(f"Invalid width spec: '{width_spec}'")
        return (False, width, pixel_width)

    if len(width_s) > 0:
        try:
            width = int(width_s)
        except ValueError:
            print("Invalid width value: '{width_s}'")
            return (False, width, pixel_width)
    
    if len(pixel_width_s) > 0:
        try:
            pixel_width = int(pixel_width_s)
        except ValueError:
            print("Invalid pixel width value: '{pixel_width_s}'")
            return (False, width, pixel_width)
        if pixel_width < 1:
            print("Pixel width can't be < 1.")
            return (False, width, pixel_width)

    return (True, width, pixel_width)

def parse_size(size, width=None, pixel_width=None, height=None):
    size_comp = size.split("x")
    if len(size_comp) != 2:
        print(f"Invalid size: '{size}'")
        return (False, width, pixel_width, height)
    
    [width_spec, height_s] = size_comp
    (ok, width, pixel_width) = parse_width_spec(width_spec, width=width, pixel_width=pixel_width)
    if not ok: return (False, width, pixel_width, height)

    if len(height_s) > 0:
        try:
            height = int(height_s)
        except ValueError:
            print(f"Invalid height value: '{height_s}'")
            return (False, width, pixel_width, height)

    return (True, width, pixel_width, height)

def parse_origin(origin, origin_x=None, origin_y=None):
    origin_comp = origin.split("o")
    if len(origin_comp) != 2:
        print(f"Invalid origin: '{origin}'")
        return (False, origin_x, origin_y)

    [origin_x_s, origin_y_s] = origin_comp

    if len(origin_x_s) > 0:
        try:
            origin_x = int(origin_x_s)
        except ValueError:
            print("Invalid origin x value: '{origin_x_s}'")
            return (False, origin_x, origin_y)

    if len(origin_y_s) > 0:
        try:
            origin_y = int(origin_y_s)
        except ValueError:
            print("Invalid origin y value: '{origin_y_s}'")
            return (False, origin_x, origin_y)

    return (True, origin_x, origin_y)

def main(argc, argv) -> int:
    if argc <= 1:
        print("No input file provided.")
        return 1
    
    filepath = argv[1]
    if not path.exists(filepath):
        print(f"No file '{filepath}' found.")
        return 1
    
    width = None
    height = None
    pixel_width = 2
    origin_x = 1
    origin_y = 1

    if argc >= 3:
        transform = argv[2]
        transform_comp = transform.split("@")

        (ok, width, pixel_width, height) = parse_size(transform_comp[0], width=width, pixel_width=pixel_width, height=height)
        if not ok: return 1
        
        if len(transform_comp) == 2:
            (ok, origin_x, origin_y) = parse_origin(transform_comp[1], origin_x=origin_x, origin_y=origin_y)
            if not ok: return 1
        elif len(transform_comp) > 2:
            print(f"Invalid transform: '{transform}'")
            return 1
    
    flags = argv[3:]
    no_audio = "-noaudio" in flags

    term.reset_background_color()
    term.clear_all()

    if no_audio:
        play_video(
            filepath,
            origin_x=origin_x,
            origin_y=origin_y,
            width=width,
            height=height,
            pixel_width=pixel_width
        )
        return 0

    audio_sync = Event()
    video_sync = Event()
    abort = Event()

    audio_thread = Thread(
        name="Thread-Audio",
        target=play_audio_thread,
        args=(filepath,),
        kwargs={
            "sync": video_sync,
            "ready": audio_sync,
            "abort": abort
        }
    )

    try:
        audio_thread.start()
        play_video(
            filepath,
            origin_x=origin_x,
            origin_y=origin_y,
            width=width,
            height=height,
            pixel_width=pixel_width,
            sync=audio_sync,
            ready=video_sync,
            abort=abort
        )
    finally:
        abort.set()
        audio_thread.join()
    return 0


if __name__ == "__main__":
    try:
        if main(len(argv), argv) == 0:
            term.clear_all()
            term.set_cursor(1, 1)
        else:
            print_usage(argv[0])
    except KeyboardInterrupt:
        term.clear_all()
        term.set_cursor(1, 1)
    except Exception:
        term.clear_all()
        term.set_cursor(1, 1)
        raise
