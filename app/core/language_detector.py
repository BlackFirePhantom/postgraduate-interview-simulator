import re
from typing import Tuple
from app.models.schemas import DetectedLanguage


def is_chinese_char(uchar: str) -> bool:
    """判断单个字符是否为中文字符"""
    return '\u4e00' <= uchar <= '\u9fff'


def detect_introduction_language(text: str) -> Tuple[DetectedLanguage, str]:
    """
    判断候选人自我介绍是从中文开始还是从英文开始。
    
    返回:
        Tuple[DetectedLanguage, str]: (语言枚举, 判定理由)
    """
    cleaned = text.strip()
    if not cleaned:
        return DetectedLanguage.ZH, "输入为空，默认按中文流程处理"

    # 提取前 80 个字符（或前两句话）重点分析开端
    prefix = cleaned[:80].strip()
    
    # 去除标点符号与空白
    # 查找第一个有效语义字符/词
    match_zh = re.search(r'[\u4e00-\u9fff]', prefix)
    match_en = re.search(r'[a-zA-Z]{2,}', prefix)
    
    # 典型英文开场常用短语
    en_openings = [
        "good morning", "good afternoon", "dear professors", "honored professors",
        "hello", "hi ", "my name is", "first of all", "thank you for",
        "it is my honor", "i am glad", "let me introduce myself"
    ]
    lower_prefix = prefix.lower()
    for phrase in en_openings:
        if lower_prefix.startswith(phrase):
            return DetectedLanguage.EN, f"检测到英文经典开场词 '{phrase}'，判定为英文开场"

    # 典型中文开场词
    zh_openings = [
        "各位老师", "尊敬的老师", "老师好", "您好", "大家好",
        "我叫", "我是", "很荣幸", "首先", "感谢各位老师"
    ]
    for phrase in zh_openings:
        if prefix.startswith(phrase):
            return DetectedLanguage.ZH, f"检测到中文礼貌开场词 '{phrase}'，判定为中文开场"

    # 若没有命中开头短语，比较前文第一个出现的语言类型及其位置
    zh_first_pos = match_zh.start() if match_zh else 9999
    en_first_pos = match_en.start() if match_en else 9999

    # 如果前部明显先出现中文
    if zh_first_pos < en_first_pos:
        zh_count = sum(1 for c in prefix if is_chinese_char(c))
        en_word_count = len(re.findall(r'[a-zA-Z]+', prefix))
        if zh_count >= 3:
            return DetectedLanguage.ZH, f"开头先出现中文表述（汉字数: {zh_count}），判定为中文开场"

    # 如果前部先出现英文
    if en_first_pos < zh_first_pos:
        en_words = re.findall(r'[a-zA-Z]+', prefix)
        if len(en_words) >= 2:
            return DetectedLanguage.EN, f"开头先出现英文表述（包含单词: {' '.join(en_words[:3])}...），判定为英文开场"

    # 全文宏观统筹统计
    total_zh = sum(1 for c in cleaned if is_chinese_char(c))
    total_en_words = len(re.findall(r'[a-zA-Z]+', cleaned))

    if total_en_words > total_zh * 1.2 and total_en_words >= 10:
        return DetectedLanguage.EN, f"全文英文词数({total_en_words})远多于中文字数({total_zh})，判定为英文自我介绍"
    
    return DetectedLanguage.ZH, f"综合判定为中文自我介绍（中文字数: {total_zh}）"
