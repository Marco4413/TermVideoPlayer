import args
import term
from play import play_audio, play_video

import argparse
from threading import Thread, Event
from time import sleep
from sys import argv, stdout

import av
import pyaudio

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
            "output_device": opt.audio_device,
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

def print_audio_output_devices():
    pya = pyaudio.PyAudio()
    default_output_device = pya.get_default_output_device_info()
    for i in range(pya.get_device_count()):
        device = pya.get_device_info_by_index(i)
        if device["maxOutputChannels"] > 0:
            is_default = default_output_device["index"] == device["index"]
            print(f"{device['index']}{' (default) ' if is_default else ' '}- {device['name']}")
    pya.terminate()

def main(argc, argv):
    arg_parser = argparse.ArgumentParser(
        prog=argv[0],
        description="A Video Player for the Terminal.",
        allow_abbrev=False,
    )

    arg_subparsers = arg_parser.add_subparsers(required=True)

    av_log_levels = [ "PANIC", "FATAL", "ERROR", "WARNING", "INFO", "VERBOSE", "DEBUG" ]
    play_parser = arg_subparsers.add_parser("play", help="plays the specified file", description="Plays the specified file.")
    play_parser.add_argument("filepath", help="the video file to play")
    play_parser.add_argument("res", type=args.resolution, metavar=args.get_resolution_format(), help="the video resolution")
    play_parser.add_argument("-o", "--origin", type=args.position, metavar=args.get_position_format(), default=args.Position(1,1), help=f"the video playback origin (default %(default)s)")
    play_parser.add_argument("-na", "--no-audio", action="store_true", help="disable audio playback (default: %(default)s)")
    play_parser.add_argument("-ad", "--audio-device", type=int, metavar="DEVICE_INDEX", help=f"selects the audio playback device (use `{arg_parser.prog} list-audio` to print output devices)")
    play_parser.add_argument("-v", "--volume", type=float, default=1.0, help="sets audio volume (default: %(default)s)")
    play_parser.add_argument("-b", "--block", action="store_true", help="waits for input at the end of playback (default: %(default)s)")
    play_parser.add_argument("-l", "--loop", type=int, metavar="N", default=1, help="plays the file N times. if N < 1 loops indefinitely (default: %(default)s)")
    play_parser.add_argument("-lw", "--loop-wait", type=float, metavar="secs", default=0, help="delay between loops (default: %(default)s)")
    play_parser.add_argument("--av-log-level", choices=av_log_levels, default="ERROR", help="sets av's log level (default: %(default)s)")
    play_parser.set_defaults(command="play")

    arg_subparsers.add_parser(
        "print-audio",
        help="prints all available output devices",
        description="Prints all available output devices."
    ).set_defaults(command="print-audio")

    opt = arg_parser.parse_args(argv[1:])
    if opt.command == "print-audio":
        print_audio_output_devices()
        return

    av.logging.set_level(getattr(av.logging, opt.av_log_level))

    term_clear()
    try:
        while True:
            play_file(opt)
            if opt.loop == 1:
                break
            opt.loop -= 1 # Can't wait for the number to underflow!
            # If int is a 64 bit number and loop=0, it would take 18446744073709551616 iterations to get back to 1 (which breaks the loop)
            # At 60 FPS it's roughly
            #   295147905179352825856 milliseconds
            # = 295147905179352826 seconds
            # = 81985529216487 hours
            # = 3416063717354 days
            # which is like 9359078678 years (twice the age of Earth as of 2024). We don't need to worry about this.
            # I have used https://www.wolframalpha.com as a calculator
            if opt.loop_wait > 0:
                sleep(opt.loop_wait)
        if opt.block: input()
    except KeyboardInterrupt:
        pass
    except:
        raise
    finally:
        term_clear()

if __name__ == "__main__":
    main(len(argv), argv)
