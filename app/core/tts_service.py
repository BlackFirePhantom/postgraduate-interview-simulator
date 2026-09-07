import hashlib
import re
import asyncio
from pathlib import Path
from typing import Optional, Tuple
import edge_tts
from app.config import BASE_DIR

AUDIO_CACHE_DIR = BASE_DIR / "app" / "static" / "audio_cache"
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 严肃高压考官人声配置 (具有威严感的中年教授，语速加快，直切主题)
VOICE_ZH = "zh-CN-YunjianNeural"         # 沉稳、严谨、深具压迫感的资深主考官
RATE_ZH = "+22%"                         # 语速明显加快，节奏紧凑，模拟听多套话后的雷厉风行风格
PITCH_ZH = "-4Hz"                        # 语调微降，增添严肃冷峻的考场压迫感

VOICE_EN = "en-US-ChristopherNeural"     # 严谨、不苟言笑的英文学术教授
RATE_EN = "+20%"                         # 英文提问语速加快
PITCH_EN = "-3Hz"                        # 语调深沉严肃


def choose_voice_params(text: str) -> Tuple[str, str, str]:
    """根据问题内容自动选择中英文严肃考官音色及语速语调参数"""
    en_words = len(re.findall(r'[a-zA-Z]+', text))
    zh_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    if en_words > zh_chars:
        return VOICE_EN, RATE_EN, PITCH_EN
    return VOICE_ZH, RATE_ZH, PITCH_ZH


async def get_or_generate_audio(
    text: str,
    voice: Optional[str] = None,
    rate: Optional[str] = None,
    pitch: Optional[str] = None
) -> Path:
    """
    获取或生成严肃考官语音 MP3 文件。
    参数包含音色、语速与音调，利用 MD5 进行服务端秒级缓存。
    """
    default_voice, default_rate, default_pitch = choose_voice_params(text)
    selected_voice = voice or default_voice
    selected_rate = rate or default_rate
    selected_pitch = pitch or default_pitch
    
    # 将文本、音色、语速、音调一同计入缓存指纹
    key = f"{selected_voice}_{selected_rate}_{selected_pitch}_{text.strip()}"
    hash_name = hashlib.md5(key.encode("utf-8")).hexdigest()
    output_path = AUDIO_CACHE_DIR / f"{hash_name}.mp3"

    if output_path.exists() and output_path.stat().st_size > 0:
        return output_path

    # 调用微软神经网络 TTS 引擎生成具有压迫感与快速语速的人声音频
    communicate = edge_tts.Communicate(
        text.strip(),
        selected_voice,
        rate=selected_rate,
        pitch=selected_pitch
    )
    await communicate.save(str(output_path))
    return output_path


async def warmup_cache_for_questions(questions: list) -> None:
    """在后台静默预热题库音频，提升手机端秒播体验"""
    # 严肃开场语
    intro_speech = "同学注意时间，在座各位老师今天已经面试了几十名同学，不要背诵长篇套话，直接陈述你的核心竞争优势与科研成果。"
    tasks = [get_or_generate_audio(intro_speech, VOICE_ZH, RATE_ZH, PITCH_ZH)]
    
    for q in questions[:30]:  # 预热前30道高频题，节约启动资源
        q_text = getattr(q, "question", None) or (q.get("question", "") if isinstance(q, dict) else "")
        if q_text:
            tasks.append(get_or_generate_audio(q_text))
            
    semaphore = asyncio.Semaphore(3)
    async def worker(t):
        async with semaphore:
            try:
                await t
            except Exception as e:
                pass

    await asyncio.gather(*(worker(t) for t in tasks))
