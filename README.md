# Ogg File Batch Download and Convert

Python automation for batch download and conversion to .mp3 of .ogg files from a webpage

## Overview

This Python script is designed to parse a webpage containing a list of .ogg audio files, each behind its own subpage from the list. The .ogg files are subsequently converted to .mp3, with optional metadata supplied as inputs to the script.

## Requirements

The script is written for Python 3, and requires the following external libraries to be available in the Python environment (e.g. virtual or via `pip install`):

* Python 3.x
  - requests
  - beautifulsoup4
  - pydub
  - music_tag

It is also necessary that the programs 'ffmpeg' and 'ffprobe' be installed or accessible on the local path. On Linux systems, this requirement may be satisfied by installing the 'ffmpeg' package (e.g. `sudo apt install ffmpeg`).

## Usage

The target URL is the only required input argument. The remaining arguments are optional and will be used if supplied.

```bash
python ogg-batch-download-convert.py [target_url] <output_directory> <album_name> <artist_name> <thumbnail_file>
```

## License

MIT © 2024 John Greenwell