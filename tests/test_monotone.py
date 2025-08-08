import tempfile
import os

from gamecov import Frame, FrameCoverage, FrameMonitor
import gamecov.generator as cg
from gamecov.writer import write_mp4


from hypothesis import given, settings, strategies as st


@settings(deadline=None)
@given(data=st.data(), n=st.integers(min_value=1, max_value=100))
def test_monotone(data, n):
    monitor = FrameMonitor()
    prev_cov = 0
    created_files = []
    for _ in range(n):
        frames = data.draw(cg.frames_lists)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_f:
            output_path = tmp_f.name
            created_files.append(output_path)
            write_mp4(frames, output_path)
            cov = FrameCoverage(output_path)
            if not monitor.is_seen(cov):
                monitor.add_cov(cov)

            assert len(monitor.item_seen) >= prev_cov, "Coverage should not decrease"
            prev_cov = len(monitor.item_seen)

    # Clean up temporary files
    for f in created_files:
        os.remove(f)
