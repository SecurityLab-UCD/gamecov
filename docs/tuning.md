# Tuning Frame Coverage: Radius and Threshold Parameters

This guide explains how to tune the `radius` (for monitors) and `threshold` (for `FrameCoverage`) parameters to achieve meaningful coverage metrics for your game.

## The Problem: Linear Growth Without Convergence

If you observe frame coverage growing linearly without saturation while branch coverage has already converged, your radius is likely too strict:

```
# Branch coverage: saturates quickly (~1000 branches in first 500s)
# Frame coverage: keeps growing linearly (0 → 4000+ over 18000s)
```

This happens because games produce many visually distinct frames from the same code paths:

- Character position changes
- Animation cycles
- Timer/counter updates
- Particle effects and lighting variations

## Understanding Radius

The `radius` parameter controls the Hamming distance threshold for considering two perceptual hashes as duplicates.

| Radius | Effect                                           | Use Case                                |
| ------ | ------------------------------------------------ | --------------------------------------- |
| 3-5    | Strict — only very similar frames are duplicates | High-fidelity visual distinction needed |
| 8-10   | Moderate — tolerates animation/position changes  | **Default (radius=10)**                 |
| 12-15  | Lenient — groups visually related frames         | Games with high visual entropy          |
| 20+    | Very lenient — only major scene changes count    | Coarse-grained coverage                 |

### How Radius Affects Convergence

Lower radius values detect more unique frames, leading to:

- Higher final coverage counts
- Slower or no convergence (linear growth)
- More sensitivity to visual noise

Higher radius values group more frames together, leading to:

- Lower final coverage counts (fewer clusters)
- Faster convergence (saturation)
- Focus on semantically distinct game states

## Empirical Results: Zelda Fuzzing Dataset

We analyzed 30 recordings from three independent fuzzing runs on a Zelda game with different radius values:

### Results by Run

| Run    | Radius | Final Coverage | Growth Rate | Status           |
| ------ | ------ | -------------- | ----------- | ---------------- |
| rand-0 | 5      | 195            | 0.96        | Linear growth    |
| rand-0 | 10     | 83             | 0.49        | Converging       |
| rand-0 | 15     | 46             | 0.12        | Saturated        |
| rand-0 | 20     | 9              | -0.31       | Over-grouped     |
| rand-1 | 5      | 133            | 0.56        | Linear growth    |
| rand-1 | 10     | 57             | 0.45        | Converging       |
| rand-1 | 15     | 39             | 0.25        | Converging       |
| rand-1 | 20     | 11             | -0.08       | Over-grouped     |
| rand-2 | 5      | 245            | 0.14        | Nearly saturated |
| rand-2 | 10     | 104            | 0.14        | Nearly saturated |
| rand-2 | 15     | 59             | 0.04        | Saturated        |
| rand-2 | 20     | 10             | -0.60       | Over-grouped     |

### Summary by Radius

| Radius | Avg Coverage | Avg Growth Rate | Status                        |
| ------ | ------------ | --------------- | ----------------------------- |
| 5      | 191          | 0.55            | Often linear growth           |
| 10     | 81           | 0.36            | Converging                    |
| 15     | 48           | 0.14            | **Saturated**                 |
| 20     | 10           | -0.33           | Over-grouped (clusters merge) |

**Growth Rate**: Ratio of coverage increase in last 10 recordings vs first 10.

- < 0.15 = effectively saturated
- 0.15-0.40 = converging
- \> 0.40 = linear growth
- Negative = coverage decreasing (clusters merging)

### Key Observations

1. **radius=5**: Coverage grows nearly linearly. Final counts vary widely (133-245) across runs. Not suitable for convergence-based stopping criteria.

2. **radius=10 (default)**: Moderate convergence. Coverage still growing but slowing down. Good balance between detail and convergence.

3. **radius=15**: Effectively saturated. Coverage plateaus quickly. Recommended for games with high visual entropy.

4. **radius=20**: Over-grouped. Coverage count can _decrease_ as new frames bridge previously separate clusters. Final counts very low (~10). Too aggressive for most use cases.

## Choosing the Right Radius

### Decision Framework

1. **Start with radius=10** as a baseline
2. Run a sample of recordings and observe:
    - Does coverage eventually plateau?
    - Is the final count meaningful (not too high or low)?

3. **Adjust based on behavior:**

    | Observation                     | Action                       |
    | ------------------------------- | ---------------------------- |
    | Coverage grows linearly forever | Increase radius (try 12, 15) |
    | Coverage saturates immediately  | Decrease radius (try 8, 5)   |
    | Final count too high (1000s)    | Increase radius              |
    | Final count too low (<20)       | Decrease radius              |
    | Coverage count decreases often  | Radius might be too high     |

### Game-Specific Considerations

| Game Type                 | Recommended Radius | Rationale                                  |
| ------------------------- | ------------------ | ------------------------------------------ |
| Platformer with scrolling | 10-12              | Distinct screens matter, positions less so |
| Fighting game             | 8-10               | Character states are meaningful            |
| Open world / 3D           | 12-15              | High visual variance from same locations   |
| Puzzle game               | 5-8                | Each board state is significant            |
| Menu-heavy UI             | 8-10               | Distinguish different menus                |

## API Usage

### Setting Radius on Monitors

```python
from gamecov import FrameMonitor, BKFrameMonitor, RustBKFrameMonitor

# All monitors accept radius parameter
monitor = FrameMonitor(radius=10)
monitor = BKFrameMonitor(radius=10)
monitor = RustBKFrameMonitor(radius=10)  # Recommended for performance
```

### Setting Threshold on FrameCoverage

The `threshold` parameter on `FrameCoverage` should match the monitor's radius for consistent behavior:

```python
from gamecov import FrameCoverage, RustBKFrameMonitor

RADIUS = 10  # Choose based on your game

monitor = RustBKFrameMonitor(radius=RADIUS)

for recording_path in recordings:
    # Use same threshold for coverage computation
    cov = FrameCoverage(recording_path, threshold=RADIUS)
    monitor.add_cov(cov)

print(f"Coverage clusters: {monitor.coverage_count}")
```

### Environment Variable (Default)

```bash
# Sets default for all monitors/coverage objects
RADIUS=10 python my_fuzzer.py
```

## Monitoring Convergence

Track both metrics over time to assess convergence:

```python
from gamecov import RustBKFrameMonitor, FrameCoverage

monitor = RustBKFrameMonitor(radius=10)
history = []

for i, recording in enumerate(recordings):
    cov = FrameCoverage(recording, threshold=10)
    monitor.add_cov(cov)

    history.append({
        "recording": i,
        "coverage_count": monitor.coverage_count,  # Clusters (order-independent)
        "item_seen": len(monitor.item_seen),       # Total distinct hashes (monotonic)
    })

# Check convergence: is growth rate decreasing?
recent_growth = history[-1]["coverage_count"] - history[-10]["coverage_count"]
early_growth = history[10]["coverage_count"] - history[0]["coverage_count"]
growth_ratio = recent_growth / early_growth if early_growth > 0 else 0

print(f"Growth ratio: {growth_ratio:.2f}")
if growth_ratio < 0.15:
    print("Coverage has effectively saturated")
elif growth_ratio < 0.4:
    print("Coverage is converging")
else:
    print("Coverage still growing linearly - consider increasing radius")
```

## Summary

| Parameter   | Class                                                  | Purpose                                                                               |
| ----------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| `radius`    | `FrameMonitor`, `BKFrameMonitor`, `RustBKFrameMonitor` | Hamming distance threshold for duplicate detection during monitoring                  |
| `threshold` | `FrameCoverage`, `get_frame_cov()`                     | Hamming distance threshold for deduplication when computing coverage from a recording |

**Key insight**: A useful coverage metric should eventually saturate. If frame coverage grows linearly while branch coverage has converged, increase your radius until frame coverage also shows saturation behavior.
