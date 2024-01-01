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
        return

def print_usage(program: str):
    print("Usage:")
    print("  `$ python %s <path-to-video> [[width_spec]x[height]] [...flags]`" % (program,))
    print("    width_spec: [width][:[pixel_width]]")
    print("      pixel_width: default is 2")
    print("    flags:")
    print("      -noaudio: disables audio playback")

def main(argc, argv) -> int:
    if argc <= 1:
        print("No input file provided.")
        return 1
    
    filepath = argv[1]
    if not path.exists(filepath):
        print("No file '%s' found." % (filepath,))
        return 1
    
    width = None
    height = None
    pixel_width = 2

    if argc >= 3:
        size = argv[2]
        size_comp = size.split("x")
        if len(size_comp) != 2:
            print("Invalid size format: '%s'" % (size,))
            return 1
        
        [width_spec, height_s] = size_comp
        if len(width_spec) > 0:
            width_comp = width_spec.split(":")
            width_s = width_comp[0]
            pixel_width_s = ""

            if len(width_comp) == 2:
                pixel_width_s = width_comp[1]
            elif len(width_comp) > 2:
                print("Invalid width spec: '%s'" % (width_spec,))
                return 1

            if len(width_s) > 0:
                try:
                    width = int(width_s)
                except ValueError:
                    print("Invalid width value: '%s'" % (width_s,))
                    return 1
            
            if len(pixel_width_s) >= 2:
                try:
                    pixel_width = int(pixel_width_s)
                except ValueError:
                    print("Invalid pixel width value: '%s'" % (pixel_width_s,))
                    return 1
                if pixel_width < 1:
                    print("Pixel width can't be < 1.")
                    return 1
        if len(height_s) > 0:
            try:
                height = int(height_s)
            except ValueError:
                print("Invalid height value: '%s'" % (height_s,))
                return 1
    
    flags = argv[3:]
    no_audio = "-noaudio" in flags

    term.reset_background_color()
    term.clear_all()

    if no_audio:
        play_video(
            filepath,
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
        term.clear_all()
        term.set_cursor(1, 1)
    return 0


if __name__ == "__main__":
    if main(len(argv), argv) != 0:
        print_usage(argv[0])
