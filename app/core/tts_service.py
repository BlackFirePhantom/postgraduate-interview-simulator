import hashlib
import re
import asyncio
from pathlib import Path
from typing import Optional
import edge_tts
from app.config import BASE_DIR

AUDIO_CACHE_DIR = BASE_DIR / "app" / "static" / "audio_cache"
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 默认保研考官拟真人声配置 (微软高保真神经网络音色)
VOICE_ZH = "zh-CN-YunxiNeural"         # 沉稳、专业、具有学术感的青年男考官
VOICE_EN = "en-US-ChristopherNeural"   # 地道、严谨的英文学术教授男声


def choose_voice_for_text(text: str) -> str:
    """根据问题内容自动选择中文或英文拟真考官声音"""
    en_words = len(re.findall(r'[a-zA-Z]+', text))
    zh_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    if en_words > zh_chars:
        return VOICE_EN
    return VOICE_ZH


async def get_or_generate_audio(text: str, voice: Optional[str] = None) -> Path:
    """
    获取或生成真实考官语音 MP3 文件。
    使用 MD5 散列缓存，生成一次后永久秒级响应。
    """
    selected_voice = voice or choose_voice_for_text(text)
    
    # 计算缓存指纹
    key = f"{selected_voice}_{text.strip()}"
    hash_name = hashlib.md5(key.encode("utf-8")).hexdigest()
    output_path = AUDIO_CACHE_DIR / f"{hash_name}.mp3"

    if output_path.exists() and output_path.stat().st_size > 0:
        return output_path

    # 调用微软神经网络 TTS 引擎生成真实人声音频
    communicate = edge_tts.Communicate(text, selected_voice)
    await communicate.save(str(output_path))
    return output_path


async def warmup_cache_for_questions(questions: list) -> None:
    """在后台静默预热题库音频，提升手机端秒播体验"""
    # 欢迎问候语也预热
    intro_speech = "同学你好，欢迎参加本次保研面试！请先向在座各位老师进行自我介绍。"
    tasks = [get_or_generate_audio(intro_speech, VOICE_ZH)]
    
    for q in questions:
        q_text = getattr(q, "question", None) or q.get("question", "")
        if q_text:
            tasks.append(get_or_generate_audio(q_text))
            
    # 并发限制，避免瞬时并发过高
    semaphore = asyncio.Semaphore(3)
    async def worker(t):
        async with semaphore:
            try:
                await t
            except Exception as e:
                print(f"[TTS Pre-cache Warning] {e}")

    await asyncio.gather(*(worker(t) for t in tasks))
