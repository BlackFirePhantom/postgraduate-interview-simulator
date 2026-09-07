from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QuestionCategory(str, Enum):
    ACADEMIC = "academic"  # 专业问题
    ENGLISH = "english"    # 英语问题
    GENERAL = "general"    # 一般问题/综合素质


class Stage(str, Enum):
    INTRO = "intro"          # 自我介绍阶段
    ACADEMIC = "academic"    # 专业问答阶段
    ENGLISH = "english"      # 英语问答阶段
    GENERAL = "general"      # 综合/一般问题阶段
    SUMMARY = "summary"      # 总结阶段


class DetectedLanguage(str, Enum):
    ZH = "zh"
    EN = "en"


class QuestionItem(BaseModel):
    id: str
    category: QuestionCategory
    subcategory: str = Field(..., description="子领域，如操作系统/动机考察/学术英语")
    question: str = Field(..., description="题目内容")
    tips: List[str] = Field(default_factory=list, description="答题关键点/要点提示")
    reference_answer: str = Field(default="", description="标准参考回答")
    keywords: List[str] = Field(default_factory=list, description="评分与踩分关键词")


class IntroRequest(BaseModel):
    text: str = Field(..., min_length=5, description="面试者自我介绍文本")


class AnswerRequest(BaseModel):
    question_id: str = Field(..., description="对应回答的问题ID")
    answer_text: str = Field(..., min_length=2, description="候选人作答文本")


class EvaluationResult(BaseModel):
    score: int = Field(..., ge=0, le=100, description="得分 0-100")
    feedback: str = Field(..., description="面试官点评与改进建议")
    key_points_covered: List[str] = Field(default_factory=list, description="已覆盖的要点")
    missing_points: List[str] = Field(default_factory=list, description="建议补充的要点")


class InterviewRecord(BaseModel):
    question: QuestionItem
    user_answer: str
    evaluation: EvaluationResult
    timestamp: float


class SessionStatus(BaseModel):
    session_id: str
    current_stage: Stage
    stage_name_cn: str
    detected_language: Optional[DetectedLanguage] = None
    language_reason: Optional[str] = None
    planned_stages: List[Stage] = Field(default_factory=list)
    current_question: Optional[QuestionItem] = None
    current_question_index: int = 0
    total_questions: int = 0
    is_finished: bool = False
    records: List[InterviewRecord] = Field(default_factory=list)
    overall_report: Optional[Dict[str, Any]] = None
