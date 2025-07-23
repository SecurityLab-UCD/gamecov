from typing import Generator

import imageio.v3 as iio
from returns.result import safe

from .frame import Frame
from .frame_cov import FrameCoverage


def load_mp4(url: str) -> list[Frame]:
    """Load an MP4 file as a list of Frames."""
    # bulk read all frames
    # Warning: large videos will consume a lot of memory (RAM)
    frames = iio.imread(url, plugin="pyav", extension=".mp4")
    return [Frame.fromarray(f) for f in frames]


def load_mp4_lazy(url: str) -> Generator[Frame, None, None]:
    """Load an MP4 file as a generator of Frames.
    for large videos, use this to avoid high memory usage.
    """
    # iterate over large videos
    for frame in iio.imiter(url, plugin="pyav", extension=".mp4"):
        yield Frame.fromarray(frame)


@safe
def get_frame_cov(url: str) -> FrameCoverage:
    """Get the frame coverage for a given MP4 file."""
    frames = load_mp4(url)
    return FrameCoverage(frames)
