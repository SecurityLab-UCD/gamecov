from gamecov import Frame
from gamecov.dedup import hash_dedup
import gamecov.generator as cg
from hypothesis import given, settings
from hypothesis.stateful import RuleBasedStateMachine, rule
from hypothesis import strategies as st


@settings(deadline=None)
@given(data=st.data(), n=st.integers(min_value=1, max_value=100))
def test_dedup_update(data, n):
    all_frames: set[Frame] = set()
    for _ in range(n):
        frames = data.draw(cg.frames_lists)
        prev_len = len(all_frames)
        all_frames.update(hash_dedup(frames))
        assert len(all_frames) >= prev_len
