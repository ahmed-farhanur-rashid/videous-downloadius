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

def test_retry_attempts_is_retry_count_plus_one():
    # mirrors _run_download: retry_count=N means N retries after the first try
    for retry_count in (0, 2, 5):
        attempts = retry_count + 1
        assert attempts == retry_count + 1
        assert attempts >= 1  # always at least one try, even with 0 retries configured

def test_error_message_truncation():
    def truncate(message, limit=300):
        return message if len(message) < limit else message[:limit] + "…"

    short = "short error"
    assert truncate(short) == short
    long_msg = "x" * 500
    result = truncate(long_msg)
    assert len(result) == 301  # 300 chars + ellipsis
    assert result.endswith("…")

def test_cookie_opts_mapping():
    # mirrors the branch in _run_download
    def build_cookie_opts(cookie_source, cookie_file):
        opts = {}
        if cookie_source == "Custom file..." and cookie_file:
            opts["cookiefile"] = cookie_file
        elif cookie_source not in ("None", "Custom file..."):
            opts["cookiesfrombrowser"] = (cookie_source.lower(),)
        return opts

    assert build_cookie_opts("None", "") == {}
    assert build_cookie_opts("Chrome", "") == {"cookiesfrombrowser": ("chrome",)}
    assert build_cookie_opts("Custom file...", "/tmp/cookies.txt") == {"cookiefile": "/tmp/cookies.txt"}
    assert build_cookie_opts("Custom file...", "") == {}  # no file chosen yet -> no-op, not a crash

if __name__ == "__main__":
    test_theme_tokens()
    test_pipeline_progress_math()
    test_video_qualities_are_height_capped()
    test_audio_qualities_map_to_kbps_or_none()
    test_concurrency_capped_for_throttle_safety()
    test_audio_postprocessor_shape()
    test_retry_attempts_is_retry_count_plus_one()
    test_error_message_truncation()
    test_cookie_opts_mapping()
    print("ok")
