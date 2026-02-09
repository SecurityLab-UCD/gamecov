# API Reference

This document provides detailed API documentation for `gamecov`, a library for measuring visual coverage in video game play-testing.

## Table of Contents

- [Configuration](#configuration)
- [Coverage Classes](#coverage-classes)
  - [FrameCoverage](#framecoverage)
  - [FrameMonitor](#framemonitor)
  - [BKFrameMonitor](#bkframemonitor)
  - [RustBKFrameMonitor](#rustbkframemonitor)
- [Helper Functions](#helper-functions)
  - [get_frame_cov](#get_frame_cov)
- [Loaders](#loaders)
- [Protocols](#protocols)

---

## Configuration

### RADIUS (Hamming Distance Threshold)

The `radius` parameter controls how similar two frames must be to be considered duplicates. It represents the maximum Hamming distance between two perceptual hashes.

| Value | Effect |
|-------|--------|
| Lower (e.g., 3) | Stricter matching — more frames considered unique |
| Higher (e.g., 10) | Looser matching — more frames considered duplicates |
| Default: 5 | Balanced — tolerates compression artifacts while distinguishing meaningfully different states |

**Setting the radius:**

```python
# Option 1: Constructor parameter (recommended)
from gamecov import FrameMonitor, BKFrameMonitor, RustBKFrameMonitor

monitor = FrameMonitor(radius=10)
monitor = BKFrameMonitor(radius=10)
monitor = RustBKFrameMonitor(radius=10)

# Option 2: FrameCoverage threshold parameter
from gamecov import FrameCoverage

cov = FrameCoverage("recording.mp4", threshold=10)

# Option 3: Environment variable (affects default value)
# RADIUS=10 python my_script.py
```

**Choosing a radius value:**

- If frame coverage keeps growing linearly without saturation, increase the radius.
- If frame coverage saturates too quickly (missing visual distinctions), decrease the radius.
- Start with the default (5) and adjust based on your game's visual characteristics.

---

## Coverage Classes

### FrameCoverage

Computes frame coverage for a single video recording.

```python
from gamecov import FrameCoverage

cov = FrameCoverage(
    recording_path="gameplay.mp4",
    hash_method="phash",  # or "average"
    threshold=5,          # Hamming distance threshold
)
```

**Constructor Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `recording_path` | `str` | required | Path to the MP4 video file |
| `hash_method` | `HashMethod` | `"phash"` | Perceptual hash algorithm: `"phash"` or `"average"` |
| `threshold` | `int` | `5` (from `RADIUS` env var) | Hamming distance threshold for deduplication |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `trace` | `list[ImageHash]` | Ordered list of every frame's hash in the recording |
| `coverage` | `set[ImageHash]` | Deduplicated set of unique frame hashes |
| `path_id` | `str` | SHA1 fingerprint of the coverage set (for identifying duplicate paths) |

**Example:**

```python
from gamecov import FrameCoverage

# Analyze a recording with custom threshold
cov = FrameCoverage("session1.mp4", threshold=8)

print(f"Total frames: {len(cov.trace)}")
print(f"Unique frames: {len(cov.coverage)}")
print(f"Path ID: {cov.path_id}")
```

---

### FrameMonitor

Accumulates frame coverage across multiple recordings. Uses a greedy first-seen-wins deduplication strategy.

```python
from gamecov import FrameMonitor

monitor = FrameMonitor(radius=5)
```

**Constructor Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `radius` | `int` | `5` (from `RADIUS` env var) | Hamming distance threshold for duplicate detection |

**Methods:**

| Method | Description |
|--------|-------------|
| `add_cov(cov)` | Add a `Coverage` object to the monitor |
| `is_seen(cov)` | Check if a coverage path has already been recorded |
| `reset()` | Clear all monitor state |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `item_seen` | `set[ImageHash]` | All unique frame hashes seen so far |
| `path_seen` | `set[str]` | All unique path IDs seen so far |
| `coverage_count` | `int` | Number of unique frames (`len(item_seen)`) |
| `radius` | `int` | The configured Hamming distance threshold |

**Example:**

```python
from gamecov import FrameMonitor, FrameCoverage

# Create monitor with custom radius
monitor = FrameMonitor(radius=8)

# Process multiple recordings
for path in ["session1.mp4", "session2.mp4", "session3.mp4"]:
    cov = FrameCoverage(path, threshold=8)  # use same threshold

    if not monitor.is_seen(cov):
        monitor.add_cov(cov)
        print(f"Added {path}, coverage: {monitor.coverage_count}")
    else:
        print(f"Skipped {path} (duplicate path)")
```

**Note:** `FrameMonitor` is order-dependent — processing recordings in different orders may yield different coverage counts. Use `BKFrameMonitor` for order-independent coverage.

---

### BKFrameMonitor

Frame monitor backed by a BK-tree and union-find for order-independent coverage measurement.

```python
from gamecov import BKFrameMonitor

monitor = BKFrameMonitor(radius=5)
```

**Constructor Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `radius` | `int` | `5` (from `RADIUS` env var) | Hamming distance threshold for clustering |

**Methods:**

| Method | Description |
|--------|-------------|
| `add_cov(cov)` | Add a `Coverage` object to the monitor |
| `is_seen(cov)` | Check if a coverage path has already been recorded |
| `reset()` | Clear all monitor state including BK-tree and union-find |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `item_seen` | `set[ImageHash]` | All distinct frame hashes (monotonically non-decreasing) |
| `path_seen` | `set[str]` | All unique path IDs seen |
| `coverage_count` | `int` | Number of connected components (order-independent) |
| `radius` | `int` | The configured Hamming distance threshold |

**Example:**

```python
from gamecov import BKFrameMonitor, FrameCoverage

# Create monitor with higher radius for more aggressive deduplication
monitor = BKFrameMonitor(radius=10)

for path in recording_paths:
    cov = FrameCoverage(path, threshold=10)
    monitor.add_cov(cov)

    # coverage_count = connected components (order-independent)
    # len(item_seen) = total distinct hashes (monotonic)
    print(f"Components: {monitor.coverage_count}, "
          f"Distinct hashes: {len(monitor.item_seen)}")
```

**Key Differences from FrameMonitor:**

| Aspect | FrameMonitor | BKFrameMonitor |
|--------|--------------|----------------|
| Algorithm | Greedy first-seen-wins | BK-tree + union-find |
| Order-independent | No | Yes |
| `coverage_count` | `len(item_seen)` (monotonic) | Connected components (may decrease) |
| Performance | O(N*M) per session | O(log N) average lookup |
| Recommended for | Backward compatibility | Production fuzzing |

---

### RustBKFrameMonitor

Rust-accelerated version of `BKFrameMonitor` for maximum throughput.

```python
from gamecov import RustBKFrameMonitor

monitor = RustBKFrameMonitor(radius=5)
```

**Constructor Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `radius` | `int` | `5` (from `RADIUS` env var) | Hamming distance threshold for clustering |

**API:** Identical to `BKFrameMonitor`.

**Requirements:** Built automatically when installing `gamecov` from source with a Rust toolchain available.

**Performance:** ~2-5x faster than `BKFrameMonitor` for large datasets (10,000+ hashes).

**Example:**

```python
from gamecov import RustBKFrameMonitor, FrameCoverage

# Use Rust backend for better performance
try:
    monitor = RustBKFrameMonitor(radius=8)
except ImportError:
    # Fallback to Python implementation
    from gamecov import BKFrameMonitor
    monitor = BKFrameMonitor(radius=8)

for path in large_recording_set:
    cov = FrameCoverage(path, threshold=8)
    monitor.add_cov(cov)
```

---

## Helper Functions

### get_frame_cov

Safe wrapper around `FrameCoverage` that returns a `Result` type.

```python
from gamecov import get_frame_cov

result = get_frame_cov(
    url="gameplay.mp4",
    hash_method="phash",
    threshold=5,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | required | Path to the MP4 video file |
| `hash_method` | `HashMethod` | `"phash"` | Perceptual hash algorithm |
| `threshold` | `int` | `5` (from `RADIUS` env var) | Hamming distance threshold |

**Returns:** `Result[FrameCoverage, Exception]` — use `.unwrap()` or pattern match to extract the value.

**Example:**

```python
from gamecov import get_frame_cov

result = get_frame_cov("recording.mp4", threshold=10)

# Option 1: unwrap (raises on failure)
cov = result.unwrap()

# Option 2: pattern match
match result:
    case Success(cov):
        print(f"Coverage: {len(cov.coverage)}")
    case Failure(err):
        print(f"Error: {err}")
```

---

## Loaders

Video frame loaders for different use cases:

```python
from gamecov import load_mp4, load_mp4_lazy, load_mp4_last_n
```

| Function | Returns | Use Case |
|----------|---------|----------|
| `load_mp4(path)` | `list[Frame]` | Small videos, random access needed |
| `load_mp4_lazy(path)` | `Generator[Frame]` | Large videos, memory-constrained |
| `load_mp4_last_n(path, n)` | `list[Frame]` | Tail sampling (last N frames) |

---

## Protocols

### CoverageItem

Protocol for coverage data points:

```python
class CoverageItem(Protocol):
    def __hash__(self) -> int: ...
    def __str__(self) -> str: ...
```

### Coverage[T]

Protocol for coverage containers:

```python
class Coverage(Protocol[T]):
    @property
    def trace(self) -> list[T]: ...

    @property
    def coverage(self) -> set[T]: ...

    @property
    def path_id(self) -> str: ...
```

### CoverageMonitor[T]

Abstract base class for monitors:

```python
class CoverageMonitor(ABC, Generic[T]):
    def __init__(self): ...
    def is_seen(self, cov: Coverage[T]) -> bool: ...
    def add_cov(self, cov: Coverage[T]) -> None: ...
    def reset(self) -> None: ...

    @property
    def coverage_count(self) -> int: ...
```

---

## Quick Reference

### Which Monitor Should I Use?

| Scenario | Recommended Monitor |
|----------|---------------------|
| Production fuzzing | `RustBKFrameMonitor` |
| Python-only environment | `BKFrameMonitor` |
| Backward compatibility | `FrameMonitor` |
| Maximum performance | `RustBKFrameMonitor` |
| Order-independent metrics | `BKFrameMonitor` or `RustBKFrameMonitor` |

### Typical Workflow

```python
from gamecov import RustBKFrameMonitor, FrameCoverage

# 1. Create monitor with appropriate radius
monitor = RustBKFrameMonitor(radius=8)

# 2. Process recordings
for recording_path in get_recordings():
    cov = FrameCoverage(recording_path, threshold=8)
    monitor.add_cov(cov)

# 3. Check coverage
print(f"Visual clusters explored: {monitor.coverage_count}")
print(f"Total distinct frames: {len(monitor.item_seen)}")
print(f"Unique execution paths: {len(monitor.path_seen)}")
```
