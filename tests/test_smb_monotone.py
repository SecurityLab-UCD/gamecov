import os
from gamecov import Frame, FrameCoverage, FrameMonitor
from gamecov.loader import load_mp4, load_mp4_lazy
import pytest


def test_smb_monotone():
    assets_path = "assets/smb"

    if not os.path.exists(assets_path):
        pytest.skip("Assets path does not exist")

    # get all mp4 files
    mp4_files = [f for f in os.listdir(assets_path) if f.endswith(".mp4")]
    # sort mp4 files of file name
    mp4_files.sort()

    monitor = FrameMonitor()
    prev_cov = 0

    for f in mp4_files:
        f = os.path.join(assets_path, f)
        cov = FrameCoverage(f)
        if not monitor.is_seen(cov):
            monitor.add_cov(cov)

        assert len(monitor.item_seen) >= prev_cov, "Coverage should not decrease"
        prev_cov = len(monitor.item_seen)


if __name__ == "__main__":
    test_smb_monotone()
