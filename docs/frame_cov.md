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

## Why Frame Coverage Is a Valid Fuzzing Metric

A useful fuzzing coverage metric must satisfy two properties:

1. **Monotonicity** — coverage never decreases as more inputs are observed. A fuzzer can safely interpret "coverage stopped growing" as saturation.
2. **Order-independence** — the final coverage value depends only on *which* inputs were observed, not *when*. This makes coverage comparable across runs with different scheduling strategies.

`gamecov` provides two monitors. We justify each property for both.

### Definitions

Let *H* = {h₁, h₂, …} be the universe of pHash values (64-bit vectors).
Define the **neighbourhood graph** G(S) for a set S ⊆ H as:

- Vertices: S
- Edges: {(a, b) | hamming(a, b) ≤ RADIUS}

Hamming distance is a **metric** (non-negative, symmetric, zero iff equal, and satisfies the triangle inequality). This makes G(S) a well-defined undirected graph for any S.

### Monotonicity

**`item_seen` (both monitors).** `add_cov` only ever *inserts* hashes into `item_seen`; it never removes them. Therefore `|item_seen|` is monotonically non-decreasing across successive `add_cov` calls.

*Proof.* Each call iterates over `cov.coverage`. A hash is added to `item_seen` if and only if it was not already present (the exact-duplicate check short-circuits). No code path removes elements from the set. ∎

This is the metric used by `FrameMonitor.coverage_count` (which returns `len(item_seen)`). It is also monotonic in `BKFrameMonitor`, but `BKFrameMonitor` uses a different primary metric (see below).

### Order-Independence (`BKFrameMonitor`)

**`coverage_count` = number of connected components of G(item_seen).**

*Claim.* For any fixed set S of hashes, the connected-component count cc(G(S)) is uniquely determined by S, regardless of the order in which the hashes were inserted.

*Proof.* The graph G(S) is defined purely by the set S and the distance predicate hamming(a, b) ≤ RADIUS. Neither depends on insertion order. The number of connected components is a property of the graph, not of how it was constructed.

The implementation maintains this invariant incrementally via union-find:

1. When a new hash x is inserted, `find_all_within(x, RADIUS)` returns **all** existing hashes within the radius (not just the first match).
2. x is unioned with every such neighbour. After the union step, any path of radius-edges connecting x to any existing component is faithfully captured.
3. Because union-find tracks *all* edges, not just first-seen ones, the resulting component structure is identical to computing cc(G(S)) from scratch.

This is verified empirically by `test_order_independent_coverage`, which asserts identical `coverage_count` across original, reversed, and randomly shuffled insertion orders. ∎

**Why `FrameMonitor` is order-dependent.** The greedy first-seen-wins dedup skips a hash if *any* existing hash is within RADIUS. Because the "within RADIUS" relation is **not transitive** (a is near b, b is near c, but a may not be near c), the set of retained hashes depends on which hash was encountered first. Different orderings can yield different retained sets and therefore different counts.

### Non-Monotonicity of `coverage_count` Is Expected

`BKFrameMonitor.coverage_count` may *decrease* when a new hash bridges two previously separate components. For example:

```
Before:  {A}  {B}       (2 components, hamming(A,B) > RADIUS)
Insert C where hamming(A,C) ≤ RADIUS and hamming(B,C) ≤ RADIUS
After:   {A, B, C}      (1 component)
```

This is correct: the new hash genuinely reduces the number of distinct visual clusters. In a fuzzing context, `coverage_count` decreasing means the fuzzer discovered that two previously-distinct regions are actually connected — this is valuable information, not a metric error. A fuzzer should track `coverage_count` (clusters explored) alongside `len(item_seen)` (total distinct observations) and use both signals.

### Cross-Run Comparability

Because `coverage_count` depends only on the set of observed hashes:

- Two fuzzing campaigns over the same game can be directly compared: the campaign with more connected components explored more visually distinct regions.
- Merging coverage from two campaigns is straightforward: take the union of their hash sets and recompute components. The result equals what a single campaign observing all those hashes would report.
- The metric is **idempotent**: adding a recording that contributes no new hashes changes nothing.

These properties make `BKFrameMonitor.coverage_count` suitable as a fuzzing progress metric analogous to edge coverage in traditional software fuzzing.

### Summary of Metric Properties

| Property | `FrameMonitor` (`len(item_seen)`) | `BKFrameMonitor` (`coverage_count`) |
|----------|-----------------------------------|-------------------------------------|
| Monotonic | Yes | No (may decrease on bridge) |
| Order-independent | No (greedy first-seen-wins) | Yes (graph-theoretic) |
| Cross-run comparable | No | Yes |
| Mergeable | No | Yes (set union) |
| Idempotent | Yes | Yes |

`BKFrameMonitor` is the recommended monitor for production fuzzing. `FrameMonitor` remains available for backward compatibility and as a simpler baseline.

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

| Function            | Behavior                       | Use Case                           |
| ------------------- | ------------------------------ | ---------------------------------- |
| `load_mp4()`        | Decode all frames into memory  | Small videos, random access needed |
| `load_mp4_lazy()`   | Generator, one frame at a time | Large videos, memory-constrained   |
| `load_mp4_last_n()` | Seek + decode last _n_ frames  | Tail sampling                      |

All loaders use `imageio.v3` with the PyAV plugin.

## BK-Tree Optimization

The naive `FrameMonitor` checks each new hash against all previously seen hashes — O(N\*M) per session. `BKFrameMonitor` uses a [Burkhard-Keller tree](https://en.wikipedia.org/wiki/BK-tree) that indexes hashes by Hamming distance in a metric space.

### How it works

1. Each image hash is packed into an integer via `numpy.packbits`.
2. The BK-tree stores these integers. Distances are computed with `(x ^ y).bit_count()` (popcount = Hamming distance).
3. On lookup, the triangle inequality prunes branches: for a query point _x_ with radius _r_ at a node with distance _d_, only children with keys in [d-r, d+r] need to be visited.

### Order-Independent Coverage via Union-Find

The greedy first-seen-wins dedup in `FrameMonitor` is **order-dependent**: processing the same recordings in different orders can yield different coverage counts (because the "is duplicate" relation is not transitive).

`BKFrameMonitor` solves this with a union-find (disjoint-set) structure:

1. **Every** distinct hash is inserted into the BK-tree (no greedy skip).
2. On insertion, `find_all_within(x, radius)` locates all existing neighbours.
3. The new hash is unioned with every neighbour in the union-find.
4. `coverage_count` = number of connected components = number of disjoint clusters.

Because the Hamming-distance graph depends only on which hashes exist (not insertion order), the connected-component count is fully order-independent.

**Trade-off**: `coverage_count` may transiently _decrease_ when a new hash bridges two previously separate components. `len(item_seen)` (total distinct hashes) remains monotonically non-decreasing.

### Performance

Benchmarked on the SMB dataset with `N_MAX=500` recordings:

| Monitor          | Time  |
| ---------------- | ----- |
| `FrameMonitor`   | ~237s |
| `BKFrameMonitor` | ~187s |

~21% speedup, and the gap widens as the number of accumulated hashes grows.

## Stitching

`stitch_images()` combines unique frames into a panorama using `stitching.AffineStitcher`. Feature detection uses SIFT (default) or ORB. The confidence threshold controls how aggressively frames are matched (range 0.4-0.6). This is primarily a visualization tool — the coverage measurement itself does not depend on stitching.

## Configuration

### Radius (Hamming Distance Threshold)

The radius parameter controls frame deduplication sensitivity. It can be configured:

1. **Constructor parameter (recommended):**
   ```python
   monitor = FrameMonitor(radius=10)
   monitor = BKFrameMonitor(radius=10)
   monitor = RustBKFrameMonitor(radius=10)
   cov = FrameCoverage("recording.mp4", threshold=10)
   ```

2. **Environment variable (sets default):**
   ```bash
   RADIUS=10 python my_script.py
   ```

See [docs/api.md](api.md) for full API documentation and [docs/tuning.md](tuning.md) for guidance on choosing radius values.

### Environment Variables

| Variable | Default | Description                                        |
| -------- | ------- | -------------------------------------------------- |
| `RADIUS` | `5`     | Default Hamming distance threshold                 |
| `N_MAX`  | `100`   | Max recordings to process in monotonicity tests    |

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
