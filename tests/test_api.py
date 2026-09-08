import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_static_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "保研面试模拟系统" in response.text


def test_api_questions_endpoint():
    response = client.get("/api/questions")
    assert response.status_code == 200
    questions = response.json()
    assert len(questions) >= 10
    categories = {q["category"] for q in questions}
    assert "academic" in categories
    assert "english" in categories
    assert "general" in categories


def test_api_full_interview_flow():
    # 1. 创建会话
    res_start = client.post("/api/interview/start?questions_per_stage=1")
    assert res_start.status_code == 200
    data = res_start.json()
    session_id = data["session_id"]
    assert data["current_stage"] == "intro"

    # 2. 提交英文自我介绍
    res_intro = client.post(
        f"/api/interview/{session_id}/intro",
        json={"text": "Good morning professors, I am honored to attend this mock interview."}
    )
    assert res_intro.status_code == 200
    intro_data = res_intro.json()
    assert intro_data["detected_language"] == "en"
    assert intro_data["planned_stages"] == ["english", "academic", "general"]
    assert intro_data["current_question"]["category"] == "english"

    # 3. 逐题提交作答
    for i in range(3):
        # 查状态取题目
        res_status = client.get(f"/api/interview/{session_id}/status")
        status = res_status.json()
        assert not status["is_finished"]
        cur_q = status["current_question"]

        # 回答
        res_ans = client.post(
            f"/api/interview/{session_id}/answer",
            json={
                "question_id": cur_q["id"],
                "answer_text": "This is a comprehensive response addressing core theoretical questions and empirical evidence."
            }
        )
        assert res_ans.status_code == 200
        ans_json = res_ans.json()
        assert "evaluation" in ans_json
        assert ans_json["evaluation"]["score"] >= 0

    # 4. 验证结束报告
    res_report = client.get(f"/api/interview/{session_id}/report")
    assert res_report.status_code == 200
    report = res_report.json()
    assert report["total_questions_answered"] == 3
    assert "average_score" in report


def test_api_tts_endpoint():
    # 测试音频接口能够返回有效的 audio/mpeg 媒体流或缓存文件
    test_text = "同学你好，请作答。"
    response = client.get(f"/api/audio/tts?text={test_text}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert len(response.content) > 100


def test_api_specialized_mode_flow():
    # 1. 启动专项练习模式（专业课，随机抽取2题，无需自我介绍）
    res = client.post("/api/interview/start?mode=specialized&category=academic&count=2")
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "specialized"
    assert data["target_category"] == "academic"
    assert data["total_questions"] == 2
    assert data["current_question_index"] == 1
    assert data["current_question"]["category"] == "academic"
    session_id = data["session_id"]

    # 2. 直接提交第一题回答
    q1_id = data["current_question"]["id"]
    res_ans1 = client.post(
        f"/api/interview/{session_id}/answer",
        json={"question_id": q1_id, "answer_text": "专业课论述完整，核心原理阐述清楚，逻辑层层递进。"}
    )
    assert res_ans1.status_code == 200
    status1 = res_ans1.json()["status"]
    assert status1["current_question_index"] == 2

    # 3. 提交第二题回答并结束
    q2_id = status1["current_question"]["id"]
    res_ans2 = client.post(
        f"/api/interview/{session_id}/answer",
        json={"question_id": q2_id, "answer_text": "第二题重点说明架构优化和工程调试实现要点。"}
    )
    assert res_ans2.status_code == 200
    status2 = res_ans2.json()["status"]
    assert status2["is_finished"] is True

    # 4. 获取专项复盘报告
    res_rep = client.get(f"/api/interview/{session_id}/report")
    assert res_rep.status_code == 200
    report = res_rep.json()
    assert report["total_questions_answered"] == 2
    assert "核心专业课专项" in report["verdict"]


