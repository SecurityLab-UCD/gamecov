"""deduplication of frames."""

import cv2
import numpy as np
import imagehash
from PIL import Image
from skimage.metrics import structural_similarity as ssim


def hash_dedup(
    images: list[Image.Image], hash_size: int = 8, threshold: int = 5
) -> list[Image.Image]:
    """
    Remove duplicate or very similar frames using perceptual hashing.

    Args:
        images: List of PIL Image objects
        hash_size: Size of the hash (larger = more precise)
        threshold: Maximum hamming distance to consider images as duplicates

    Returns:
        List of unique images
    """
    unique_images: dict[imagehash.ImageHash, Image.Image] = {}

    for img in images:
        # perceptual hash
        img_hash = imagehash.average_hash(img, hash_size=hash_size)

        # Check if similar image already exists
        is_duplicate = False
        for existing_hash in unique_images.keys():
            if abs(img_hash - existing_hash) <= threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique_images[img_hash] = img

    # Return images in original order
    return list(unique_images.values())


def ssim_dedup(images: list[Image.Image], threshold: float = 0.95) -> list[Image.Image]:
    """
    SSIM (Structural Similarity Index) for duplicate detection.
    More accurate but much slower than hashing, not recommended for fuzzing.

    Args:
        images: List of PIL Image objects
        threshold: SSIM threshold (0-1, higher = more similar)

    Returns:
        List of unique images
    """

    if not images:
        return []

    unique_images = [images[0]]

    for img in images[1:]:
        # Convert to numpy array
        img_array = np.array(img.convert("L"))  # Convert to grayscale for SSIM

        # Check against all unique images
        is_duplicate = False
        for unique_img in unique_images:
            unique_array = np.array(unique_img.convert("L"))

            # Resize if needed (SSIM requires same dimensions)
            if img_array.shape != unique_array.shape:
                img_array = cv2.resize(
                    img_array, (unique_array.shape[1], unique_array.shape[0])
                )

            similarity: float = ssim(img_array, unique_array)  # type: ignore
            if similarity >= threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique_images.append(img)

    return unique_images
