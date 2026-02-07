"""Benchmark: BKFrameMonitor (Python) vs RustBKFrameMonitor (Rust).

Measures add_cov throughput at the monitor level.

Run with:
    uv run pytest benchmarks/ --benchmark-enable
    uv run pytest benchmarks/ --benchmark-enable --benchmark-group-by=param:backend
"""

from __future__ import annotations

from typing import Callable, Union

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from gamecov import BKFrameMonitor, FrameCoverage
from gamecov.frame_cov import RustBKFrameMonitor

MonitorFactory = Callable[[], Union[BKFrameMonitor, RustBKFrameMonitor]]


def _run_monitor(
    factory: MonitorFactory,
    coverages: list[FrameCoverage],
) -> int:
    """Feed all coverages into a fresh monitor and return coverage_count."""
    monitor = factory()
    for cov in coverages:
        if not monitor.is_seen(cov):
            monitor.add_cov(cov)
    return monitor.coverage_count


@pytest.mark.parametrize(
    "backend",
    [
        pytest.param("python", id="python"),
        pytest.param("rust", id="rust"),
    ],
)
class TestMonitorBenchmark:
    """Parametrized benchmark comparing Python and Rust backends."""

    @staticmethod
    def _factory(backend: str) -> MonitorFactory:
        if backend == "python":
            return BKFrameMonitor
        return RustBKFrameMonitor

    def test_add_cov_10(
        self,
        benchmark: BenchmarkFixture,
        backend: str,
        coverages_10: list[FrameCoverage],
    ) -> None:
        """Benchmark add_cov with 10 recordings."""
        result = benchmark(_run_monitor, self._factory(backend), coverages_10)
        assert result > 0

    def test_add_cov_25(
        self,
        benchmark: BenchmarkFixture,
        backend: str,
        coverages_25: list[FrameCoverage],
    ) -> None:
        """Benchmark add_cov with 25 recordings."""
        result = benchmark(_run_monitor, self._factory(backend), coverages_25)
        assert result > 0

    def test_add_cov_50(
        self,
        benchmark: BenchmarkFixture,
        backend: str,
        coverages_50: list[FrameCoverage],
    ) -> None:
        """Benchmark add_cov with 50 recordings."""
        result = benchmark(_run_monitor, self._factory(backend), coverages_50)
        assert result > 0
