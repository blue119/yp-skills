import importlib.util
from pathlib import Path


def load_module():
    script_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "subtitle_to_text.py"
    )
    spec = importlib.util.spec_from_file_location("subtitle_to_text", str(script_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_vtt_english_conversion():
    mod = load_module()
    samples_dir = Path(__file__).resolve().parents[0] / "samples"
    vtt = samples_dir / "sample_en.vtt"
    expected = "Hello and welcome to this tutorial.\n\nToday we're going to learn about video text tracks."
    out = mod.convert_subtitles_to_text(vtt, lang="en", fmt="vtt")
    assert out.strip() == expected


def test_srt_english_conversion():
    mod = load_module()
    samples_dir = Path(__file__).resolve().parents[0] / "samples"
    srt = samples_dir / "sample_en.srt"
    expected = "Hello and welcome to this tutorial.\n\nToday we're going to learn about video text tracks."
    out = mod.convert_subtitles_to_text(srt, lang="en", fmt="srt")
    assert out.strip() == expected


def test_vtt_traditional_chinese_conversion():
    mod = load_module()
    samples_dir = Path(__file__).resolve().parents[0] / "samples"
    vtt = samples_dir / "sample_zh_tw.vtt"
    expected = "大家好，歡迎收看臺灣的教學。\n\n今天我們要學習如何使用字幕檔案。"
    out = mod.convert_subtitles_to_text(vtt, lang="zh_tw", fmt="vtt")
    assert out.strip() == expected


def test_srt_simplified_chinese_conversion():
    mod = load_module()
    samples_dir = Path(__file__).resolve().parents[0] / "samples"
    srt = samples_dir / "sample_zh_cn.srt"
    expected = "大家好，欢迎观看这个教学。\n\n今天我们要学习如何使用字幕文件。"
    out = mod.convert_subtitles_to_text(srt, lang="zh_cn", fmt="srt")
    assert out.strip() == expected


def test_backwards_alias_matches():
    mod = load_module()
    samples_dir = Path(__file__).resolve().parents[0] / "samples"
    vtt = samples_dir / "sample_en.vtt"
    out_alias = mod.convert_vtt_to_text(vtt)
    out_main = mod.convert_subtitles_to_text(vtt, lang="en", fmt="vtt")
    assert out_alias.strip() == out_main.strip()
