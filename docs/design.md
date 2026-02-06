# Design

## Coverage Framework

`gamecov` is built on a generic `Protocol`-based framework (`cov_base.py`) that decouples coverage types from monitoring logic.

### Protocols

- **`CoverageItem`** — anything hashable and stringable. All coverage data points must satisfy this protocol.
- **`Coverage[T]`** — an execution trace exposing:
  - `.trace` — ordered list of all items encountered.
  - `.coverage` — deduplicated set of unique items.
  - `.path_id` — SHA1 fingerprint of the unique coverage set.
- **`CoverageMonitor[T]`** — accumulates coverage across sessions:
  - `.add_cov(cov)` — merge new coverage into the monitor.
  - `.is_seen(cov)` — check whether a path has already been recorded.
  - `.item_seen` / `.path_seen` — running totals.

Frame coverage (`FrameCoverage`, `FrameMonitor`, `BKFrameMonitor`) is the first concrete implementation. The framework is designed to support future metrics such as audio coverage or state-graph coverage with no changes to the monitoring interface.

### Key Invariants

- `len(item_seen)` is **monotonically non-decreasing** — `add_cov()` can only grow the set of distinct hashes, never shrink it. This property is verified by the `test_monotone*` test suite.
- `coverage_count` (connected-component count, `BKFrameMonitor` only) is **order-independent**: the same set of hashes always produces the same count regardless of insertion order. It may transiently decrease when a bridging hash merges two clusters.

## Frame Coverage

### Perceptual Hashing

Each video frame is hashed with pHash (`imagehash.phash`, 8x8 by default). Two frames are considered duplicates if the Hamming distance between their hashes is within `RADIUS` (default 5 bits). This tolerates minor visual differences (compression artifacts, slight camera movement) while distinguishing meaningfully different game states.

The `Frame` dataclass uses `imagehash.average_hash` for Python `__hash__`/set membership, while deduplication logic uses the more discriminating pHash.

### Pipeline

```
MP4 recording
  |
  v
loader.py -- load_mp4_lazy() / load_mp4() / load_mp4_last_n()
  |
  v
Iterable[Frame]           (PIL Image wrapped with average-hash)
  |
  v
dedup.py -- dedup_unique_hashes()    (pHash + Hamming distance)
  |
  v
FrameCoverage             (.coverage -> set[ImageHash], .path_id -> SHA1)
  |
  v
FrameMonitor / BKFrameMonitor       (.add_cov() accumulates unique items)
  |
  v
Coverage statistics       (.item_seen, .path_seen)
```

### Loading Strategies

| Function | Behavior | Use Case |
|----------|----------|----------|
| `load_mp4()` | Decode all frames into memory | Small videos, random access needed |
| `load_mp4_lazy()` | Generator, one frame at a time | Large videos, memory-constrained |
| `load_mp4_last_n()` | Seek + decode last *n* frames | Tail sampling |

All loaders use `imageio.v3` with the PyAV plugin.

## BK-Tree Optimization

The naive `FrameMonitor` checks each new hash against all previously seen hashes — O(N*M) per session. `BKFrameMonitor` uses a [Burkhard-Keller tree](https://en.wikipedia.org/wiki/BK-tree) that indexes hashes by Hamming distance in a metric space.

### How it works

1. Each image hash is packed into an integer via `numpy.packbits`.
2. The BK-tree stores these integers. Distances are computed with `(x ^ y).bit_count()` (popcount = Hamming distance).
3. On lookup, the triangle inequality prunes branches: for a query point *x* with radius *r* at a node with distance *d*, only children with keys in [d-r, d+r] need to be visited.

### Order-Independent Coverage via Union-Find

The greedy first-seen-wins dedup in `FrameMonitor` is **order-dependent**: processing the same recordings in different orders can yield different coverage counts (because the "is duplicate" relation is not transitive).

`BKFrameMonitor` solves this with a union-find (disjoint-set) structure:

1. **Every** distinct hash is inserted into the BK-tree (no greedy skip).
2. On insertion, `find_all_within(x, radius)` locates all existing neighbours.
3. The new hash is unioned with every neighbour in the union-find.
4. `coverage_count` = number of connected components = number of disjoint clusters.

Because the Hamming-distance graph depends only on which hashes exist (not insertion order), the connected-component count is fully order-independent.

**Trade-off**: `coverage_count` may transiently *decrease* when a new hash bridges two previously separate components. `len(item_seen)` (total distinct hashes) remains monotonically non-decreasing.

### Performance

Benchmarked on the SMB dataset with `N_MAX=500` recordings:

| Monitor | Time |
|---------|------|
| `FrameMonitor` | ~237s |
| `BKFrameMonitor` | ~187s |

~21% speedup, and the gap widens as the number of accumulated hashes grows.

## Stitching

`stitch_images()` combines unique frames into a panorama using `stitching.AffineStitcher`. Feature detection uses SIFT (default) or ORB. The confidence threshold controls how aggressively frames are matched (range 0.4-0.6). This is primarily a visualization tool — the coverage measurement itself does not depend on stitching.

## Configuration

| Environment Variable | Default | Description                                        |
| -------------------- | ------- | -------------------------------------------------- |
| `RADIUS`             | `5`     | Hamming distance threshold for frame deduplication |
| `N_MAX`              | `100`   | Max recordings to process in monotonicity tests    |


## Dependencies

| Library          | Purpose                                   |
| ---------------- | ----------------------------------------- |
| `imageio` + `av` | Video decoding/encoding via PyAV          |
| `pillow`         | Image representation                      |
| `imagehash`      | Perceptual hashing (pHash, average hash)  |
| `opencv-python`  | Color conversion, video writing           |
| `stitching`      | Panorama stitching                        |
| `numpy`          | Numerical operations                      |
| `returns`        | Functional error handling (`Result` type) |
| `typer`          | CLI framework                             |
| `hypothesis`     | Property-based testing                    |
