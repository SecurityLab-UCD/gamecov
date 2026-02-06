import os
import random
import tempfile

from hypothesis import given, settings, strategies as st

from gamecov import FrameCoverage, BKFrameMonitor
import gamecov.generator as cg
from gamecov.writer import write_mp4


@settings(deadline=None)
@given(data=st.data(), n=st.integers(min_value=1, max_value=30))
def test_order_independent_coverage(data, n):
    """BKFrameMonitor.coverage_count must be the same regardless of insertion order."""
    created_files: list[str] = []
    covs: list[FrameCoverage] = []

    for _ in range(n):
        frames = data.draw(cg.frames_lists)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_f:
            output_path = tmp_f.name
            created_files.append(output_path)
            write_mp4(frames, output_path)
            covs.append(FrameCoverage(output_path))

    # Process in original order
    monitor_a = BKFrameMonitor()
    for cov in covs:
        if not monitor_a.is_seen(cov):
            monitor_a.add_cov(cov)

    # Process in reversed order
    monitor_b = BKFrameMonitor()
    for cov in reversed(covs):
        if not monitor_b.is_seen(cov):
            monitor_b.add_cov(cov)

    # Process in a random shuffle
    shuffled = list(covs)
    random.shuffle(shuffled)
    monitor_c = BKFrameMonitor()
    for cov in shuffled:
        if not monitor_c.is_seen(cov):
            monitor_c.add_cov(cov)

    assert monitor_a.coverage_count == monitor_b.coverage_count, (
        "coverage_count should be order-independent (original vs reversed)"
    )
    assert monitor_a.coverage_count == monitor_c.coverage_count, (
        "coverage_count should be order-independent (original vs shuffled)"
    )
    # Total distinct hashes should also agree (set union is order-independent)
    assert len(monitor_a.item_seen) == len(monitor_b.item_seen)
    assert len(monitor_a.item_seen) == len(monitor_c.item_seen)

    for f in created_files:
        os.remove(f)
