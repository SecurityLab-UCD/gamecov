from dataclasses import dataclass
from PIL import Image
import imagehash


@dataclass
class Frame:
    """wrapper for PIL Image with average hash."""

    img: Image.Image

    def __hash__(self):
        return hash(imagehash.average_hash(self.img))

    @classmethod
    def fromarray(cls, array):
        """Create a Frame from a numpy array."""
        return cls(img=Image.fromarray(array))
