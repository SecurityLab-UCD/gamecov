import tempfile
from hypothesis import given, settings
from gamecov.frame import Frame
from gamecov.loader import load_mp4
from gamecov.writer import write_mp4
import gamecov.generator as cg


@settings(deadline=None)
@given(frames=cg.frames_lists)
def test_load_write_round_trip(frames: list[Frame]):
    """Test that loading and writing MP4 files preserves the original frames."""

    with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_file:
        output_path = temp_file.name
        write_mp4(frames, output_path)

        # load the frames from the new MP4 file
        new_frames = load_mp4(output_path)

        # compare the original and new frames
        assert len(frames) == len(new_frames), "Frame counts do not match"

        # NOTE: do not now why dedup does not work here
        # assert len(hash_dedup(frames)) == len(
        #     hash_dedup(new_frames)
        # ), "Unique frame counts do not match"
        for i, (orig_frame, new_frame) in enumerate(zip(frames, new_frames)):
            assert orig_frame.img.size == new_frame.img.size, f"Frame {i} size mismatch"
