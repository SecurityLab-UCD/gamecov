import base64
from dataclasses import dataclass
from io import BytesIO
from typing import Callable, Literal

import imagehash
from imagehash import ImageHash
from PIL import Image

HashMethod = Literal["ahash", "phash"]

_HASH_FUNCTIONS: dict[HashMethod, Callable[..., ImageHash]] = {
    "ahash": imagehash.average_hash,
    "phash": imagehash.phash,
}


def compute_hash(img: Image.Image, method: HashMethod = "phash") -> ImageHash:
    """Compute a perceptual hash of a PIL Image using the specified method."""
    return _HASH_FUNCTIONS[method](img)


def encode_image(img: Image.Image) -> str:
    """encode a PIL image object to base64 bytestring, and decode for requests
    https://stackoverflow.com/questions/31826335/how-to-convert-pil-image-image-object-to-base64-string
    https://platform.openai.com/docs/guides/vision/uploading-base64-encoded-images
    """
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_bytestring = base64.b64encode(buffered.getvalue())
    return img_bytestring.decode("utf-8")


@dataclass
class Frame:
    """wrapper for PIL Image with perceptual hash."""

    img: Image.Image
    hash_method: HashMethod = "phash"

    def __hash__(self) -> int:
        return hash(compute_hash(self.img, self.hash_method))

    def __str__(self) -> str:
        return encode_image(self.img)

    @classmethod
    def fromarray(cls, array, hash_method: HashMethod = "phash") -> "Frame":
        """Create a Frame from a numpy array."""
        return cls(img=Image.fromarray(array), hash_method=hash_method)
