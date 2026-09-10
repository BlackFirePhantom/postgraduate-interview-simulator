import pytest
from app.core.interview_engine import SessionManager
from app.models.schemas import Stage, QuestionCategory, DetectedLanguage


def test_chinese_intro_routing():
    manager = SessionManager()
    session = manager.create_session(questions_per_stage=1)
    
    zh_intro = "各位评委老师好，我是来自计算机科学与技术专业的考生李明，很荣幸参加保研面试。"
    status = session.start_with_intro(zh_intro)
    
    # 验证语言识别为中文
    assert status.detected_language == DetectedLanguage.ZH
    # 验证规划阶段：一般问题/专业问题优先，英语排在最后
    assert status.planned_stages == [Stage.GENERAL, Stage.ACADEMIC, Stage.ENGLISH]
    assert status.current_question is not None
    assert status.current_question.category == QuestionCategory.GENERAL
    assert status.total_questions == 3  # 每阶段1题，共3题


def test_english_intro_routing():
    manager = SessionManager()
    session = manager.create_session(questions_per_stage=1)
    
    en_intro = "Good morning honorable professors, my name is Ming Li. It is my great privilege to attend this interview."
    status = session.start_with_intro(en_intro)
    
    # 验证语言识别为英文
    assert status.detected_language == DetectedLanguage.EN
    # 验证规划阶段：英语问题排在第一位，随后专业与一般问题
    assert status.planned_stages == [Stage.ENGLISH, Stage.ACADEMIC, Stage.GENERAL]
    assert status.current_question is not None
    assert status.current_question.category == QuestionCategory.ENGLISH
    assert status.total_questions == 3


def test_full_interview_answering_lifecycle():
    manager = SessionManager()
    session = manager.create_session(questions_per_stage=1)
    session.start_with_intro("各位老师好，我叫王小明，非常渴望进入贵课题组深造。")

    # 依次回答所有题目
    while not session.is_finished:
        cur_q = session.get_current_question()
        assert cur_q is not None
        eval_res = session.submit_answer(
            cur_q.id,
            "我的回答是：该问题非常关键。首先从原理出发需要考虑系统资源分配，其次要兼顾并发和吞吐量，最后在实际项目中需要做充分的性能评估和容灾测试。"
        )
        assert eval_res.score > 0
        assert eval_res.feedback != ""

    status = session.get_status()
    assert status.is_finished is True
    assert status.current_stage == Stage.SUMMARY
    assert status.overall_report is not None
    assert "average_score" in status.overall_report
    assert status.overall_report["total_questions_answered"] == 3


def test_20min_full_exam_structure():
    """验证20分钟全真考场模式（共11题：5道专业题、3道英语题约5分钟、3道综合题）"""
    manager = SessionManager()
    session = manager.create_session(questions_per_stage=2)
    status = session.start_with_intro("各位评委老师好，我是刘子俊，主要研究微电子与硬件加速。")

    assert status.total_questions == 11
    # 验证各类型题目分布
    categories = [q.category for q in session.question_queue]
    assert categories.count(QuestionCategory.ACADEMIC) == 5
    assert categories.count(QuestionCategory.ENGLISH) == 3
    assert categories.count(QuestionCategory.GENERAL) == 3


def test_timeout_zero_score():
    """验证30秒未开口作答/超时放弃直接判0分"""
    manager = SessionManager()
    session = manager.create_session(questions_per_stage=1)
    session.start_with_intro("老师好，我参加面试。")

    cur_q = session.get_current_question()
    assert cur_q is not None
    eval_res = session.submit_answer(cur_q.id, "（考场30秒内未开口，超时放弃作答）")
    assert eval_res.score == 0
    assert "0分" in eval_res.feedback or "未开口" in eval_res.feedback or "超时" in eval_res.feedback


def test_specialized_academic_practice():
    """验证核心专业课专项练习（免自我介绍，自定义5题随机抽取）"""
    manager = SessionManager()
    session = manager.create_session()
    status = session.start_specialized(category=QuestionCategory.ACADEMIC, count=5)

    assert status.total_questions == 5
    assert status.current_question_index == 1
    assert status.current_question is not None
    assert status.current_question.category == QuestionCategory.ACADEMIC
    assert all(q.category == QuestionCategory.ACADEMIC for q in session.question_queue)
    assert status.stage_name_cn == "专业问题考查"


def test_specialized_english_practice():
    """验证英语专项练习（语言识别为EN，自定义3题随机抽取）"""
    manager = SessionManager()
    session = manager.create_session()
    status = session.start_specialized(category=QuestionCategory.ENGLISH, count=3)

    assert status.total_questions == 3
    assert status.detected_language == DetectedLanguage.EN
    assert status.current_question is not None
    assert status.current_question.category == QuestionCategory.ENGLISH
    assert all(q.category == QuestionCategory.ENGLISH for q in session.question_queue)


def test_specialized_general_lifecycle():
    """验证综合素质专项作答至结束并生成专项终审报告"""
    manager = SessionManager()
    session = manager.create_session()
    session.start_specialized(category=QuestionCategory.GENERAL, count=3)

    while not session.is_finished:
        cur_q = session.get_current_question()
        assert cur_q is not None
        assert cur_q.category == QuestionCategory.GENERAL
        res = session.submit_answer(cur_q.id, "在实际科研与团队协作中，我会保持积极心态，主动与导师和同门沟通并寻找解决方案。")
        assert res.score > 0

    report = session.overall_report
    assert report is not None
    assert report["total_questions_answered"] == 3
    assert "综合素质与抗压专项" in report["verdict"]


def test_give_up_answer_flow():
    """验证'我不会/查看标答'触发0分并给出引导和标答"""
    manager = SessionManager()
    session = manager.create_session(questions_per_stage=1)
    session.start_with_intro("老师好，我参加面试。")

    cur_q = session.get_current_question()
    assert cur_q is not None
    # 候选人点击'我不会'
    eval_res = session.submit_answer(cur_q.id, "我不会，请教老师指点。")
    assert eval_res.score == 0
    assert "主动放弃" in eval_res.feedback
    assert "0分" in eval_res.feedback
    assert len(cur_q.reference_answer) > 0


def test_question_bank_language_purity():
    """验证题库中英文题目与标答严格纯洁性（英文无汉字中文标点，中文无冗余英文括号夹杂）"""
    import json
    import re
    from pathlib import Path

    bank_path = Path("app/data/question_bank.json")
    with open(bank_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    zh_pattern = re.compile(r"[\u4e00-\u9fa5]")
    full_width_punct = set("，。！？：“”（）【】—、…")

    for q in questions:
        assert q["reference_answer"], f"Empty reference answer in {q['id']}"
        assert q.get("shorthand"), f"Empty shorthand in {q['id']}"
        assert not q["reference_answer"].endswith(('（', '【', '、', '，', '“', '‘', '(', '\"')), f"Truncated reference answer in {q['id']}"
        if q["category"] == "english":
            # 英语题目不得含有中文字符或中文全角标点
            assert not zh_pattern.search(q["question"]), f"EN Q contains Chinese: {q['id']}"
            assert not any(c in full_width_punct for c in q["question"]), f"EN Q contains full-width punct: {q['id']}"
            assert not zh_pattern.search(q["reference_answer"]), f"EN Ref contains Chinese: {q['id']}"
            assert not any(c in full_width_punct for c in q["reference_answer"]), f"EN Ref contains full-width punct: {q['id']}"
            # 英语标答必须精炼，严格控制在 2 至 3 句话
            sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', q["reference_answer"].replace('\n', ' ')) if s.strip()]
            assert 2 <= len(sents) <= 3, f"EN Ref must have 2-3 sentences: {q['id']} has {len(sents)}"
        else:
            # 中文题目与标答不得包含英文括号夹杂，如（Fermi Level）或（Setup Time）
            bracket_en = re.findall(r"[（\(]([A-Za-z]{2,}(?:\s+[A-Za-z]+)+)[）\)]", q["question"])
            assert not bracket_en, f"ZH Q contains English translation brackets: {q['id']} -> {bracket_en}"


