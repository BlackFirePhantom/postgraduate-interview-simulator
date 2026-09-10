import os
import asyncio
from pathlib import Path
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.data.repository import question_repo
from app.core.interview_engine import session_manager
from app.core.tts_service import get_or_generate_audio, warmup_cache_for_questions
from app.models.schemas import (
    SessionStatus,
    IntroRequest,
    AnswerRequest,
    QuestionCategory,
    QuestionItem,
    InterviewMode,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：服务启动时异步预热题库语音缓存"""
    # 异步预热，不阻塞主服务启动
    asyncio.create_task(warmup_cache_for_questions(question_repo.all_questions()))
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="支持沉浸式考官人声提问、手机访问与中英文自我介绍动态流转的保研模拟面试系统",
    version="1.1.0",
    lifespan=lifespan,
)

# 允许跨域（便于移动端与不同端口访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启用 GZip 压缩（题目库 JSON 达 470KB，启用 GZip 后大幅压缩至 170KB，跨公网极速传输）
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 静态资源与页面路径
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "css").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "js").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "audio_cache").mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root():
    """主页直接提供给手机端与桌面端访问"""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(
            str(index_file),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return {"message": f"欢迎使用 {settings.APP_NAME}，静态页面正在构建中。"}


@app.post("/api/interview/start", response_model=SessionStatus)
async def start_interview(
    questions_per_stage: Optional[int] = Query(None, ge=1, le=5),
    mode: Optional[InterviewMode] = Query(None),
    category: Optional[QuestionCategory] = Query(None),
    count: Optional[int] = Query(None, ge=1, le=50),
):
    """开启一场全新的保研模拟面试或单项专项练习"""
    actual_mode = mode or InterviewMode.FULL
    session = session_manager.create_session(
        questions_per_stage=questions_per_stage,
        mode=actual_mode,
        target_category=category,
        specialized_count=count,
    )
    if actual_mode == InterviewMode.SPECIALIZED:
        target_cat = category or QuestionCategory.ACADEMIC
        target_cnt = count or 5
        session.start_specialized(category=target_cat, count=target_cnt)
    return session.get_status()


@app.post("/api/interview/{session_id}/intro", response_model=SessionStatus)
async def submit_intro(session_id: str, payload: IntroRequest):
    """
    提交自我介绍文本：
    自动检测自我介绍是中文还是英文开场，并动态决定提问路线：
    - 中文开场 -> 先考察一般问题或专业问题，后续切入英语问题
    - 英文开场 -> 优先考察英语问题，后续进入专业与一般问题
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在或已过期")
    
    status = session.start_with_intro(payload.text)
    return status


@app.post("/api/interview/{session_id}/answer")
async def submit_answer(session_id: str, payload: AnswerRequest):
    """提交对当前题目的回答，返回得分反馈及推进后的面试状态"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在或已过期")
    
    try:
        evaluation = session.submit_answer(payload.question_id, payload.answer_text)
        current_status = session.get_status()
        return {
            "evaluation": evaluation,
            "status": current_status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/interview/{session_id}/status", response_model=SessionStatus)
async def get_session_status(session_id: str):
    """获取当前面试进行状态"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在或已过期")
    return session.get_status()


@app.get("/api/interview/{session_id}/report")
async def get_session_report(session_id: str):
    """获取最终完整面试评估报告"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在或已过期")
    if not session.is_finished:
        raise HTTPException(status_code=400, detail="面试尚未结束，无法生成最终报告")
    return session.overall_report


@app.get("/api/audio/tts")
async def get_tts_audio(text: str, voice: Optional[str] = None, rate: Optional[str] = None):
    """
    提供真实考官与标准回答语音合成音频（高保真神经人声 MP3 格式）。
    中文为沉稳专业的男考官 (Yunjian)，英文为学术男教授 (Christopher)。
    支持通过 rate 参数微调朗读语速（如标答跟读纠音采用标准原速 +0%）。
    具备服务端 MD5 缓存，秒级响应。
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="文本内容不能为空")
    try:
        audio_file = await get_or_generate_audio(text, voice=voice, rate=rate)
        return FileResponse(
            str(audio_file),
            media_type="audio/mpeg",
            headers={"Cache-Control": "public, max-age=86400"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"考官语音合成失败: {str(e)}")


@app.get("/api/questions", response_model=List[QuestionItem])
async def list_questions(category: Optional[QuestionCategory] = None):
    """查询或浏览当前题库中收录的题目"""
    if category:
        return question_repo.get_by_category(category)
    return question_repo.all_questions()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
