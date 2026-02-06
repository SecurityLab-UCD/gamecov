import os
from gamecov import FrameCoverage, FrameMonitor, BKFrameMonitor
import pytest


def test_smb_monotone_BK():
    """item_seen count is monotonic; coverage_count (components) may dip on bridges."""
    assets_dir = os.path.abspath("assets/smb")

    if not os.path.exists(assets_dir):
        pytest.skip("Assets path does not exist")

    # get all mp4 files
    mp4_files = [f for f in os.listdir(assets_dir) if f.endswith(".mp4")]
    # sort mp4 files of file name
    mp4_files.sort()

    monitor = BKFrameMonitor()
    prev_item_count = 0

    for f in mp4_files:
        f = os.path.join(assets_dir, f)
        cov = FrameCoverage(f)
        if not monitor.is_seen(cov):
            monitor.add_cov(cov)

        assert len(monitor.item_seen) >= prev_item_count, (
            "item_seen count should not decrease"
        )
        prev_item_count = len(monitor.item_seen)


def test_smb_monotone():
    assets_dir = os.path.abspath("assets/smb")

    if not os.path.exists(assets_dir):
        pytest.skip("Assets path does not exist")

    # get all mp4 files
    mp4_files = [f for f in os.listdir(assets_dir) if f.endswith(".mp4")]
    # sort mp4 files of file name
    mp4_files.sort()

    monitor = FrameMonitor()
    prev_cov = 0

    for f in mp4_files:
        f = os.path.join(assets_dir, f)
        cov = FrameCoverage(f)
        if not monitor.is_seen(cov):
            monitor.add_cov(cov)

        assert len(monitor.item_seen) >= prev_cov, "Coverage should not decrease"
        prev_cov = len(monitor.item_seen)


if __name__ == "__main__":
    test_smb_monotone()
