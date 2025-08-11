"""deduplication of frames."""

from typing import Iterable

import cv2
import numpy as np
import imagehash
from imagehash import ImageHash
from skimage import metrics as skm
from deprecated import deprecated

from .frame import Frame
from .env import RADIUS


def is_dup(
    img_hash_1: ImageHash, img_hash_2: ImageHash, threshold: int = RADIUS
) -> bool:
    """Hamming distance.
    Check if two image hashes are duplicates based on a threshold.
    """
    return abs(img_hash_1 - img_hash_2) <= threshold


def dedup_unique_frames(
    frames: Iterable[Frame], hash_size: int = 8, threshold: int = RADIUS
) -> set[Frame]:
    """
    Remove duplicate or very similar frames using perceptual hashing.

    Args:
        images: List of PIL Image objects
        hash_size: Size of the hash (larger = more precise)
        threshold: Maximum hamming distance to consider images as duplicates

    Returns:
        List of unique images
    """
    unique_images: dict[ImageHash, Frame] = {}

    for f in frames:
        # perceptual hash
        img_hash = imagehash.phash(f.img, hash_size=hash_size)

        # Check if similar image already exists
        is_duplicate = False
        for existing_hash in unique_images:
            if is_dup(img_hash, existing_hash, threshold):
                is_duplicate = True
                break
        if not is_duplicate:
            unique_images[img_hash] = f

    # Return frames in original order
    return set(unique_images.values())


def dedup_unique_hashes(
    frames: Iterable[Frame], hash_size: int = 8, threshold: int = RADIUS
) -> set[ImageHash]:
    """
    Remove duplicate or very similar frames using perceptual hashing.

    Args:
        images: List of PIL Image objects
        hash_size: Size of the hash (larger = more precise)
        threshold: Maximum hamming distance to consider images as duplicates

    Returns:
        List of unique images
    """
    unique_images: set[ImageHash] = set()

    for f in frames:
        # perceptual hash
        img_hash = imagehash.phash(f.img, hash_size=hash_size)

        # Check if similar image already exists
        is_duplicate = False
        for existing_hash in unique_images:
            if is_dup(img_hash, existing_hash, threshold):
                is_duplicate = True
                break
        if not is_duplicate:
            unique_images.add(img_hash)

    # Return frames in original order
    return unique_images


@deprecated("Too slow to use in fuzzing.")
def ssim_dedup(frames: Iterable[Frame], threshold: float = 0.95) -> set[Frame]:
    """
    SSIM (Structural Similarity Index) for duplicate detection.
    More accurate but much slower than hashing, not recommended for fuzzing.

    Args:
        images: List of PIL Image objects
        threshold: SSIM threshold (0-1, higher = more similar)

    Returns:
        List of unique images
    """

    assert 0 <= threshold <= 1, "Threshold must be between 0 and 1"

    if not frames:
        return set()

    frames = list(frames)

    unique_images = [frames[0]]

    for f in frames[1:]:
        # Convert to numpy array
        img_array = np.array(f.img.convert("L"))  # Convert to grayscale for SSIM

        # Check against all unique images
        is_duplicate = False
        for unique_f in unique_images:
            unique_array = np.array(unique_f.img.convert("L"))

            # Resize if needed (SSIM requires same dimensions)
            if img_array.shape != unique_array.shape:
                img_array = cv2.resize(
                    img_array, (unique_array.shape[1], unique_array.shape[0])
                )

            similarity: float = skm.structural_similarity(img_array, unique_array)  # type: ignore
            if similarity >= threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique_images.append(f)

    return set(unique_images)
