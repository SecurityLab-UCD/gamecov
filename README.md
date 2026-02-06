# gamecov

Coverage monitoring for directed game play-testing (Game-Fuzz).

`gamecov` brings the idea of code coverage to video games.
Instead of measuring lines or branches executed,
it measures **unique visual states** observed during game-play.
A fuzzer drives the game, records sessions as MP4 videos,
and `gamecov` tells you how much of the game's visual space has been explored.

## Coverage Metrics

### Frame Coverage

Frame coverage counts the number of perceptually unique frames across gameplay recordings.
Two frames are considered duplicates if the Hamming distance between their perceptual hashes (pHash) falls within a configurable threshold.

**How it works:**

1. Load game-play recording (MP4).
2. Compute a perceptual hash (pHash) for each frame.
3. Deduplicate frames by Hamming distance — frames within `RADIUS` bits of an existing hash are discarded.
4. The remaining set of unique hashes is the **coverage** for that session.
5. A **monitor** accumulates coverage across multiple sessions, tracking total unique frames seen.

## Installation

Requires Python >= 3.11.

### As a package

Install directly from GitHub with [uv](https://docs.astral.sh/uv/):

```bash
uv add git+https://github.com/SecurityLab-UCD/gamecov.git
```

Or with pip:

```bash
pip install git+https://github.com/SecurityLab-UCD/gamecov.git
```

### For development

Clone the repo and sync dependencies:

```bash
git clone https://github.com/SecurityLab-UCD/gamecov.git
cd gamecov
uv sync
```

## Quick Start

### Compute frame coverage for a single recording

```python
from gamecov import FrameCoverage

cov = FrameCoverage("path/to/recording.mp4")
print(f"Unique frames: {len(cov.coverage)}")
print(f"Path ID: {cov.path_id}")
```

### Monitor coverage across multiple sessions

```python
from gamecov import FrameCoverage, BKFrameMonitor

monitor = BKFrameMonitor()

for recording in recordings:
    cov = FrameCoverage(recording)
    if not monitor.is_seen(cov):
        monitor.add_cov(cov)

print(f"Total unique frames: {len(monitor.item_seen)}")
print(f"Unique paths: {len(monitor.path_seen)}")
```

### CLI

```bash
# Deduplicate frames and stitch a panorama
uv run python src/main.py --input-mp4-path path/to/video.mp4 --confidence-threshold 0.5
```

## Development

### Prerequisites

```bash
# Install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

### Running Tests

```bash
# Run all tests in parallel
uv run pytest -n auto

# Run with coverage
uv run pytest -n auto --cov=gamecov
```

### Code Quality

```bash
# Type checking
uv run mypy src/ tests/

# Linting
uv run ruff check src/
```

### CI

GitHub Actions runs four checks on every PR: `pytest`, `mypy`, `ruff`, and `pylint`.
