from PIL import Image
from stitching import AffineStitcher
import numpy as np
import numpy.typing as npt
import cv2

from .frame import Frame


def pil_to_cv2(image: Image.Image) -> np.ndarray:
    """Convert PIL Image to OpenCV format (BGR)."""
    # Convert PIL to numpy array
    numpy_image = np.array(image)

    # PIL uses RGB, OpenCV uses BGR
    if len(numpy_image.shape) == 3 and numpy_image.shape[2] == 3:
        return cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
    return numpy_image


def stitch_images(
    frames: list[Frame],
    detector: str = "sift",
    confidence_threshold: float = 0.5,
) -> Image.Image:
    """
    Stitch multiple images together using OpenStitching library.

    Args:
        frames: List of Frame objects to stitch
        detector: Feature detector to use (e.g., 'sift', 'orb')
        confidence_threshold: Confidence threshold for stitching (0.4-0.6)
    Returns:
        Stitched Frame
    """
    assert (
        0.4 <= confidence_threshold <= 0.6
    ), "Confidence threshold must be between 0.4 and 0.6"

    stitcher = AffineStitcher(
        detector=detector,
        confidence_threshold=confidence_threshold,
        crop=True,
    )

    # Perform stitching
    # note: the following line has type ignored because OpenStitching is untyped
    panorama: npt.NDArray = stitcher.stitch([pil_to_cv2(f.img) for f in frames])  # type: ignore

    return Image.fromarray(
        cv2.cvtColor(panorama, cv2.COLOR_RGB2BGR)  # convert color back to BGR
        if len(panorama.shape) == 3
        else panorama
    )
