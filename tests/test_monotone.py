import tempfile
import os

from gamecov import FrameCoverage, FrameMonitor, BKFrameMonitor
import gamecov.generator as cg
from gamecov.writer import write_mp4


from hypothesis import given, settings, strategies as st, HealthCheck

N_MAX = int(os.getenv("N_MAX", 100))


@settings(
    deadline=None,
    suppress_health_check=(HealthCheck.data_too_large, HealthCheck.too_slow),
)
@given(data=st.data(), n=st.integers(min_value=1, max_value=N_MAX))
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


@settings(
    deadline=None,
    suppress_health_check=(HealthCheck.data_too_large, HealthCheck.too_slow),
)
@given(data=st.data(), n=st.integers(min_value=1, max_value=N_MAX))
def test_monotone_BK(data, n):
    monitor = BKFrameMonitor()
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
