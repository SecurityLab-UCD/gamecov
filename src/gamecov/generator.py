from hypothesis import given, strategies as st
from hypothesis.strategies import composite
import hypothesis.extra.numpy as hnp
import numpy as np

from .frame import Frame


@composite
def frames(draw, height: int, width: int, channels: int = 3) -> Frame:
    """
    Composite strategy that returns a PIL.Image with the requested dimensions.

    * height, width - fixed integers you supply
    * channels      - 3 → RGB, 1 → grayscale, etc.
    """
    array = draw(
        hnp.arrays(
            dtype=np.uint8,
            shape=(height, width, channels),
            elements=st.integers(min_value=0, max_value=255),
        )
    )
    return Frame.fromarray(array)


# `frames()` is the composite strategy from the previous example
frames_lists = st.lists(
    frames(height=128, width=128, channels=3),  # element strategy
    min_size=5,
    max_size=50,
)
