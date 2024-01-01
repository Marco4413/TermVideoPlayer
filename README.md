# TermVideoPlayer

![](preview.png)

## About

This python script will let you play `ffmpeg`-readable videos on your terminal (with audio)!

**This project is experimental**: I haven't tested all possible formats so some may not work.

## Usage

`$ python main.py <path-to-video>`

## The audio stops playing

If it stops playing, it means that it couldn't be processed fast enough.

## Requirements

This project was developed for Python 3.12

You'll need an [ANSI](https://en.wikipedia.org/wiki/ANSI_escape_code)-compatible terminal, and the following Python packages:
- av (11.0.0)
- pillow (10.1.0)
- pyaudio (0.2.14)

`$ pip install av pillow pyaudio`
