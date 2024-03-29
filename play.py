import term

from args import Resolution
import array
from io import StringIO
from queue import Queue
from threading import Barrier, Event
from time import sleep, time
from typing import Optional, TextIO, Tuple, Union
from sys import argv, stdout

# Deps:
# - python (3.12.1)
# - av (11.0.0)
# - pillow (10.1.0)
# - pyaudio (0.2.14)
# $ pip install av pillow pyaudio
import av
from PIL.Image import Image
from pyaudio import PyAudio, paContinue, paAbort, paComplete, paFloat32

def clamp_float32_samples_and_set_volume(data: bytes, volume: float = 1.0) -> bytes:
    peaks = array.array("f", data)
    for i in range(len(peaks)):
        peaks[i] = max(min(peaks[i] * volume, 1.0), -1.0)
    return peaks.tobytes()

def play_audio(
    filepath: str, *,
    volume: float = 1.0,
    output_device: Optional[int] = None,
    pyaudio: Optional[PyAudio] = None,
    sync: Optional[Union[Event, Barrier]] = None,
    ready: Optional[Event] = None,
    abort: Event = Event(),
    ):
    with av.open(filepath, mode="r", timeout=5) as container:
        audio_fifo = av.AudioFifo()
        def audio_callback(in_data, frame_count, time_info, status):
            if abort.is_set() or status != 0:
                return (bytes(), paAbort)

            frame = audio_fifo.read(frame_count)
            if frame is None:
                return (bytes(), paComplete)

            data = bytes(frame.planes[0])
            return (clamp_float32_samples_and_set_volume(data, volume), paContinue)

        # Setup Audio Decoder and Resampler
        audio_generator = container.decode(audio=0)
        first_frame = next(audio_generator)

        audio_resampler = av.audio.resampler.AudioResampler(
            format="flt",
            layout=first_frame.layout,
            rate=first_frame.rate,
        )

        pya = pyaudio or PyAudio()
        try:
            # Sync with other threads
            if ready is not None:
                ready.set() # We're ready
            if sync is not None:
                sync.wait() # Wait for sync

            # Open Audio Stream
            pya_stream = pya.open(
                format=paFloat32,
                channels=len(audio_resampler.layout.channels),
                rate=audio_resampler.rate,
                #frames_per_buffer=first_frame.samples,
                stream_callback=audio_callback,
                output_device_index=output_device,
                output=True,
            )

            for frame in audio_generator:
                if abort.is_set():
                    break
                frame_flt = audio_resampler.resample(frame)[0]
                frame_flt.pts = None
                audio_fifo.write(frame_flt)

            while pya_stream.is_active():
                sleep(1)

            pya_stream.stop_stream()
            pya_stream.close()
        finally:
            if pyaudio is None:
                # Terminate pya only if we're the ones who created it
                pya.terminate()

def write_image(image: Image, origin_x: int, origin_y: int, pixel_ch: str, *, out: TextIO = stdout):
    last_bg = None
    screen = StringIO()

    for y in range(image.height):
        term.set_cursor(origin_x, origin_y+y, screen)
        for x in range(image.width):
            pixel = image.getpixel((x, y))
            # Don't change background if not necessary
            if last_bg != pixel:
                last_bg = pixel
                term.set_background_color(pixel[0], pixel[1], pixel[2], screen)
            screen.write(pixel_ch)
    term.reset_background_color(screen)

    # Render in a single write to out
    out.write(screen.getvalue())
    out.flush() # Flush otherwise out can ignore the frame
    # I think that stdout auto-flushes after a certain amount of characters are written to it,
    #  so we still need an internal buffer to send the whole thing in one call.
    # Maybe flushing out should be the job of `play_video`, since `write` on buffers should not flush.
    # However, I'll keep it like that for now. Maybe add a new kwarg to `write_image` like `flush=False`?

def play_video(
    filepath: str, *,
    origin_x: int = 1,
    origin_y: int = 1,
    width: Optional[int] = None, height: Optional[int] = None,
    pixel_width: int = 2,
    bounding_box: Resolution = Resolution(None, 2, None),
    align_center: bool = False,
    out: TextIO = stdout,
    sync: Optional[Union[Event, Barrier]] = None,
    ready: Optional[Event] = None,
    abort: Event = Event()
    ):
    pixel_ch = " " * pixel_width
    with av.open(filepath, mode="r", timeout=5) as container:
        video_generator = container.decode(video=0)
        first_frame = next(video_generator)
        
        frame_aspect_ratio = first_frame.width / first_frame.height
        if width is None and height is None:
            width = first_frame.width
            height = first_frame.height
        elif width is None:
            width = int(height * frame_aspect_ratio)
        elif height is None:
            height = int(width / frame_aspect_ratio)
        
        # Keep the frame within its bounding_box
        bb_pixel_width = bounding_box.pixel_width or pixel_width
        aspect_ratio = width / height
        if bounding_box.width is not None and (width*pixel_width) > (bounding_box.width*bb_pixel_width):
            width = bounding_box.width*bb_pixel_width//pixel_width
            height = int(width / aspect_ratio)
        if bounding_box.height is not None and height > bounding_box.height:
            height = bounding_box.height
            width = int(height * aspect_ratio)

        # Offset the frame if align_center
        off_x = 0
        off_y = 0
        if align_center:
            if bounding_box.width is not None:
                off_x = ((bounding_box.width*bb_pixel_width) - (width*pixel_width)) // 2
            if bounding_box.height is not None:
                off_y = (bounding_box.height - height) // 2

        # Print first frame (required to display images)
        write_image(
            first_frame.to_image(width=width, height=height), 
            origin_x+off_x, origin_y+off_y, pixel_ch, out=out
        )

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

            # Write the current frame
            image: Image = frame.to_image(width=width, height=height)
            write_image(image, origin_x+off_x, origin_y+off_y, pixel_ch, out=out)
