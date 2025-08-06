import numpy as np
import imageio.v3 as iio
import cv2

from .frame import Frame


def write_mp4(frames: list[Frame], output_path: str) -> None:
    """Write a list of Frames to an MP4 file."""
    # convert Frames to numpy arrays
    arrays = [np.array(frame.img) for frame in frames]
    print(arrays)
    print(output_path)
    iio.imwrite(output_path, arrays, extension=".mp4")


def write_mp4_cv2(frames: list[Frame], output_path: str, fps: float = 24.0) -> None:

    # Get the dimensions from the first frame
    height, width, _ = np.array(frames[0].img).shape

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for frame in frames:
        img = cv2.cvtColor(np.array(frame.img), cv2.COLOR_RGB2BGR)
        out.write(img)

    out.release()
