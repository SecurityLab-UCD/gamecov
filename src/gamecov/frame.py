import base64
from dataclasses import dataclass
from io import BytesIO

import imagehash
from PIL import Image


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
    """wrapper for PIL Image with average hash."""

    img: Image.Image

    def __hash__(self):
        return hash(imagehash.average_hash(self.img))

    def __str__(self):
        return encode_image(self.img)

    @classmethod
    def fromarray(cls, array) -> "Frame":
        """Create a Frame from a numpy array."""
        return cls(img=Image.fromarray(array))
