import json
import random
from pathlib import Path
from typing import List, Optional, Dict
from app.config import settings
from app.models.schemas import QuestionItem, QuestionCategory


class QuestionRepository:
    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or settings.QUESTION_BANK_PATH
        self._questions: List[QuestionItem] = []
        self._by_id: Dict[str, QuestionItem] = {}
        self._last_mtime: float = 0.0
        self.reload()

    def reload(self) -> None:
        """从 JSON 文件重新载入题库"""
        if not self.file_path.exists():
            self._questions = []
            self._by_id = {}
            return

        try:
            mtime = self.file_path.stat().st_mtime
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._questions = [QuestionItem(**item) for item in data]
                self._by_id = {q.id: q for q in self._questions}
                self._last_mtime = mtime
        except Exception as e:
            print(f"Error loading question bank: {e}")

    def _ensure_fresh(self) -> None:
        """检查文件修改时间，若发生变更则自动毫秒级重新加载到内存"""
        try:
            if self.file_path.exists():
                mtime = self.file_path.stat().st_mtime
                if mtime > self._last_mtime:
                    self.reload()
        except Exception:
            pass

    def get_by_id(self, question_id: str) -> Optional[QuestionItem]:
        self._ensure_fresh()
        return self._by_id.get(question_id)

    def get_by_category(self, category: QuestionCategory) -> List[QuestionItem]:
        self._ensure_fresh()
        return [q for q in self._questions if q.category == category]

    def sample_questions(self, category: QuestionCategory, count: int = 2) -> List[QuestionItem]:
        """随机抽取指定类别的问题，若题目不足则全部返回"""
        self._ensure_fresh()
        candidates = self.get_by_category(category)
        if not candidates:
            return []
        sample_size = min(len(candidates), count)
        return random.sample(candidates, sample_size)

    def all_questions(self) -> List[QuestionItem]:
        self._ensure_fresh()
        return self._questions

# 单例仓库
question_repo = QuestionRepository()
