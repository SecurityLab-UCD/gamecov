"""Shared fixtures for benchmark suite.

Pre-generates FrameCoverage objects so the benchmark loop only measures
monitor operations (add_cov / is_seen), not video I/O or hashing.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Generator

import numpy as np
import pytest

from gamecov import FrameCoverage
from gamecov.frame import Frame
from gamecov.writer import write_mp4

SEED: int = 42
FRAME_HEIGHT: int = 128
FRAME_WIDTH: int = 128
FRAMES_PER_RECORDING: int = 20


def _generate_coverages(
    n_recordings: int,
    seed: int = SEED,
) -> Generator[list[FrameCoverage], None, None]:
    """Generate n_recordings FrameCoverage objects from deterministic random frames."""
    rng = np.random.default_rng(seed)
    coverages: list[FrameCoverage] = []
    temp_files: list[str] = []

    for _ in range(n_recordings):
        frames = [
            Frame.fromarray(
                rng.integers(
                    0, 256, size=(FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8
                )
            )
            for _ in range(FRAMES_PER_RECORDING)
        ]
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            write_mp4(frames, tmp.name)
            temp_files.append(tmp.name)
            coverages.append(FrameCoverage(tmp.name))

    yield coverages

    for f in temp_files:
        os.remove(f)


@pytest.fixture(scope="session")
def coverages_10() -> Generator[list[FrameCoverage], None, None]:
    yield from _generate_coverages(10)


@pytest.fixture(scope="session")
def coverages_25() -> Generator[list[FrameCoverage], None, None]:
    yield from _generate_coverages(25)


@pytest.fixture(scope="session")
def coverages_50() -> Generator[list[FrameCoverage], None, None]:
    yield from _generate_coverages(50)
