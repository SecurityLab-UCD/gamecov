import typer

from gamecov import dedup_unique_frames, load_mp4
from gamecov.stitch import stitch_images


def main(
    input_mp4_path: str = "assets/videos/38118.mp4", confidence_threshold: float = 0.5
):
    """placeholder for main function to load video, deduplicate frames, and stitch images."""

    images = load_mp4(input_mp4_path)

    # Deduplicate using hash method
    unique_images = dedup_unique_frames(images)

    # # Stitch images together
    stitched_image = stitch_images(
        unique_images, confidence_threshold=confidence_threshold
    )
    stitched_image.save(f"output_{confidence_threshold}.jpg")


if __name__ == "__main__":
    typer.run(main)
