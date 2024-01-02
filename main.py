import args
import term
from play import play_audio, play_video

import argparse
from os import path
from threading import Thread, Event
from time import sleep
from sys import argv, stdout

import av

def play_audio_thread(*args, ready: Event, abort: Event, **kwargs):
    try:
        play_audio(*args, ready=ready, abort=abort, **kwargs)
    except IndexError:
        # No Audio
        pass
    except:
        abort.set()
    finally:
        ready.set()

def play_file(opt: argparse.Namespace):
    if opt.no_audio:
        play_video(
            opt.filepath,
            origin_x=opt.origin.x,
            origin_y=opt.origin.y,
            width=opt.res.width,
            height=opt.res.height,
            pixel_width=opt.res.pixel_width
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
            "volume": opt.volume,
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

    av_log_levels = [ "PANIC", "FATAL", "ERROR", "WARNING", "INFO", "VERBOSE", "DEBUG" ]
    arg_parser.add_argument("filepath", help="the video file to open")
    arg_parser.add_argument("res", type=args.resolution, metavar=args.get_resolution_format(), help="the video resolution")
    arg_parser.add_argument("-o", "--origin", type=args.position, metavar=args.get_position_format(), default=argparse.Namespace(x=1,y=1), help=f"the video playback origin (default '1p1')")
    arg_parser.add_argument("-na", "--no-audio", action="store_true", help="disable audio playback (default: False)")
    arg_parser.add_argument("-v", "--volume", type=float, default=1.0, help="sets audio volume (default: 1.0)")
    arg_parser.add_argument("-b", "--block", action="store_true", help="waits for input at the end of playback (default: False)")
    arg_parser.add_argument("-l", "--loop", type=int, metavar="N", default=0, help="loops N times. if N < 0 loops indefinitely (default: 0)")
    arg_parser.add_argument("-lw", "--loop-wait", type=float, metavar="secs", default=0, help="delay between loops (default: 0.0)")
    arg_parser.add_argument("--log-level", choices=av_log_levels, default="ERROR", help="av log level (default: 'ERROR')")
    opt = arg_parser.parse_args(argv[1:], namespace=argparse.Namespace())

    av.logging.set_level(getattr(av.logging, opt.log_level))

    if not path.exists(opt.filepath):
        arg_parser.print_help()
        print(f"No file '{opt.filepath}' found.")
        return 1

    term_clear()
    try:
        play_file(opt) # Play once at start
        while opt.loop != 0:
            # If any loop is needed, loop
            opt.loop -= 1
            if opt.loop_wait > 0:
                sleep(opt.loop_wait)
            play_file(opt)
        if opt.block: input()
    except KeyboardInterrupt:
        pass
    except:
        raise
    finally:
        term_clear()
    return 0

if __name__ == "__main__":
    main(len(argv), argv)
