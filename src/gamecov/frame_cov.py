import hashlib

from returns.result import safe

from .frame import Frame
from .dedup import hash_dedup
from .cov_base import Coverage, CoverageMonitor
from .loader import load_mp4


class FrameCoverage(Coverage[Frame]):
    """track frame coverage in a game-play session"""

    def __init__(self, recording_path: str):
        self.recording_path = recording_path
        frames = load_mp4(recording_path)
        self.unique_frames = hash_dedup(frames)

    @property
    def trace(self) -> list[Frame]:
        """Note: this function is lazy, loading the frames AGAIN from the recording path.
        You should not call this function if you already have the frames loaded.
        """
        return load_mp4(self.recording_path)

    @property
    def coverage(self) -> set[Frame]:
        return set(self.unique_frames)

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


@safe
def get_frame_cov(url: str) -> FrameCoverage:
    """Get the frame coverage for a given MP4 file."""
    frames = load_mp4(url)
    return FrameCoverage(frames)
