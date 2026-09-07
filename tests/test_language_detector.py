import pytest
from app.core.language_detector import detect_introduction_language
from app.models.schemas import DetectedLanguage


def test_detect_chinese_intro():
    zh_text = "各位老师好，我叫李华，来自软件工程专业。非常荣幸能参加本次保研面试。"
    lang, reason = detect_introduction_language(zh_text)
    assert lang == DetectedLanguage.ZH
    assert "中文" in reason


def test_detect_english_intro():
    en_text = "Good morning, respected professors. My name is Alex and I'm very honored to have this opportunity."
    lang, reason = detect_introduction_language(en_text)
    assert lang == DetectedLanguage.EN
    assert "英文" in reason


def test_detect_informal_english_opening():
    en_text = "Hello professors, let me briefly introduce myself and my research background in NLP."
    lang, reason = detect_introduction_language(en_text)
    assert lang == DetectedLanguage.EN


def test_detect_informal_chinese_opening():
    zh_text = "老师好！我是张三，本科期间主要做分布式计算与缓存优化。"
    lang, reason = detect_introduction_language(zh_text)
    assert lang == DetectedLanguage.ZH


def test_detect_mixed_starts_with_english():
    # 开头英文，后续夹带中文
    mixed_text = "Good afternoon professors. 接下来我用中文向各位老师详细汇报我的科研项目经历..."
    lang, reason = detect_introduction_language(mixed_text)
    assert lang == DetectedLanguage.EN


def test_detect_mixed_starts_with_chinese():
    # 开头中文，后续夹带英文
    mixed_text = "各位老师下午好，接下来由我进行汇报。My main research interest lies in Deep Learning..."
    lang, reason = detect_introduction_language(mixed_text)
    assert lang == DetectedLanguage.ZH
