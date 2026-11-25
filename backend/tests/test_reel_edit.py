from app.application.videos.production import Cut, Timeline
from app.domain.motion import DEFAULT_STYLE, STYLES
from app.domain.video import editing_direction
from app.infrastructure.video.openmotion import composition


def test_reel_and_separate_inserts_share_one_timeline():
    style = STYLES[DEFAULT_STYLE]
    timeline = Timeline(cuts=[Cut(scene=1, start_ms=0, end_ms=20000)])
    args = (
        style,
        "Reel",
        "split",
        timeline,
        20,
        {"scene-1": "a.mp4"},
        {"width": 1000, "height": 600, "durationSeconds": 24},
    )
    plain = composition(*args, reel_format="reel-story", insert=False)
    assert 'id="guide"' not in plain and 'id="outro"' not in plain
    assert 'src="demos/common.js"' not in plain
    combined = composition(*args, reel_format="reel-steps", outro=style)
    assert 'data-composition-id="guide" data-start="8.0" data-duration="3"' in combined
    assert 'data-composition-id="outro" data-start="17" data-duration="3"' in combined
    assert "demos/cm-outro.js" in combined
    assert editing_direction({"reel_format": "reel-story"}) != editing_direction(
        {"reel_format": "reel-pulse"}
    )
