from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
from imagehash import ImageHash
from returns.result import safe

from .cov_base import Coverage, CoverageMonitor
from .dedup import is_dup
from .env import RADIUS
from .frame import Frame, HashMethod, compute_hash
from .loader import load_mp4_lazy


def _imagehash_to_u64(img_hash: ImageHash) -> int:
    """Convert an ImageHash to a u64 integer for the Rust backend."""
    hash_bytes = np.packbits(
        np.asarray(img_hash.hash, dtype=np.uint8),
        bitorder="big",
    ).tobytes()
    return int.from_bytes(hash_bytes, "big")


def _trace_and_unique(
    frames: Iterable[Frame],
    threshold: int = RADIUS,
    hash_method: HashMethod = "phash",
) -> tuple[list[ImageHash], set[ImageHash]]:
    """Single-pass computation of full trace and unique hash set.

    Returns:
        (trace, unique_hashes) — the ordered list of every frame hash,
        and the deduplicated set of unique hashes.
    """
    trace: list[ImageHash] = []
    unique: set[ImageHash] = set()

    for f in frames:
        img_hash = compute_hash(f.img, hash_method)
        trace.append(img_hash)

        is_duplicate = False
        for existing_hash in unique:
            if is_dup(img_hash, existing_hash, threshold):
                is_duplicate = True
                break
        if not is_duplicate:
            unique.add(img_hash)

    return trace, unique


class FrameCoverage:
    """track frame coverage in a game-play session"""

    def __init__(self, recording_path: str, hash_method: HashMethod = "phash"):
        self.recording_path = recording_path
        self.hash_method: HashMethod = hash_method
        self._trace, self.unique_frames = _trace_and_unique(
            load_mp4_lazy(recording_path), hash_method=hash_method
        )

    @property
    def trace(self) -> list[ImageHash]:
        """ordered list of every frame hash in the recording."""
        return self._trace

    @property
    def coverage(self) -> set[ImageHash]:
        """coverage set of unique frame hashes"""
        return set(self.unique_frames)

    @property
    def path_id(self) -> str:
        """generate a unique path ID based on the coverage"""
        path = tuple(
            sorted(
                np.packbits(
                    np.asarray(h.hash, dtype=np.uint8), bitorder="big"
                ).tobytes()
                for h in self.coverage
            )
        )
        return hashlib.sha1(str(path).encode()).hexdigest()


class FrameMonitor(CoverageMonitor[ImageHash]):
    """monitor frame coverage in a game-play session"""

    def is_seen(self, cov: Coverage[ImageHash]) -> bool:
        """Check if the coverage has been seen."""
        return cov.path_id in self.path_seen

    def add_cov(self, cov: Coverage[ImageHash]) -> None:
        """Add a new execution coverage record to the monitor."""
        self.path_seen.add(cov.path_id)

        # O(N*M) but correct and fast in pure Python
        for img_hash in cov.coverage:
            # skip exact-same frames
            # smb test: 144.24ms -> 141.32ms
            if img_hash in self.item_seen:
                continue
            # generator with `any` can short-circuit
            if not any(is_dup(img_hash, h, threshold=RADIUS) for h in self.item_seen):
                self.item_seen.add(img_hash)


@safe
def get_frame_cov(url: str, hash_method: HashMethod = "phash") -> FrameCoverage:
    """Get the frame coverage for a given MP4 file."""
    return FrameCoverage(url, hash_method=hash_method)


@dataclass
class _BKNode:
    val: int
    children: dict[int, "_BKNode"] = field(default_factory=dict)


class _BKTree:
    def __init__(self):
        self.root: _BKNode | None = None

    def add(self, x: int):
        """Add a new value `x` to the BK-tree."""
        if self.root is None:
            self.root = _BKNode(x)
            return

        node = self.root
        while True:
            d = (x ^ node.val).bit_count()
            if d == 0:
                return
            child = node.children.get(d)
            if child is None:
                node.children[d] = _BKNode(x)
                return
            node = child

    def any_within(self, x: int, r: int) -> bool:
        """check if there is any value within the range [x-r, x+r] in the BK-tree.

        Args:
            x (int): The value to check.
            r (int): The range.

        Returns:
            bool: whether any value within the range
        """
        if self.root is None:
            return False

        stack = [self.root]
        while stack:
            n = stack.pop()
            d = (x ^ n.val).bit_count()
            if d <= r:
                return True
            lo, hi = d - r, d + r
            for dd, child in n.children.items():
                if lo <= dd <= hi:
                    stack.append(child)
        return False

    def find_all_within(self, x: int, r: int) -> list[int]:
        """Return all values in the tree within Hamming distance r of x."""
        if self.root is None:
            return []
        results: list[int] = []
        stack = [self.root]
        while stack:
            n = stack.pop()
            d = (x ^ n.val).bit_count()
            if d <= r:
                results.append(n.val)
            lo, hi = d - r, d + r
            for dd, child in n.children.items():
                if lo <= dd <= hi:
                    stack.append(child)
        return results


class _UnionFind:
    """Disjoint-set (union-find) with path splitting and union by rank."""

    def __init__(self) -> None:
        self._parent: dict[int, int] = {}
        self._rank: dict[int, int] = {}
        self._count: int = 0

    def make_set(self, x: int) -> None:
        if x not in self._parent:
            self._parent[x] = x
            self._rank[x] = 0
            self._count += 1

    def find(self, x: int) -> int:
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]  # path splitting
            x = self._parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self._rank[ra] < self._rank[rb]:
            ra, rb = rb, ra
        self._parent[rb] = ra
        if self._rank[ra] == self._rank[rb]:
            self._rank[ra] += 1
        self._count -= 1

    @property
    def component_count(self) -> int:
        return self._count


# > N_MAX=500 uv run pytest tests/test_monotone.py --durations=0
# 236.71s call     tests/test_monotone.py::test_monotone
# 186.90s call     tests/test_monotone.py::test_monotone_BK
class BKFrameMonitor(FrameMonitor):
    """FrameMonitor backed by a BK-tree and union-find for order-independent coverage.

    Coverage is measured as the number of connected components in the
    Hamming-distance neighbourhood graph (distance <= radius).  Unlike the
    greedy first-seen-wins approach, this metric is **order-independent**:
    the same set of hashes always produces the same coverage count regardless
    of insertion order.

    Note: ``coverage_count`` may transiently *decrease* when a newly inserted
    hash bridges two previously separate components.  ``len(item_seen)``
    (total distinct hashes) remains monotonically non-decreasing.
    """

    def __init__(self, radius: int = RADIUS):
        super().__init__()
        self._bktree = _BKTree()
        self._exact_bytes: set[bytes] = set()
        self._uf = _UnionFind()
        self.radius = radius

    def add_cov(self, cov: Coverage[ImageHash]) -> None:
        """Add coverage to the current set.

        Every distinct hash is inserted into the BK-tree and unioned with all
        its neighbours within ``self.radius``.  Coverage is the number of
        connected components in the resulting union-find structure.
        """
        self.path_seen.add(cov.path_id)
        for img_hash in cov.coverage:
            x = _imagehash_to_u64(img_hash)
            x_bytes = x.to_bytes(8, "big")
            if x_bytes in self._exact_bytes:
                continue

            neighbors = self._bktree.find_all_within(x, self.radius)

            self._uf.make_set(x)
            for nb in neighbors:
                self._uf.union(x, nb)

            self._bktree.add(x)
            self._exact_bytes.add(x_bytes)
            self.item_seen.add(img_hash)

    @property
    def coverage_count(self) -> int:
        """Order-independent coverage: number of connected components."""
        return self._uf.component_count

    def reset(self) -> None:
        """Reset all monitor state including BK-tree and union-find."""
        super().reset()
        self._bktree = _BKTree()
        self._exact_bytes.clear()
        self._uf = _UnionFind()


class RustBKFrameMonitor(FrameMonitor):
    """Rust-accelerated BKFrameMonitor using gamecov-core.

    Behaviorally identical to :class:`BKFrameMonitor` but delegates the
    BK-tree, union-find, and coverage tracking to a compiled Rust extension
    for significantly higher throughput.

    Requires the ``gamecov-core`` package to be installed.
    """

    def __init__(self, radius: int = RADIUS):
        try:
            from gamecov import _gamecov_core
        except ImportError as exc:
            raise ImportError(
                "gamecov Rust extension not available. "
                "Reinstall gamecov from source with a Rust toolchain."
            ) from exc
        super().__init__()
        self._tracker: _gamecov_core.CoverageTracker = _gamecov_core.CoverageTracker(
            radius
        )
        self._exact: set[int] = set()
        self.radius = radius

    def add_cov(self, cov: Coverage[ImageHash]) -> None:
        """Add coverage using Rust-accelerated data structures."""
        self.path_seen.add(cov.path_id)
        for img_hash in cov.coverage:
            x = _imagehash_to_u64(img_hash)
            if x in self._exact:
                continue

            self._tracker.add_hash(x)
            self._exact.add(x)
            self.item_seen.add(img_hash)

    @property
    def coverage_count(self) -> int:
        """Order-independent coverage from Rust implementation."""
        count: int = self._tracker.coverage_count
        return count

    def reset(self) -> None:
        """Reset all monitor state."""
        super().reset()
        from gamecov import _gamecov_core

        self._tracker = _gamecov_core.CoverageTracker(self.radius)
        self._exact.clear()
