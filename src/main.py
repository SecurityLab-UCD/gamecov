import fire

from mapcov import load_mp4, hash_dedup
from mapcov.stitch import stitch_images


def main(
    input_mp4_path: str = "assets/videos/38118.mp4", confidence_threshold: float = 0.5
):

    images = load_mp4(input_mp4_path)

    # Deduplicate using hash method
    unique_images = hash_dedup(images)

    # # Stitch images together
    stitched_image = stitch_images(
        unique_images, confidence_threshold=confidence_threshold
    )
    stitched_image.save(f"output_{confidence_threshold}.jpg")


if __name__ == "__main__":
    fire.Fire(main)
