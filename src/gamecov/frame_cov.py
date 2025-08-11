import hashlib

from returns.result import safe
from imagehash import ImageHash
import imagehash
from .dedup import dedup_unique_hashes, is_dup
from .cov_base import Coverage, CoverageMonitor
from .loader import load_mp4, load_mp4_lazy


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
            if not any(is_dup(img_hash, h) for h in self.item_seen):
                self.item_seen.add(img_hash)


@safe
def get_frame_cov(url: str) -> FrameCoverage:
    """Get the frame coverage for a given MP4 file."""
    return FrameCoverage(url)
