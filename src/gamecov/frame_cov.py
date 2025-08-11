import hashlib
from dataclasses import dataclass, field

from returns.result import safe
from imagehash import ImageHash
import imagehash
import numpy as np

from .dedup import dedup_unique_hashes, is_dup
from .cov_base import Coverage, CoverageMonitor
from .loader import load_mp4, load_mp4_lazy
from .env import RADIUS


class FrameCoverage:
    """track frame coverage in a game-play session"""

    def __init__(self, recording_path: str):
        self.recording_path = recording_path
        self.unique_frames = dedup_unique_hashes(load_mp4_lazy(recording_path))

    @property
    def trace(self) -> list[ImageHash]:
        """Note: this function is lazy, loading the frames AGAIN from the recording path.
        You should not call this function if you already have the frames loaded.
        """
        return [imagehash.phash(f.img) for f in load_mp4(self.recording_path)]

    @property
    def coverage(self) -> set[ImageHash]:
        """coverage set of unique frame hashes"""
        return set(self.unique_frames)

    @property
    def path_id(self) -> str:
        """generate a unique path ID based on the coverage"""
        path = tuple(sorted(hash(frame) for frame in self.coverage))
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
def get_frame_cov(url: str) -> FrameCoverage:
    """Get the frame coverage for a given MP4 file."""
    return FrameCoverage(url)


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


# > N_MAX=500 uv run pytest tests/test_monotone.py --durations=0
# 236.71s call     tests/test_monotone.py::test_monotone
# 186.90s call     tests/test_monotone.py::test_monotone_BK
class BKFrameMonitor(FrameMonitor):
    """FrameMonitor implemented using BK Tree
    For long videos with many frames,
    this implementation speed up the process of checking frame coverage significantly.
    """

    def __init__(self, radius: int = RADIUS):
        super().__init__()
        self._bktree = _BKTree()
        self._exact_bytes: set[bytes] = set()
        self.radius = radius

    def add_cov(self, cov: Coverage[ImageHash]) -> None:
        """add coverage to the current set.
        The deduplication by Hamming distance is managed by a BK-tree.
        """
        self.path_seen.add(cov.path_id)
        for img_hash in cov.coverage:
            hash_bytes = np.packbits(
                np.asarray(img_hash.hash, dtype=np.uint8),
                bitorder="big",
            ).tobytes()
            if hash_bytes in self._exact_bytes:  # exact dup
                continue

            x = int.from_bytes(hash_bytes, "big")
            if not self._bktree.any_within(x, self.radius):  # prune most candidates
                self._bktree.add(x)
                self._exact_bytes.add(hash_bytes)
                self.item_seen.add(img_hash)
