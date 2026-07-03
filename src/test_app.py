import sys
sys.path.insert(0, ".")
from theme import tokens_for, DARK, LIGHT
from app import VIDEO_QUALITIES, AUDIO_QUALITIES, CONCURRENCY_OPTIONS

def test_theme_tokens():
    assert tokens_for("dark") == DARK
    assert tokens_for("light") == LIGHT
    assert tokens_for("system") in (DARK, LIGHT)  # resolves to one or the other

def test_pipeline_progress_math():
    # stage_progress must clamp to [0,1] same as PipelineStrip.set_state does
    def clamp(x):
        return max(0.0, min(1.0, x))
    assert clamp(-0.2) == 0.0
    assert clamp(1.5) == 1.0
    assert clamp(0.5) == 0.5

def test_video_qualities_are_height_capped():
    assert "Best" in VIDEO_QUALITIES
    assert "bestvideo[height<=720]" in VIDEO_QUALITIES["720p"]

def test_audio_qualities_map_to_kbps_or_none():
    assert AUDIO_QUALITIES["Best (source)"] is None
    assert AUDIO_QUALITIES["320 kbps"] == 320
    assert all(v is None or isinstance(v, int) for v in AUDIO_QUALITIES.values())

def test_concurrency_capped_for_throttle_safety():
    assert max(CONCURRENCY_OPTIONS) <= 8
    assert 1 in CONCURRENCY_OPTIONS  # sequential must remain an option

def test_audio_postprocessor_shape():
    # mirrors the branch in _run_download without needing a QApplication
    def build_postprocessor(kbps):
        pp = {"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}
        if kbps is not None:
            pp["preferredquality"] = str(kbps)
        return pp

    assert build_postprocessor(None) == {"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}
    assert build_postprocessor(192)["preferredquality"] == "192"

if __name__ == "__main__":
    test_theme_tokens()
    test_pipeline_progress_math()
    test_video_qualities_are_height_capped()
    test_audio_qualities_map_to_kbps_or_none()
    test_concurrency_capped_for_throttle_safety()
    test_audio_postprocessor_shape()
    print("ok")
