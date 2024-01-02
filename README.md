# TermVideoPlayer

![](preview.png)

## About

This Python script will let you play `ffmpeg`-readable videos on your terminal (with audio)!

**This project is experimental**: I haven't tested all possible formats so some may not work.

## Usage

`$ python main.py --help`

`$ python main.py play --help`

Usage is explained within the help prompts.

### Examples

Open `video.mp4`, set pixel width to 2 chars, and video height to 64 chars (keep aspect-ratio):
- `$ python main.py video.mp4 :2x64`

Open `video.mp4`, set video width to 10 chars (keep aspect-ratio):
- `$ python main.py video.mp4 10x`

Open `video.mp4`, set video height to 10 chars (keep aspect-ratio), set origin to (6,3) and disable audio:
- `$ python main.py video.mp4 x10 -o6p3 --no-audio`

## The audio stops playing

If it stops playing, it means that it couldn't be processed fast enough.

## Requirements

This project was developed for Python 3.12 (it **should** also work on 3.8)

You'll need an [ANSI](https://en.wikipedia.org/wiki/ANSI_escape_code)-compatible terminal, and the following Python packages:
- av (11.0.0)
- pillow (10.1.0)
- pyaudio (0.2.14)

`$ pip install av pillow pyaudio`

If you're on **Linux**, you must install `portaudio19-dev` before `pyaudio` through your distro's package manager:
- Ubuntu: `$ sudo apt install portaudio19-dev`
