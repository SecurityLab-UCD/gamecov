"""Tests for RustBKFrameMonitor: differential correctness and monotonicity."""
import os
import random
import tempfile

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck

pytest.importorskip("gamecov._gamecov_core")

from gamecov import FrameCoverage, BKFrameMonitor
from gamecov.frame_cov import RustBKFrameMonitor
import gamecov.generator as cg
from gamecov.writer import write_mp4

N_MAX = int(os.getenv("N_MAX", 100))


@settings(
    deadline=None,
    suppress_health_check=(HealthCheck.data_too_large, HealthCheck.too_slow),
)
@given(data=st.data(), n=st.integers(min_value=1, max_value=30))
def test_differential_python_vs_rust(data, n):
    """BKFrameMonitor and RustBKFrameMonitor must produce identical results."""
    created_files: list[str] = []
    covs: list[FrameCoverage] = []

    for _ in range(n):
        frames = data.draw(cg.frames_lists)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_f:
            output_path = tmp_f.name
            created_files.append(output_path)
            write_mp4(frames, output_path)
            covs.append(FrameCoverage(output_path))

    py_monitor = BKFrameMonitor()
    rust_monitor = RustBKFrameMonitor()

    for cov in covs:
        if not py_monitor.is_seen(cov):
            py_monitor.add_cov(cov)
        if not rust_monitor.is_seen(cov):
            rust_monitor.add_cov(cov)

    assert py_monitor.coverage_count == rust_monitor.coverage_count, (
        f"coverage_count mismatch: Python={py_monitor.coverage_count} "
        f"Rust={rust_monitor.coverage_count}"
    )
    assert len(py_monitor.item_seen) == len(rust_monitor.item_seen), (
        f"item_seen count mismatch: Python={len(py_monitor.item_seen)} "
        f"Rust={len(rust_monitor.item_seen)}"
    )

    for f in created_files:
        os.remove(f)


@settings(
    deadline=None,
    suppress_health_check=(HealthCheck.data_too_large, HealthCheck.too_slow),
)
@given(data=st.data(), n=st.integers(min_value=1, max_value=30))
def test_rust_order_independent_coverage(data, n):
    """RustBKFrameMonitor.coverage_count must be order-independent."""
    created_files: list[str] = []
    covs: list[FrameCoverage] = []

    for _ in range(n):
        frames = data.draw(cg.frames_lists)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_f:
            output_path = tmp_f.name
            created_files.append(output_path)
            write_mp4(frames, output_path)
            covs.append(FrameCoverage(output_path))

    # Original order
    monitor_a = RustBKFrameMonitor()
    for cov in covs:
        if not monitor_a.is_seen(cov):
            monitor_a.add_cov(cov)

    # Reversed order
    monitor_b = RustBKFrameMonitor()
    for cov in reversed(covs):
        if not monitor_b.is_seen(cov):
            monitor_b.add_cov(cov)

    # Shuffled order
    shuffled = list(covs)
    random.shuffle(shuffled)
    monitor_c = RustBKFrameMonitor()
    for cov in shuffled:
        if not monitor_c.is_seen(cov):
            monitor_c.add_cov(cov)

    assert monitor_a.coverage_count == monitor_b.coverage_count
    assert monitor_a.coverage_count == monitor_c.coverage_count
    assert len(monitor_a.item_seen) == len(monitor_b.item_seen)
    assert len(monitor_a.item_seen) == len(monitor_c.item_seen)

    for f in created_files:
        os.remove(f)


@settings(
    deadline=None,
    suppress_health_check=(HealthCheck.data_too_large, HealthCheck.too_slow),
)
@given(data=st.data(), n=st.integers(min_value=1, max_value=N_MAX))
def test_rust_monotone(data, n):
    """len(item_seen) must be monotonically non-decreasing for RustBKFrameMonitor."""
    monitor = RustBKFrameMonitor()
    prev_item_count = 0
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

            assert len(monitor.item_seen) >= prev_item_count, (
                "item_seen count should not decrease"
            )
            prev_item_count = len(monitor.item_seen)

    for f in created_files:
        os.remove(f)
