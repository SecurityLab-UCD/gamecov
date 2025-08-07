import os
import tempfile

from gamecov.dedup import hash_dedup
from gamecov.loader import load_mp4, load_mp4_lazy
from gamecov.writer import write_mp4, write_mp4_cv2
import imageio.v2 as iiov2
from PIL import Image


def v2_loader(mp4_path: str) -> list[Image.Image]:
    """Load a mp4 file and convert it to a list of PIL Image objects.

    Args:
        mp4_path (str): Path to the mp4 file.
    Returns:
        list[Image.Image]: List of PIL Image objects.
    """
    fps = 10  # Default frames per second used in game-fuzz
    with iiov2.get_reader(mp4_path, mode="I", fps=fps) as reader:
        imgs = [Image.fromarray(frame) for frame in reader]  # type: ignore
    return imgs


def diff_one(mp4_path: str) -> None:
    """Compare the output of load_mp4 and v2_loader for a single mp4 file."""
    frames = load_mp4(mp4_path)
    v2_frames = v2_loader(mp4_path)
    lazy_frames = list(load_mp4_lazy(mp4_path))

    assert len(frames) == len(v2_frames), "Frame counts do not match"
    assert len(frames) == len(lazy_frames), "Frame counts do not match"
    for i, (frame, v2_frame, lazy_frame) in enumerate(
        zip(frames, v2_frames, lazy_frames)
    ):
        assert frame.img.size == v2_frame.size, f"Frame {i} size mismatch"
        assert frame.img.size == lazy_frame.img.size, f"Frame {i} size mismatch"


def test_load_mp4_differential():
    """differential test load_mp4, load_mp4_lazy, and v2_loader functions return the same number of frames."""

    assets_dir = "assets/videos"
    if not os.path.exists(assets_dir):
        print(f"Assets directory '{assets_dir}' does not exist.")
        return

    for f in os.listdir(assets_dir):
        if not f.endswith(".mp4"):
            continue

        mp4_path = os.path.join(assets_dir, f)
        diff_one(mp4_path)


def one_round_trip(mp4_path: str):
    """Test that loading and writing MP4 files preserves the original frames."""
    frames = load_mp4(mp4_path)

    # Write the frames to a temporary MP4 file
    with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_file:
        output_path = temp_file.name
        # NOTE: using cv2 for write since ffmpeg does not support the resolution used in the tests
        # i.e. ffmpeg resizes the frames from (900, 660) to (912, 672) for macro_block_size=16,
        # which cannot pass the size check in the tests
        write_mp4_cv2(frames, output_path)

        # load the frames from the new MP4 file
        new_frames = load_mp4(output_path)

        # compare the original and new frames
        assert len(frames) == len(new_frames), "Frame counts do not match"
        assert len(hash_dedup(frames)) == len(
            hash_dedup(new_frames)
        ), "Unique frame counts do not match"
        for i, (orig_frame, new_frame) in enumerate(zip(frames, new_frames)):
            assert orig_frame.img.size == new_frame.img.size, f"Frame {i} size mismatch"


def test_load_write_round_trip():
    """Test that loading and writing MP4 files preserves the original frames."""

    assets_dir = "assets/videos"
    if not os.path.exists(assets_dir):
        print(f"Assets directory '{assets_dir}' does not exist.")
        return

    for f in os.listdir(assets_dir):
        if not f.endswith(".mp4"):
            continue

        mp4_path = os.path.join(assets_dir, f)
        one_round_trip(mp4_path)
