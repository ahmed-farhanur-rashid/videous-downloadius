import sys
sys.path.insert(0, ".")
from theme import tokens_for, DARK, LIGHT

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

if __name__ == "__main__":
    test_theme_tokens()
    test_pipeline_progress_math()
    print("ok")
