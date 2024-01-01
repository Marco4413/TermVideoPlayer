import term
from play import play_audio, play_video

from os import path
from threading import Thread, Event
from sys import argv, stdout

def main(argc, argv):
    if argc <= 1:
        print("No input file provided.")
        return 1
    
    filepath = argv[1]
    if not path.exists(filepath):
        print("No file '%s' found." % (filepath,))
        return 1

    term.reset_background_color()
    term.clear_all()

    audio_sync = Event()
    video_sync = Event()
    abort = Event()

    audio_thread = Thread(
        name="Thread-Audio",
        target=play_audio,
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
            height=64,
            pixel_width=2,
            sync=audio_sync,
            ready=video_sync,
            abort=abort
        )
    finally:
        abort.set()
        audio_thread.join()
        term.clear_all()
    return 0


if __name__ == "__main__":
    main(len(argv), argv)
