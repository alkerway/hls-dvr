# HLS DVR
DVR an HLS live manifest onto your computer. Polls and downloads the manifest and fragments with python then runs FFMpeg to create one single video.

# Usage

1. Have ffmpeg installed
1. Create a `manifest` and `log` folder in your directory.
1. Change the config variables at the top of main.py to your desired stream and length
1. `python3 main.py`

