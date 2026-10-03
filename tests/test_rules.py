"""Bölüm 2 kurallarının kod denetimleri."""
import subprocess

import pytest

from core import prompts, rules, settings
from core.providers.mock import mock_script
from core.pipeline.shots import plan_modes

CHANNEL = settings.load_channel("k1")
CHANNEL_DIR = settings.channel_dir("k1")
FORBIDDEN = prompts.load(CHANNEL_DIR, CHANNEL, "forbidden")
FMT = settings.load_config()["format"]
IDEA = {"title": "How a diesel engine moves a car", "device": "inline-4 turbo-diesel car engine"}


@pytest.fixture
def script():
    return mock_script(IDEA, ["f1"])


def _kf_prompt(script, desc=None):
    shot = script["shots"][4]
    return prompts.keyframe_prompt(
        channel=CHANNEL, forbidden=FORBIDDEN, kf_id="K05", which="end", shot=shot,
        frame_desc=desc or shot["end_frame_desc"], refs=[{"description": "museum cutaway"}],
        prev_kf="K04", lessons=[])


def test_keyframe_prompt_has_all_nine_headers_and_forbidden_list(script):
    p = _kf_prompt(script)
    assert rules.check_keyframe_prompt(p, FORBIDDEN) == []
    assert p.rstrip().endswith(FORBIDDEN)
    assert "any woman or girl" in p


def test_short_keyframe_prompt_is_rejected(script):
    errs = rules.check_keyframe_prompt(_kf_prompt(script, desc="A diesel engine."), FORBIDDEN)
    assert any("çok kısa" in e for e in errs)


def test_prompt_mentioning_a_woman_is_rejected(script):
    desc = script["shots"][0]["end_frame_desc"] + " A woman stands next to the car."
    errs = rules.check_keyframe_prompt(_kf_prompt(script, desc=desc), FORBIDDEN)
    assert any("kadın" in e for e in errs)


def test_negated_mentions_are_allowed():
    assert rules.female_mentions("No woman or girl anywhere, no people.") == []
    assert rules.female_mentions("A girl walks by.") == ["girl"]


def test_shot_prompt_rules(script):
    shot = script["shots"][5]
    p = prompts.shot_prompt(forbidden=FORBIDDEN, shot=shot, n_shots=11, duration_s=5,
                            start_desc=shot["start_frame_desc"], end_desc=shot["end_frame_desc"])
    assert rules.check_shot_prompt(p, FORBIDDEN) == []
    assert "no cuts" in p


def test_video_request_must_be_silent():
    rules.assert_silent_video_request(False)
    with pytest.raises(ValueError):
        rules.assert_silent_video_request(True)


def test_sfx_prompt_always_says_no_music():
    p = rules.sfx_prompt("diesel idle, cast iron, close-up, 2s", CHANNEL["sfx_suffix"])
    assert p.endswith("no music, no melody, no instruments, no voice")
    assert rules.sfx_prompt(p, CHANNEL["sfx_suffix"]) == p  # iki kez eklenmez


def test_valid_script_passes(script):
    errs, _ = rules.validate_script(script, FMT, {"f1"})
    assert errs == []


def test_script_needs_all_six_beats(script):
    for s in script["shots"]:
        if s["beat"] == 5:
            s["beat"] = 4
    errs, _ = rules.validate_script(script, FMT, {"f1"})
    assert any("eksik vuruş" in e for e in errs)


def test_script_rejects_unsourced_fact_and_bad_shot_count(script):
    script["shots"][4]["fact_ids"] = ["f99"]
    script["shots"] = script["shots"][:7]
    errs, _ = rules.validate_script(script, FMT, {"f1"})
    assert any("kaynaksız" in e for e in errs)
    assert any("sahne sayısı" in e for e in errs)


def test_numeric_fact_needs_two_sources():
    facts = {"facts": [{"id": "f1", "claim": "x", "value": "16:1", "unit": None,
                        "sources": [{"url": "https://a", "title": "a"}], "confidence": "high"}], "components": []}
    assert rules.validate_facts(facts)


def test_hybrid_mode_respects_ai_seconds_cap(script):
    timing = {"shots": [{"id": s["id"], "gen_s": 4} for s in script["shots"]]}
    cfg = {"mode": "hybrid", "max_ai_video_seconds_per_video": 24}
    modes = plan_modes(script["shots"], timing, cfg)
    assert sum(4 for m in modes.values() if m == "ai") <= 24
    low = [s["id"] for s in script["shots"] if s["motion_importance"] == "low"]
    assert all(modes[i] == "kenburns" for i in low)
    full = plan_modes(script["shots"], timing, {**cfg, "mode": "full_ai"})
    assert set(full.values()) == {"ai"}


def test_default_config_is_hybrid_with_1000_usd_monthly_cap():
    cfg = settings.load_config()
    assert cfg["video"]["mode"] == "hybrid"
    assert cfg["budget"]["max_cost_per_month"] <= 1000


@pytest.mark.parametrize("path", [".env", "venv/x", ".venv/x", "node_modules/x", "jobs/k1-0001/a.json",
                                  "ready/x/video.mp4", "a.mp4", "a.wav", "a.mp3", "data/shorts.db",
                                  "x.sqlite", "x.sqlite3"])
def test_secrets_and_media_never_go_to_github(path):
    assert subprocess.run(["git", "check-ignore", "-q", path], cwd=settings.ROOT).returncode == 0


def test_env_example_is_tracked():
    assert subprocess.run(["git", "check-ignore", "-q", ".env.example"], cwd=settings.ROOT).returncode == 1


def test_no_youtube_upload_code():
    """Kural 7: sistem YouTube'a otomatik yükleme yapmaz."""
    out = subprocess.run(["git", "grep", "-il", "-e", "youtube/v3", "-e", "videos.insert", "--", "core"],
                         cwd=settings.ROOT, capture_output=True, text=True)
    assert out.stdout.strip() == ""
