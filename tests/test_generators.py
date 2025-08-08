from gamecov import Frame
import gamecov.generator as cg
from gamecov.dedup import dedup_unique_frames


from hypothesis import given, strategies as st, settings


@given(frame=cg.frames(height=128, width=128, channels=3))
def test_size_is_right(frame: Frame):
    assert frame.img.size == (128, 128)
    assert frame.img.mode == "RGB"  # 3-channel check


@given(frames=cg.frames_lists)
def test_frames_list(frames: list[Frame]):
    assert len(frames) >= 5
    assert len(frames) <= 50
    for frame in frames:
        assert frame.img.size == (128, 128)
        assert frame.img.mode == "RGB"


@settings(max_examples=100, deadline=None)
@given(frames=cg.frames_lists)
def test_rand_dedup(frames: list[Frame]):
    assert len(dedup_unique_frames(frames)) <= len(frames), "Deduplication failed"
    assert len(dedup_unique_frames(frames)) == len(
        set(dedup_unique_frames(frames))
    ), "Hash deduplication failed uniqueness check"
