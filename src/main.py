import os
import argparse
import mapcov
from mapcov.loader import load_mp4, load_mp4_lazy


def main():

    # iterate all mp4 files in the assets directory
    assets_dir = "assets"
    if not os.path.exists(assets_dir):
        print(f"Assets directory '{assets_dir}' does not exist.")
        return
    mp4_files = [f for f in os.listdir(assets_dir) if f.endswith(".mp4")]
    if not mp4_files:
        print("No MP4 files found in the assets directory.")
        return
    for mp4_file in mp4_files:
        url = os.path.join(assets_dir, mp4_file)
        frames = load_mp4(url)
        print(f"intime: {len(frames)}")
        lazy_frames = list(load_mp4_lazy(url))
        print(f"lazy: {len(lazy_frames)}")
        assert len(frames) == len(lazy_frames), "Frame counts do not match"
        print("===========================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load an MP4 file and print the number of frames."
    )
    parser.add_argument(
        "-i",
        "--input_url",
        type=str,
        help="Path to the MP4 file",
        default="assets/38118.mp4",
    )
    args = parser.parse_args()
    main()
