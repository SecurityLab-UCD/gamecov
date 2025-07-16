from typing import Generator

import imageio.v3 as iio
from PIL import Image

from .frame import Frame


def load_mp4(url: str) -> list[Frame]:
    """Load an MP4 file as a list of Frames."""
    assert url.endswith(".mp4"), "File must be an MP4 file"
    # bulk read all frames
    # Warning: large videos will consume a lot of memory (RAM)
    frames = iio.imread(url, plugin="pyav")
    return [Frame.fromarray(f) for f in frames]


def load_mp4_lazy(url: str) -> Generator[Frame, None, None]:
    """Load an MP4 file as a generator of Frames.
    for large videos, use this to avoid high memory usage.
    """
    assert url.endswith(".mp4"), "File must be an MP4 file"
    # iterate over large videos
    for frame in iio.imiter(url, plugin="pyav"):
        yield Frame.fromarray(frame)
