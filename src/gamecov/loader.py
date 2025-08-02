from typing import Generator

import imageio.v3 as iio

from .frame import Frame


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


def load_mp4_last_n(url: str, n: int) -> list[Frame]:
    """Load the last n frames of an MP4 file as a list of Frames.
    The implementation of this function is based on
    https://stackoverflow.com/questions/73079005/how-to-get-the-last-frame-of-a-video-with-imageio-in-python
    """

    # seeking dimensions first
    # improps is fast since it doesn't decode frames
    props = iio.improps(url, plugin="pyav", extension=".mp4")

    # Make sure the codec knows the number of frames
    assert props.shape[0] != -1

    # seek to the last n frames
    start = max(0, props.shape[0] - n)
    frames = [
        Frame.fromarray(iio.imread(url, plugin="pyav", extension=".mp4", index=i))
        for i in range(start, props.shape[0])
    ]
    return frames
