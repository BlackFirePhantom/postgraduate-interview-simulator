import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseModel):
    APP_NAME: str = "保研面试模拟系统"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # 默认每个阶段的抽题数量
    QUESTIONS_PER_STAGE: int = int(os.getenv("QUESTIONS_PER_STAGE", "2"))
    
    # 数据文件路径
    QUESTION_BANK_PATH: Path = BASE_DIR / "app" / "data" / "question_bank.json"

    # 可选的大模型配置（若未配置则使用内置启发式评估模块）
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat")

settings = Settings()
