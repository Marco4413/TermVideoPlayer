import args
import term
from play import play_audio, play_video

import argparse
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

def play_file(opt: argparse.Namespace):
    if opt.no_audio:
        play_video(
            opt.filepath,
            origin_x=opt.origin.x or 1,
            origin_y=opt.origin.y or 1,
            width=opt.res.width,
            height=opt.res.height,
            pixel_width=opt.res.pixel_width or 2
        )
        return

    audio_sync = Event()
    video_sync = Event()
    abort = Event()

    audio_thread = Thread(
        name="Thread-Audio",
        target=play_audio_thread,
        args=(opt.filepath,),
        kwargs={
            "sync": video_sync,
            "ready": audio_sync,
            "abort": abort
        }
    )

    try:
        audio_thread.start()
        play_video(
            opt.filepath,
            origin_x=opt.origin.x,
            origin_y=opt.origin.y,
            width=opt.res.width,
            height=opt.res.height,
            pixel_width=opt.res.pixel_width,
            sync=audio_sync,
            ready=video_sync,
            abort=abort
        )
    finally:
        abort.set()
        audio_thread.join()

def term_clear():
    term.reset_background_color()
    term.clear_all()
    term.set_cursor(1, 1)

def main(argc, argv) -> int:
    arg_parser = argparse.ArgumentParser(
        prog=argv[0],
        description="A Video Player for the Terminal.",
        allow_abbrev=False,
    )

    arg_parser.add_argument("filepath", help="the video file to open")
    arg_parser.add_argument("res", type=args.resolution, metavar=args.get_resolution_format(), help="the video resolution")
    arg_parser.add_argument("-o", "--origin", type=args.position, metavar=args.get_position_format(), default=argparse.Namespace(x=1,y=1), help=f"the video playback origin")
    arg_parser.add_argument("-na", "--no-audio", action="store_true", help="disable audio playback (default: False)")
    opt = arg_parser.parse_args(argv[1:], namespace=argparse.Namespace())

    if not path.exists(opt.filepath):
        arg_parser.print_help()
        print(f"No file '{opt.filepath}' found.")
        return 1

    term_clear()
    try:
        play_file(opt)
    except KeyboardInterrupt:
        term_clear()
    except:
        raise
    return 0

if __name__ == "__main__":
    main(len(argv), argv)
