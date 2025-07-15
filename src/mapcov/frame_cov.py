from .frame import Frame
from .dedup import hash_dedup


class FrameCoverage:
    """track frame coverage in a game-play session"""

    def __init__(self, frames: list[Frame]):
        self.frames = frames

    @property
    def coverage(self) -> set[Frame]:
        return set(hash_dedup(self.frames))

    @property
    def path_id(self):
        """generate a unique path ID based on the coverage"""
        return hash(tuple(sorted(hash(frame) for frame in self.coverage)))
