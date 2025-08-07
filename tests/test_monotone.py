import tempfile

from gamecov import Frame, FrameCoverage, FrameMonitor
import gamecov.generator as cg
from gamecov.writer import write_mp4


from hypothesis import given, settings


monitor = FrameMonitor()
prev_cov = 0


@settings(deadline=None)
@given(frames=cg.frames_lists)
def test_monotone(frames: list[Frame]):
    global prev_cov
    global monitor
    with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp_f:
        output_path = tmp_f.name
        write_mp4(frames, output_path)
        cov = FrameCoverage(output_path)
        if not monitor.is_seen(cov):
            monitor.add_cov(cov)

        assert len(monitor.item_seen) >= prev_cov, "Coverage should not decrease"
        prev_cov = len(monitor.item_seen)
