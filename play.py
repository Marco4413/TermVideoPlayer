import term

from io import StringIO
from os import path
from queue import Queue
from threading import Barrier, Event
from time import sleep, time
from sys import argv, stdout

# Deps:
# - python (3.12.1)
# - av (11.0.0)
# - pillow (10.1.0)
# - pyaudio (0.2.14)
# $ pip install av pillow pyaudio
import av
from PIL.Image import Image
from pyaudio import PyAudio, get_format_from_width, paContinue, paAbort, paComplete, paOutputOverflow, paOutputUnderflow, paFloat32

def play_audio(
    filepath: str,
    sync: Event|Barrier|None = None,
    ready: Event|None = None,
    abort: Event = Event(),
    ):
    with av.open(filepath, mode="r") as container:
        frame_queue = Queue()
        def audio_callback(in_data, frame_count, time_info, status):
            if abort.is_set():
                return (bytes(), paAbort)
            try:
                return (frame_queue.get(), paContinue if status == 0 else paAbort)
            except StopIteration:
                return (bytes(), paComplete)

        # Setup Audio Decoder and Resampler
        audio_generator = container.decode(audio=0)
        first_frame = next(audio_generator)

        audio_resampler = av.audio.resampler.AudioResampler(
            format="flt",
            layout=first_frame.layout,
            rate=first_frame.rate,
        )

        pya = PyAudio()

        # Sync with other threads
        if ready is not None:
            ready.set() # We're ready
        if sync is not None:
            sync.wait() # Wait for sync

        # Open Audio Stream
        pya_stream = pya.open(
            format=paFloat32,
            channels=len(first_frame.layout.channels),
            rate=first_frame.rate,
            frames_per_buffer=first_frame.samples,
            stream_callback=audio_callback,
            output=True,
        )

        for frame in audio_generator:
            if abort.is_set():
                break
            frame_flt = audio_resampler.resample(frame)[0]
            frame_data = bytes(frame_flt.planes[0])
            frame_queue.put(frame_data)

        while pya_stream.is_active():
            sleep(1)

        pya_stream.stop_stream()
        pya_stream.close()
        pya.terminate()
    abort.set()

def play_video(
    filepath: str,
    screen: term.ScreenBuffer = term.ScreenBuffer(0, 0),
    width: int|None = None, height: int|None = None,
    pixel_width: int = 2,
    sync: Event|Barrier|None = None,
    ready: Event|None = None,
    abort: Event = Event()
    ):
    pixel_ch = " " * pixel_width
    with av.open(filepath, mode="r") as container:
        video_generator = container.decode(video=0)
        first_frame = next(video_generator)
        
        aspect_ratio = first_frame.width / first_frame.height
        if width is None and height is None:
            width = first_frame.width
            height = first_frame.height
        elif width is None:
            width = int(height * aspect_ratio)
        elif height is None:
            height = int(width / aspect_ratio)

        screen.resize(width, height, init=term.Pixel(pixel_ch, None, None))

        if ready is not None:
            ready.set() # We're ready
        if sync is not None:
            sync.wait() # Wait for sync

        start_time = time()
        for frame in video_generator:
            if abort.is_set():
                break

            video_time = time()-start_time
            if frame.time <= video_time:
                # We're behind and we need to catch up
                continue
            else:
                # We're ahead so we wait to get to the current frame
                sleep(frame.time-video_time)

            # Write to term.ScreenBuffer the current frame
            image: Image = frame.to_image(width=width, height=height)
            for y in range(height):
                for x in range(width):
                    pixel = image.getpixel((x, y))
                    screen.put_pixel(x, y, term.Pixel(
                        pixel_ch,
                        fg=None,
                        bg=term.Color(pixel[0], pixel[1], pixel[2])
                    ))

            # Render in a single write to stdout
            buf = StringIO()
            screen.draw(buf)
            stdout.write(buf.getvalue())
