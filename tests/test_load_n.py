import os

from hypothesis import given, strategies as st, settings
from gamecov.loader import load_mp4_last_n, load_mp4

# all files in assets/videos
VIDEOS = [
    os.path.join("assets/videos", f)
    for f in os.listdir("assets/videos")
    if f.endswith(".mp4")
]


@settings(deadline=None)
@given(video_path=st.sampled_from(VIDEOS), n=st.integers(min_value=1, max_value=500))
def test_load_last_n(video_path: str, n: int):
    all_frames = load_mp4(video_path)
    last_n_frames = load_mp4_last_n(video_path, n)

    if n >= len(all_frames):
        assert len(last_n_frames) == len(all_frames)
        assert last_n_frames == all_frames
    else:
        assert len(last_n_frames) == n
        assert last_n_frames == all_frames[-n:]
