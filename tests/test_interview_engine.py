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
