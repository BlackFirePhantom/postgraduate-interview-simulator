import re
from typing import List
from app.models.schemas import QuestionItem, EvaluationResult
from app.config import settings


class AnswerEvaluator:
    """
    负责对考生的回答进行评分与反馈。
    默认采用基于关键词与要点覆盖的启发式规则评估，并预留大模型 API 接口。
    """

    @classmethod
    def evaluate(cls, question: QuestionItem, answer: str) -> EvaluationResult:
        """评估候选人对某道题目的回答"""
        cleaned = answer.strip()
        
        # 1. 极短回答处理
        if len(cleaned) < 5:
            return EvaluationResult(
                score=20,
                feedback="回答过于简短，未能展现出对该问题的深入理解和专业素养，建议详细展开核心论点与背景。",
                key_points_covered=[],
                missing_points=question.tips
            )

        # 2. 检查踩分关键词
        keywords = question.keywords or []
        covered_kw = []
        for kw in keywords:
            # 大小写不敏感匹配
            if re.search(re.escape(kw), cleaned, re.IGNORECASE):
                covered_kw.append(kw)

        kw_ratio = len(covered_kw) / max(len(keywords), 1)

        # 3. 检查答题要点 (tips) 启发式覆盖
        covered_tips: List[str] = []
        missing_tips: List[str] = []
        for tip in question.tips:
            # 提取 tip 中的关键汉字或英文词进行粗匹配
            tokens = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', tip)
            match_count = sum(1 for tok in tokens if re.search(re.escape(tok), cleaned, re.IGNORECASE))
            if match_count >= 1:
                covered_tips.append(tip)
            else:
                missing_tips.append(tip)

        tip_ratio = len(covered_tips) / max(len(question.tips), 1)

        # 4. 长度与结构加分 (针对保研面试，充实的阐述通常更受老师青睐)
        length_factor = min(len(cleaned) / 150.0, 1.0)  # 达到 150 字算充实

        # 计算综合基础得分 (40% 关键词 + 40% 要点 + 20% 阐述深度)
        raw_score = (kw_ratio * 45) + (tip_ratio * 40) + (length_factor * 15)
        score = int(min(max(raw_score, 35), 98))

        # 5. 生成建设性反馈意见
        feedback_parts = []
        if score >= 85:
            feedback_parts.append("【优秀】你的回答逻辑清晰、要点明确，对核心概念的把握非常准确，展现了扎实的学术素养。")
        elif score >= 70:
            feedback_parts.append("【良好】回答整体切中主题，覆盖了核心概念。如果能结合具体例子或实践背景深入阐述，会更具说服力。")
        else:
            feedback_parts.append("【待加强】基本观点有所体现，但针对专业/英语考点的核心论述稍显欠缺，建议对照参考答案与答题要点进一步补充。")

        if covered_kw:
            feedback_parts.append(f"成功命中的关键点：{', '.join(covered_kw[:4])}。")
        if missing_tips:
            feedback_parts.append(f"建议补充完善的方向：{missing_tips[0]}。")

        feedback = " ".join(feedback_parts)

        return EvaluationResult(
            score=score,
            feedback=feedback,
            key_points_covered=covered_tips,
            missing_points=missing_tips
        )
