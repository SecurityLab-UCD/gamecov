import os
import argparse
import mapcov
from mapcov import load_mp4, hash_dedup, ssim_dedup


def main():
    """placeholder main function to ensure the script can be run."""
    images = load_mp4("assets/videos/38118.mp4")

    print(len(images))
    
    # Deduplicate using hash method
    unique_images_hash = hash_dedup(images)
    print(f"Unique images using hash deduplication: {len(unique_images_hash)}")
    
    # Deduplicate using SSIM method
    unique_images_ssim = ssim_dedup(images)
    print(f"Unique images using SSIM deduplication: {len(unique_images_ssim)}")


if __name__ == "__main__":
    main()
