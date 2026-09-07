import time
import uuid
from typing import Dict, List, Optional
from app.config import settings
from app.data.repository import question_repo
from app.models.schemas import (
    Stage,
    QuestionCategory,
    DetectedLanguage,
    QuestionItem,
    InterviewRecord,
    SessionStatus,
    EvaluationResult,
)
from app.core.language_detector import detect_introduction_language
from app.core.evaluator import AnswerEvaluator


STAGE_NAME_MAP = {
    Stage.INTRO: "自我介绍",
    Stage.ACADEMIC: "专业问题考查",
    Stage.ENGLISH: "英语口语与学术交流",
    Stage.GENERAL: "综合素质与综合能力",
    Stage.SUMMARY: "面试结束与综合评价",
}


class InterviewSession:
    """单个考生的模拟面试会话状态机"""

    def __init__(self, session_id: str, questions_per_stage: int = 2):
        self.session_id = session_id
        self.questions_per_stage = questions_per_stage
        self.created_at = time.time()
        
        # 流程与阶段控制
        self.current_stage: Stage = Stage.INTRO
        self.detected_language: Optional[DetectedLanguage] = None
        self.language_reason: Optional[str] = None
        self.candidate_intro: str = ""
        
        # 题库队列与题目指针
        self.planned_stages: List[Stage] = []
        self.question_queue: List[QuestionItem] = []
        self.current_index: int = 0
        self.records: List[InterviewRecord] = []
        self.is_finished: bool = False
        self.overall_report: Optional[Dict] = None

    def start_with_intro(self, intro_text: str) -> SessionStatus:
        """
        处理自我介绍：
        1. 检测中英文开端
        2. 根据语言动态确定后续提问顺序
        3. 组装题库队列并推出第一道题目
        """
        self.candidate_intro = intro_text
        lang, reason = detect_introduction_language(intro_text)
        self.detected_language = lang
        self.language_reason = reason

        # 核心逻辑：中文开场优先问一般问题或专业问题；英文开场优先问英语类问题
        if lang == DetectedLanguage.ZH:
            # 路线：一般问题 -> 专业问题 -> 英语问题
            self.planned_stages = [Stage.GENERAL, Stage.ACADEMIC, Stage.ENGLISH]
        else:
            # 路线：英语问题 -> 专业问题 -> 一般问题
            self.planned_stages = [Stage.ENGLISH, Stage.ACADEMIC, Stage.GENERAL]

        # 针对每个阶段抽取预定数量的题目
        self.question_queue = []
        stage_to_cat = {
            Stage.ACADEMIC: QuestionCategory.ACADEMIC,
            Stage.ENGLISH: QuestionCategory.ENGLISH,
            Stage.GENERAL: QuestionCategory.GENERAL,
        }

        for st in self.planned_stages:
            cat = stage_to_cat[st]
            sampled = question_repo.sample_questions(cat, self.questions_per_stage)
            self.question_queue.extend(sampled)

        # 题目索引归零
        self.current_index = 0
        if self.question_queue:
            self.current_stage = self._map_category_to_stage(self.question_queue[0].category)
        else:
            self.current_stage = Stage.SUMMARY
            self.is_finished = True

        return self.get_status()

    def submit_answer(self, question_id: str, answer_text: str) -> EvaluationResult:
        """
        提交当前题目回答：
        1. 评分评估
        2. 归档记录
        3. 指针移向下一题
        """
        if self.is_finished or not self.question_queue:
            raise ValueError("当前面试已结束或未开始")

        current_q = self.question_queue[self.current_index]
        if current_q.id != question_id:
            raise ValueError(f"题目ID不匹配，当前题目为: {current_q.id}, 提交为: {question_id}")

        # 评分
        evaluation = AnswerEvaluator.evaluate(current_q, answer_text)

        # 归档
        self.records.append(
            InterviewRecord(
                question=current_q,
                user_answer=answer_text,
                evaluation=evaluation,
                timestamp=time.time(),
            )
        )

        # 推进到下一题
        self.current_index += 1
        if self.current_index < len(self.question_queue):
            next_q = self.question_queue[self.current_index]
            self.current_stage = self._map_category_to_stage(next_q.category)
        else:
            self.current_stage = Stage.SUMMARY
            self.is_finished = True
            self.overall_report = self._generate_report()

        return evaluation

    def _generate_report(self) -> Dict:
        """面试结束后生成综合量化报告"""
        if not self.records:
            return {"average_score": 0, "summary": "未产生作答记录"}

        total_score = sum(r.evaluation.score for r in self.records)
        avg_score = round(total_score / len(self.records), 1)

        # 分类统计
        category_scores: Dict[str, List[int]] = {
            QuestionCategory.ACADEMIC.value: [],
            QuestionCategory.ENGLISH.value: [],
            QuestionCategory.GENERAL.value: [],
        }
        for r in self.records:
            cat = r.question.category.value
            category_scores[cat].append(r.evaluation.score)

        breakdown = {}
        for cat, scores in category_scores.items():
            if scores:
                breakdown[cat] = round(sum(scores) / len(scores), 1)
            else:
                breakdown[cat] = 0

        # 综合评语
        if avg_score >= 88:
            verdict = "【拟录取 / 优秀水平】考生学术基础扎实，临场反应敏锐，表达清晰沉稳，符合重点实验室选拔要求。"
        elif avg_score >= 75:
            verdict = "【备选良好】考生综合素质较好，针对专业与通用问题具备较好分析能力，若在英语或深层原理上稍加精进将更有竞争力。"
        else:
            verdict = "【需积极巩固】考生基础概念或英语表达存在明显薄弱项，建议重点强化参考要点并加强实战演练。"

        return {
            "average_score": avg_score,
            "category_breakdown": breakdown,
            "total_questions_answered": len(self.records),
            "verdict": verdict,
            "intro_language": self.detected_language.value if self.detected_language else "unknown",
            "language_reason": self.language_reason,
        }

    def get_current_question(self) -> Optional[QuestionItem]:
        if self.is_finished or self.current_stage == Stage.INTRO:
            return None
        if 0 <= self.current_index < len(self.question_queue):
            return self.question_queue[self.current_index]
        return None

    def get_status(self) -> SessionStatus:
        cur_q = self.get_current_question()
        return SessionStatus(
            session_id=self.session_id,
            current_stage=self.current_stage,
            stage_name_cn=STAGE_NAME_MAP.get(self.current_stage, "面试进行中"),
            detected_language=self.detected_language,
            language_reason=self.language_reason,
            planned_stages=self.planned_stages,
            current_question=cur_q,
            current_question_index=self.current_index + 1 if cur_q else 0,
            total_questions=len(self.question_queue),
            is_finished=self.is_finished,
            records=self.records,
            overall_report=self.overall_report,
        )

    @staticmethod
    def _map_category_to_stage(category: QuestionCategory) -> Stage:
        if category == QuestionCategory.ACADEMIC:
            return Stage.ACADEMIC
        elif category == QuestionCategory.ENGLISH:
            return Stage.ENGLISH
        else:
            return Stage.GENERAL


class SessionManager:
    """管理活跃的面试会话"""

    def __init__(self):
        self._sessions: Dict[str, InterviewSession] = {}

    def create_session(self, questions_per_stage: Optional[int] = None) -> InterviewSession:
        q_count = questions_per_stage or settings.QUESTIONS_PER_STAGE
        sid = str(uuid.uuid4())[:8]
        session = InterviewSession(session_id=sid, questions_per_stage=q_count)
        self._sessions[sid] = session
        return session

    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        return self._sessions.get(session_id)


# 全局单例会话管理器
session_manager = SessionManager()
InterviewEngine = SessionManager
