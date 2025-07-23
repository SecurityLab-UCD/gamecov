import hashlib

from .frame import Frame
from .dedup import hash_dedup
from .cov_base import Coverage, CoverageMonitor


class FrameCoverage(Coverage[Frame]):
    """track frame coverage in a game-play session"""

    def __init__(self, frames: list[Frame]):
        self.frames = frames

    @property
    def trace(self) -> list[Frame]:
        return self.frames

    @property
    def coverage(self) -> set[Frame]:
        return set(hash_dedup(self.trace))

    @property
    def path_id(self) -> str:
        """generate a unique path ID based on the coverage"""
        path = tuple(sorted(hash(frame) for frame in self.coverage))
        return hashlib.sha1(str(path).encode()).hexdigest()


class FrameMonitor(CoverageMonitor[Frame]):
    """monitor frame coverage in a game-play session"""

    def is_seen(self, cov: Coverage[Frame]) -> bool:
        """Check if the coverage has been seen."""
        return cov.path_id in self.path_seen

    def add_cov(self, cov: Coverage[Frame]) -> None:
        """Add a new execution coverage record to the monitor."""
        self.path_seen.add(cov.path_id)
        self.item_seen = hash_dedup(self.item_seen.union(cov.coverage))
