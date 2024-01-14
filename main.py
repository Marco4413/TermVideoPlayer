#!/bin/python3

import args
import term
from play import play_audio, play_video

import argparse
from queue import Queue
from threading import Thread, Event
from time import sleep
from typing import Optional
from sys import argv, stdout

import av
from pyaudio import PyAudio

def play_audio_thread(*args, ready: Event, abort: Event, error_queue: Queue, **kwargs):
    try:
        play_audio(*args, ready=ready, abort=abort, **kwargs)
    except IndexError:
        # No Audio
        pass
    except Exception as error:
        abort.set()
        error_queue.put(error)
    except error: # Just to be sure that we catch everything
        abort.set()
    finally:
        ready.set()

def play_file(
    filepath: str, origin: args.Position, res: args.Resolution, *,
    volume: float = 1.0,
    audio_device: Optional[int] = None,
    pyaudio: Optional[PyAudio] = None,
    bounding_box: args.Resolution = args.Resolution(None, None, None),
    align_center: bool = False
    ):
    if pyaudio is None:
        play_video(
            filepath,
            origin_x=origin.x,
            origin_y=origin.y,
            width=res.width,
            height=res.height,
            pixel_width=res.pixel_width,
            bounding_box=bounding_box,
            align_center=align_center
        )
        return

    audio_sync = Event()
    video_sync = Event()
    abort = Event()

    audio_error_queue = Queue(1)
    audio_thread = Thread(
        name="Thread-Audio",
        target=play_audio_thread,
        args=(filepath,),
        kwargs={
            "volume": volume,
            "output_device": audio_device,
            "sync": video_sync,
            "ready": audio_sync,
            "abort": abort,
            "error_queue": audio_error_queue,
        }
    )

    try:
        audio_thread.start()
        play_video(
            filepath,
            origin_x=origin.x,
            origin_y=origin.y,
            width=res.width,
            height=res.height,
            pixel_width=res.pixel_width,
            bounding_box=bounding_box,
            align_center=align_center,
            sync=audio_sync,
            ready=video_sync,
            abort=abort
        )
    finally:
        abort.set()
        audio_thread.join()

    if not audio_error_queue.empty():
        raise audio_error_queue.get(block=False)

def term_clear():
    term.reset_background_color()
    term.clear_all()
    term.set_cursor(1, 1)

def print_audio_output_devices():
    pya = PyAudio()
    default_output_device = pya.get_default_output_device_info()
    for i in range(pya.get_device_count()):
        device = pya.get_device_info_by_index(i)
        if device["maxOutputChannels"] > 0:
            is_default = default_output_device["index"] == device["index"]
            print(f"{device['index']}{' (default) ' if is_default else ' '}- {device['name']}")
    pya.terminate()

def main(argc, argv):
    arg_parser = argparse.ArgumentParser(
        prog=argv.pop(0),
        description="A Video Player for the Terminal.",
        allow_abbrev=False,
    )

    arg_subparsers = arg_parser.add_subparsers(required=True)

    av_log_levels = [ "PANIC", "FATAL", "ERROR", "WARNING", "INFO", "VERBOSE", "DEBUG" ]
    play_parser = arg_subparsers.add_parser("play", help="plays the specified file", description="Plays the specified file.")
    play_parser.add_argument("filepath", help="the video file to play")
    play_parser.add_argument("res", type=args.resolution, metavar=args.get_resolution_format(), help="the video resolution")
    play_parser.add_argument("-o", "--origin", type=args.position, metavar=args.get_position_format(), default=args.Position(1,1), help="the video playback origin (default: %(default)s)")
    play_parser.add_argument("-C", "--align-center", action="store_true", help="center-aligns the video within its bounding-box. see the --bounding-box option (default: %(default)s)")
    play_parser.add_argument("-B", "--bounding-box", type=args.resolution, metavar=args.get_resolution_format(), default=args.Resolution(None, None, None), help="sets the max size in chars for each provided axis (default: %(default)s)")
    play_parser.add_argument("-na", "--no-audio", action="store_true", help="disable audio playback (default: %(default)s)")
    play_parser.add_argument("-nc", "--no-clear", action="store_true", help="disables term clearing (default: %(default)s)")
    play_parser.add_argument("-ad", "--audio-device", type=int, metavar="DEVICE_INDEX", help=f"selects the audio playback device (use `{arg_parser.prog} list-audio` to print output devices)")
    play_parser.add_argument("-v", "--volume", type=float, default=1.0, help="sets audio volume (default: %(default)s)")
    play_parser.add_argument("-b", "--block", action="store_true", help="waits for input at the end of playback (default: %(default)s)")
    play_parser.add_argument("-l", "--loop", type=int, metavar="N", default=1, help="plays the file N times. if N < 1 loops indefinitely (default: %(default)s)")
    play_parser.add_argument("-lw", "--loop-wait", type=float, metavar="secs", default=0, help="delay between loops (default: %(default)s)")
    play_parser.add_argument("--av-log-level", choices=av_log_levels, default="ERROR", help="sets av's log level (default: %(default)s)")
    play_parser.add_argument("--av-error-show-stacktrace", action="store_true", help="raises any av error again to show stacktrace (default: %(default)s)")
    play_parser.set_defaults(command="play")

    arg_subparsers.add_parser(
        "print-audio",
        help="prints all available output devices and PyAudio's log",
        description="Prints all available output devices and PyAudio's log."
    ).set_defaults(command="print-audio")

    if len(argv) == 0:
        arg_parser.print_help()
        return

    opt = arg_parser.parse_args(argv)
    if opt.command == "print-audio":
        print_audio_output_devices()
        return

    # Set pixel_width to 2 if not provided
    opt.res.pixel_width = opt.res.pixel_width or 2

    av.logging.set_level(getattr(av.logging, opt.av_log_level))

    pya: Optional[PyAudio] = None
    if not opt.no_audio:
        pya = PyAudio()

    please_clear_if_allowed = lambda: (term.next_line() if opt.no_clear else term_clear())
    please_clear_if_allowed()

    try:
        while True:
            play_file(
                opt.filepath, opt.origin, opt.res,
                volume=opt.volume, audio_device=opt.audio_device, pyaudio=pya,
                bounding_box=opt.bounding_box, align_center=opt.align_center
            )
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
        please_clear_if_allowed()
    except av.error.FFmpegError as av_error:
        please_clear_if_allowed()
        if opt.av_error_show_stacktrace:
            raise
        print(av_error)
    except KeyboardInterrupt:
        please_clear_if_allowed()
    except:
        please_clear_if_allowed()
        raise
    finally:
        if pya is not None:
            pya.terminate()

if __name__ == "__main__":
    main(len(argv), argv.copy())
