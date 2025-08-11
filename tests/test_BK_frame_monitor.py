import tempfile
import os

from hypothesis import given, settings, strategies as st

from gamecov.frame_cov import BK_FrameMonitor, FrameCoverage
from gamecov import Frame, FrameCoverage, FrameMonitor
from gamecov.frame_cov import BK_FrameMonitor
import gamecov.generator as cg
from gamecov.writer import write_mp4


@settings(deadline=None)
@given(data=st.data(), n=st.integers(min_value=1, max_value=100))
def test_monitor_diff(data, n):
    base_monitor = FrameMonitor()
    bk_monitor = BK_FrameMonitor()
    created_files = []
    for _ in range(n):
        frames = data.draw(cg.frames_lists)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_f:
            output_path = tmp_f.name
            created_files.append(output_path)
            write_mp4(frames, output_path)
            cov = FrameCoverage(output_path)
            if not base_monitor.is_seen(cov):
                base_monitor.add_cov(cov)
            if not bk_monitor.is_seen(cov):
                bk_monitor.add_cov(cov)

            assert len(base_monitor.item_seen) == len(
                bk_monitor.item_seen
            ), "Base and BK monitors should see the same number of items"

    # Clean up temporary files
    for f in created_files:
        os.remove(f)
