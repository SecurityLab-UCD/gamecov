import imageio.v3 as iio
from PIL import Image
import numpy as np


def load_mp4(url: str) -> list[Image.Image]:
    """Load an MP4 file as a list of PIL Images."""
    assert url.endswith(".mp4"), "File must be an MP4 file"
    # bulk read all frames
    # Warning: large videos will consume a lot of memory (RAM)
    frames = iio.imread(url, plugin="pyav")
    return [Image.fromarray(f) for f in frames]


def load_mp4_lazy(url: str):
    """Load an MP4 file as a generator of PIL Images.
    for large videos, use this to avoid high memory usage.
    """
    assert url.endswith(".mp4"), "File must be an MP4 file"
    # iterate over large videos
    for frame in iio.imiter(url, plugin="pyav"):
        yield Image.fromarray(frame)
