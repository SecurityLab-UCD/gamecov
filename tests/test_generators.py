from gamecov import Frame
from gamecov.generator import frames, frames_lists


from hypothesis import given, strategies as st


@given(frame=frames(height=128, width=128, channels=3))
def test_size_is_right(frame: Frame):
    assert frame.img.size == (128, 128)
    assert frame.img.mode == "RGB"  # 3-channel check


@given(frames=frames_lists)
def test_frames_list(frames: list[Frame]):
    assert len(frames) >= 3
    assert len(frames) <= 100
    for frame in frames:
        assert frame.img.size == (128, 128)
        assert frame.img.mode == "RGB"
