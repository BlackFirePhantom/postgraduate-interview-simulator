/**
 * 保研面试模拟系统前端交互与沉浸式语音控制逻辑
 * 支持考官拟真原声超快语速提问、声波跳动、20分钟全场倒计时、30秒开口强制限时与自适应状态机推进
 */

const state = {
  sessionId: null,
  questionsPerStage: 2,   // 2 表示 20分钟高压实战(11题)，1 表示极速自测(3题)
  currentStatus: null,
  isRecording: false,
  recognition: null,
  activeTextarea: null,
  activeMicBtn: null,
  activeMicLabel: null,
  enableVoice: true,      // 默认开启考官原声自动提问
  currentAudio: null,     // 当前正在播放的 Audio 实例
  examTotalSeconds: 1200, // 20分钟全场倒计时 (秒)
  examTimerInterval: null,
  deadlineSeconds: 30,    // 30秒开口限时
  deadlineInterval: null,
  hasSpokenOrTyped: false,
};

// DOM 元素引用
const views = {
  welcome: document.getElementById("view-welcome"),
  intro: document.getElementById("view-intro"),
  question: document.getElementById("view-question"),
  report: document.getElementById("view-report"),
};

const stageBadge = document.getElementById("stage-badge");
const progressBar = document.getElementById("progress-bar");
const modalFeedback = document.getElementById("modal-feedback");
const btnToggleVoice = document.getElementById("btn-toggle-voice");
const examTimerBar = document.getElementById("exam-timer-bar");
const examTimeDisplay = document.getElementById("exam-time-display");

// 初始化
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  setupSpeechRecognition();
  updateProgress(0, "等待开始");
});

function switchView(viewName) {
  Object.keys(views).forEach((k) => {
    views[k].style.display = k === viewName ? "flex" : "none";
  });
}

function updateProgress(percent, stageText) {
  progressBar.style.width = `${percent}%`;
  if (stageText) {
    stageBadge.textContent = stageText;
  }
}

// ---------------- 20分钟全场考试总计时器 ----------------
function startExamTimer() {
  stopExamTimer();
  state.examTotalSeconds = 1200; // 20分钟
  examTimerBar.style.display = "flex";
  updateExamTimeDisplay();

  state.examTimerInterval = setInterval(() => {
    state.examTotalSeconds--;
    if (state.examTotalSeconds <= 0) {
      clearInterval(state.examTimerInterval);
      state.examTotalSeconds = 0;
      updateExamTimeDisplay();
      alert("⏰ 全场20分钟面试时间已到！请尽快完成当前题目收尾。");
    } else {
      updateExamTimeDisplay();
    }
  }, 1000);
}

function stopExamTimer() {
  if (state.examTimerInterval) {
    clearInterval(state.examTimerInterval);
    state.examTimerInterval = null;
  }
}

function updateExamTimeDisplay() {
  const m = Math.floor(state.examTotalSeconds / 60);
  const s = state.examTotalSeconds % 60;
  examTimeDisplay.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

// ---------------- 30秒开口限时逻辑 ----------------
function startResponseDeadline() {
  stopResponseDeadline();
  state.deadlineSeconds = 30;
  state.hasSpokenOrTyped = false;

  const card = document.getElementById("deadline-card");
  const secEl = document.getElementById("deadline-seconds");
  const barEl = document.getElementById("deadline-bar");
  const badgeEl = document.getElementById("deadline-badge");
  const tipEl = document.getElementById("deadline-tip");

  if (!card || !secEl || !barEl) return;

  card.classList.remove("answered");
  barEl.classList.remove("urgent");
  barEl.style.width = "100%";
  secEl.textContent = "30";
  badgeEl.textContent = "30秒内必须开口";
  badgeEl.style.background = "#ffe4e6";
  badgeEl.style.color = "#b91c1c";
  tipEl.textContent = "⚠️ 考官提问后30秒内必须开口作答（打字或语音），超时视为放弃该题，直接记0分！";

  state.deadlineInterval = setInterval(() => {
    state.deadlineSeconds--;
    
    // 更新UI
    secEl.textContent = Math.max(0, state.deadlineSeconds);
    const pct = Math.max(0, (state.deadlineSeconds / 30) * 100);
    barEl.style.width = `${pct}%`;

    if (state.deadlineSeconds <= 10) {
      barEl.classList.add("urgent");
      badgeEl.textContent = `急！剩 ${state.deadlineSeconds} 秒`;
    }

    if (state.deadlineSeconds <= 0) {
      clearInterval(state.deadlineInterval);
      state.hasSpokenOrTyped = true;
      badgeEl.textContent = "已超时未答";
      tipEl.textContent = "❌ 30秒限时已过，考官判定未掌握该知识点，自动跳过！";

      // 自动填入超时标记并自动提交
      const textarea = document.getElementById("answer-textarea");
      textarea.value = "（考场30秒内未开口，超时放弃作答）";
      updateCharCount(textarea, "answer-char-count");
      
      setTimeout(() => {
        submitAnswer();
      }, 600);
    }
  }, 1000);
}

function markCandidateAnswered() {
  if (state.hasSpokenOrTyped) return;
  state.hasSpokenOrTyped = true;
  stopResponseDeadline();

  const card = document.getElementById("deadline-card");
  const secEl = document.getElementById("deadline-seconds");
  const barEl = document.getElementById("deadline-bar");
  const badgeEl = document.getElementById("deadline-badge");
  const tipEl = document.getElementById("deadline-tip");

  if (!card) return;
  card.classList.add("answered");
  if (barEl) barEl.classList.remove("urgent");
  secEl.textContent = "已开口作答 ✅";
  badgeEl.textContent = "作答进行中";
  badgeEl.style.background = "#dcfce7";
  badgeEl.style.color = "#15803d";
  tipEl.textContent = "已成功开口，限时暂停。请沉着完整阐述，完成后点击下方提交本题回答。";
}

function stopResponseDeadline() {
  if (state.deadlineInterval) {
    clearInterval(state.deadlineInterval);
    state.deadlineInterval = null;
  }
}

function setupEventListeners() {
  // 0. 全局考官原声开关
  btnToggleVoice.addEventListener("click", () => {
    state.enableVoice = !state.enableVoice;
    if (state.enableVoice) {
      btnToggleVoice.textContent = "🔊 考官原声: 开";
      btnToggleVoice.style.background = "#eff6ff";
      btnToggleVoice.style.borderColor = "#93c5fd";
      btnToggleVoice.style.color = "#1e40af";
    } else {
      btnToggleVoice.textContent = "🔇 考官原声: 关";
      btnToggleVoice.style.background = "#f1f5f9";
      btnToggleVoice.style.borderColor = "#cbd5e1";
      btnToggleVoice.style.color = "#64748b";
      stopVoice();
    }
  });

  // 1. 题量/模式选择
  document.querySelectorAll(".q-count-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".q-count-btn").forEach((b) => {
        b.classList.remove("active");
        b.style.borderColor = "#cbd5e1";
        b.style.background = "#ffffff";
        b.style.color = "#475569";
        b.style.fontWeight = "normal";
      });
      btn.classList.add("active");
      btn.style.borderColor = "#dc2626";
      btn.style.background = "#fef2f2";
      btn.style.color = "#991b1b";
      btn.style.fontWeight = "700";
      state.questionsPerStage = parseInt(btn.getAttribute("data-count"), 10);
    });
  });

  // 2. 开始面试
  document.getElementById("btn-start-interview").addEventListener("click", startInterview);

  // 3. 预设自我介绍文案 (刘子俊背景定制)
  const introTextarea = document.getElementById("intro-textarea");
  document.getElementById("btn-preset-zh").addEventListener("click", () => {
    introTextarea.value =
      "各位老师好，我叫刘子俊，来自微电子科学与工程专业。在本科期间我GPA 3.69，专业排名前14%，主持过一项国家级大创，并作为主力荣获集创赛企业大奖全国第一名、嵌赛FPGA全国一等奖、机器人大赛全国一等奖。主攻芯片底层硬件加速与软硬件协同。非常荣幸参加面试！";
    updateCharCount(introTextarea, "intro-char-count");
  });

  document.getElementById("btn-preset-en").addEventListener("click", () => {
    introTextarea.value =
      "Good morning distinguished professors. My name is Liu Zijun, majoring in Microelectronics Science and Engineering. I have a solid foundation in semiconductor physics and IC design, with three national first prizes including the National IC Innovation Competition. I am eager to pursue my master's degree in your laboratory.";
    updateCharCount(introTextarea, "intro-char-count");
  });

  introTextarea.addEventListener("input", () => {
    updateCharCount(introTextarea, "intro-char-count");
  });

  const answerTextarea = document.getElementById("answer-textarea");
  answerTextarea.addEventListener("input", () => {
    updateCharCount(answerTextarea, "answer-char-count");
    markCandidateAnswered(); // 只要键盘输入，即视为已开口，停止30秒倒计时
  });

  // 4. 提交自我介绍
  document.getElementById("btn-submit-intro").addEventListener("click", submitIntro);

  // 5. 提示展开收起
  const tipsToggle = document.getElementById("tips-toggle");
  const tipsBody = document.getElementById("tips-body");
  const tipsArrow = document.getElementById("tips-arrow");
  tipsToggle.addEventListener("click", () => {
    const isHidden = tipsBody.style.display === "none";
    tipsBody.style.display = isHidden ? "block" : "none";
    tipsArrow.textContent = isHidden ? "▲" : "▼";
  });

  // 6. 重播自我介绍考官引导原声
  document.getElementById("btn-replay-intro-audio").addEventListener("click", () => {
    playInterviewerVoice(
      "同学注意把控时间！今天我们已经面试了几十名考生，不要讲空话套话。请直接用最精炼的语言，汇报你的核心硬核竞争力与科研实践成果！",
      document.getElementById("intro-avatar"),
      document.getElementById("intro-speaking-status")
    );
  });

  // 7. 重播题目原声
  document.getElementById("btn-replay-audio").addEventListener("click", () => {
    const curQ = state.currentStatus?.current_question;
    if (curQ) {
      playInterviewerVoice(
        curQ.question,
        document.getElementById("question-avatar"),
        document.getElementById("question-speaking-status")
      );
    }
  });

  // 8. 麦克风语音录入
  document.getElementById("btn-intro-mic").addEventListener("click", () => {
    toggleRecording(
      document.getElementById("intro-textarea"),
      document.getElementById("btn-intro-mic"),
      document.getElementById("intro-mic-label"),
      "intro-char-count"
    );
  });

  document.getElementById("btn-answer-mic").addEventListener("click", () => {
    markCandidateAnswered(); // 点击麦克风开始录入，视为已开口，停止30秒倒计时
    toggleRecording(
      document.getElementById("answer-textarea"),
      document.getElementById("btn-answer-mic"),
      document.getElementById("answer-mic-label"),
      "answer-char-count"
    );
  });

  // 9. 提交回答
  document.getElementById("btn-submit-answer").addEventListener("click", submitAnswer);

  // 10. 模态框下一题
  document.getElementById("btn-next-question").addEventListener("click", () => {
    modalFeedback.style.display = "none";
    renderCurrentState();
  });

  // 11. 重新开始
  document.getElementById("btn-restart").addEventListener("click", () => {
    stopRecording();
    stopVoice();
    stopExamTimer();
    stopResponseDeadline();
    state.sessionId = null;
    state.currentStatus = null;
    introTextarea.value = "";
    answerTextarea.value = "";
    examTimerBar.style.display = "none";
    switchView("welcome");
    updateProgress(0, "准备中");
  });
}

function updateCharCount(textarea, countElId) {
  const countEl = document.getElementById(countElId);
  if (countEl) {
    countEl.textContent = `${textarea.value.length} 字`;
  }
}

// ---------------- 沉浸式考官人声发音播放器 ----------------
function stopVoice() {
  if (state.currentAudio) {
    state.currentAudio.pause();
    state.currentAudio = null;
  }
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
  document.querySelectorAll(".avatar").forEach((a) => a.classList.remove("speaking"));
}

function playInterviewerVoice(text, avatarEl, statusEl) {
  stopVoice();
  if (!state.enableVoice || !text) return;

  if (avatarEl) avatarEl.classList.add("speaking");
  if (statusEl) {
    statusEl.innerHTML = `
      <span>⚡ 严肃考官发问中 (语速紧凑)...</span>
      <span class="voice-wave-container">
        <span class="wave-bar" style="background: #ef4444;"></span>
        <span class="wave-bar" style="background: #ef4444;"></span>
        <span class="wave-bar" style="background: #ef4444;"></span>
        <span class="wave-bar" style="background: #ef4444;"></span>
      </span>
    `;
    statusEl.style.color = "#dc2626";
  }

  const audioUrl = `/api/audio/tts?text=${encodeURIComponent(text)}`;
  const audio = new Audio(audioUrl);
  state.currentAudio = audio;

  const onPlaybackDone = () => {
    if (avatarEl) avatarEl.classList.remove("speaking");
    if (statusEl) {
      statusEl.innerHTML = `<span>⏱️ 提问完毕，30秒内请迅速开口作答</span>`;
      statusEl.style.color = "#047857";
    }
    state.currentAudio = null;
  };

  audio.onended = onPlaybackDone;

  audio.onerror = () => {
    console.warn("服务端音频加载遇到问题，降级为浏览器本地 SpeechSynthesis 引擎");
    if ("speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      const isEn = /[a-zA-Z]{5,}/.test(text);
      utterance.lang = isEn ? "en-US" : "zh-CN";
      utterance.rate = 1.35; // 浏览器本地引擎同样极大加快语速
      utterance.onend = onPlaybackDone;
      utterance.onerror = onPlaybackDone;
      window.speechSynthesis.speak(utterance);
    } else {
      onPlaybackDone();
    }
  };

  const playPromise = audio.play();
  if (playPromise !== undefined) {
    playPromise.catch((err) => {
      console.log("浏览器自动播放限制，等待用户手势点击:", err);
      if (avatarEl) avatarEl.classList.remove("speaking");
      if (statusEl) {
        statusEl.innerHTML = `<span>点击重新听题播放</span>`;
        statusEl.style.color = "#64748b";
      }
    });
  }
}

// ---------------- 语音识别录入 (Web Speech API) ----------------
function setupSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;

  const recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = "zh-CN";

  recognition.onresult = (event) => {
    let finalTranscript = "";
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript;
      }
    }

    if (state.activeTextarea && finalTranscript) {
      state.activeTextarea.value += finalTranscript;
      updateCharCount(
        state.activeTextarea,
        state.activeTextarea.id === "intro-textarea" ? "intro-char-count" : "answer-char-count"
      );
      markCandidateAnswered(); // 语音识别命中也标记为已开口
    }
  };

  recognition.onerror = (e) => {
    console.error("语音录入错误:", e);
    stopRecording();
  };

  recognition.onend = () => {
    if (state.isRecording) {
      recognition.start();
    }
  };

  state.recognition = recognition;
}

function toggleRecording(textarea, btn, label, countElId) {
  if (!state.recognition) {
    alert("您的手机浏览器暂不支持直接网页麦克风转文字，建议在手机输入法中使用自带的语音麦克风键直接说话打字！");
    return;
  }

  if (state.isRecording) {
    stopRecording();
  } else {
    stopVoice();
    state.isRecording = true;
    state.activeTextarea = textarea;
    state.activeMicBtn = btn;
    state.activeMicLabel = label;
    btn.classList.add("recording");
    label.textContent = "正在聆听中(点击停止)...";
    try {
      state.recognition.start();
    } catch (e) {
      console.warn(e);
    }
  }
}

function stopRecording() {
  if (state.isRecording) {
    state.isRecording = false;
    if (state.activeMicBtn) {
      state.activeMicBtn.classList.remove("recording");
    }
    if (state.activeMicLabel) {
      state.activeMicLabel.textContent = "语音录入";
    }
    if (state.recognition) {
      try {
        state.recognition.stop();
      } catch (e) {}
    }
  }
}

// ---------------- API 调用与流程驱动 ----------------
async function startInterview() {
  const btn = document.getElementById("btn-start-interview");
  btn.disabled = true;
  btn.textContent = "正在创建考场并联络考官...";

  try {
    const res = await fetch(`/api/interview/start?questions_per_stage=${state.questionsPerStage}`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("启动考场失败");
    const data = await res.json();
    state.sessionId = data.session_id;
    state.currentStatus = data;

    switchView("intro");
    updateProgress(10, "环节：自我介绍");

    // 开启 20 分钟全真考试总计时器！
    startExamTimer();

    // 自动播放主考官开场问候与引导
    playInterviewerVoice(
      "同学注意把控时间！今天我们已经面试了几十名考生，不要讲空话套话。请直接用最精炼的语言，汇报你的核心硬核竞争力与科研实践成果！",
      document.getElementById("intro-avatar"),
      document.getElementById("intro-speaking-status")
    );
  } catch (err) {
    alert("连接考场服务失败: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "进入考场 · 开启20分钟高压实战";
  }
}

async function submitIntro() {
  stopRecording();
  stopVoice();

  const introText = document.getElementById("intro-textarea").value.trim();
  if (introText.length < 5) {
    alert("自我介绍过短，请多说几句再提交。");
    return;
  }

  const btn = document.getElementById("btn-submit-intro");
  btn.disabled = true;
  btn.textContent = "考官正在分析开场语言并确定路线...";

  try {
    const res = await fetch(`/api/interview/${state.sessionId}/intro`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: introText }),
    });

    if (!res.ok) throw new Error("提交自我介绍失败");
    const data = await res.json();
    state.currentStatus = data;

    renderCurrentState();
  } catch (err) {
    alert("提交失败: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "提交自我介绍";
  }
}

async function submitAnswer() {
  stopRecording();
  stopVoice();
  stopResponseDeadline(); // 提交后关闭当前题目的30秒倒计时

  const answerText = document.getElementById("answer-textarea").value.trim();
  if (answerText.length < 2) {
    alert("作答内容不能为空，请作答后再提交。");
    return;
  }

  const curQ = state.currentStatus.current_question;
  if (!curQ) return;

  const btn = document.getElementById("btn-submit-answer");
  btn.disabled = true;
  btn.textContent = "考官正在打分并生成点评...";

  try {
    const res = await fetch(`/api/interview/${state.sessionId}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question_id: curQ.id,
        answer_text: answerText,
      }),
    });

    if (!res.ok) throw new Error("提交回答失败");
    const result = await res.json();
    
    // 更新本地会话状态
    state.currentStatus = result.status;

    // 清空回答输入框
    document.getElementById("answer-textarea").value = "";
    updateCharCount(document.getElementById("answer-textarea"), "answer-char-count");

    // 弹出即时反馈 Bottom Sheet
    showFeedbackModal(result.evaluation, curQ);
  } catch (err) {
    alert("提交回答失败: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "提交本题回答";
  }
}

function showFeedbackModal(evaluation, question) {
  document.getElementById("modal-score").textContent = evaluation.score;
  document.getElementById("modal-feedback-text").textContent = evaluation.feedback;
  document.getElementById("modal-reference-answer").textContent =
    question.reference_answer || "（本题注重个人思路表达与逻辑完整性）";
  modalFeedback.style.display = "flex";
}

function renderCurrentState() {
  const status = state.currentStatus;
  if (!status) return;

  if (status.is_finished) {
    renderReportView();
    return;
  }

  switchView("question");

  const q = status.current_question;
  if (!q) return;

  // 1. 设置分类徽标与题目
  const catBadge = document.getElementById("question-category-badge");
  catBadge.className = "badge-tag " + getCategoryClass(q.category);
  catBadge.textContent = getCategoryName(q.category);

  document.getElementById("question-subcategory").textContent = q.subcategory;
  document.getElementById("question-index-badge").textContent = `第 ${status.current_question_index}/${status.total_questions} 题`;
  document.getElementById("question-text").textContent = q.question;

  // 2. 根据阶段调整考官角色称呼
  const roleNameEl = document.getElementById("interviewer-role-name");
  if (q.category === "academic") {
    roleNameEl.textContent = "核心专业课考官";
  } else if (q.category === "english") {
    roleNameEl.textContent = "英语口语考官 (5分钟)";
  } else {
    roleNameEl.textContent = "综合素质评审考官";
  }

  // 3. 填充思考提示
  const tipsList = document.getElementById("tips-list");
  tipsList.innerHTML = "";
  if (q.tips && q.tips.length > 0) {
    q.tips.forEach((tip) => {
      const li = document.createElement("li");
      li.textContent = tip;
      tipsList.appendChild(li);
    });
  } else {
    tipsList.innerHTML = "<li>无特殊限制，直击核心物理/工程本质。</li>";
  }

  document.getElementById("tips-body").style.display = "none";
  document.getElementById("tips-arrow").textContent = "▼";

  // 4. 更新进度条
  const progressPercent = Math.round((status.current_question_index / (status.total_questions + 1)) * 100);
  updateProgress(progressPercent, status.stage_name_cn);

  // 5. 启动 30 秒限时作答开口计时器！
  startResponseDeadline();

  // 6. 核心交互：极速播放考官严肃发问语音
  playInterviewerVoice(
    q.question,
    document.getElementById("question-avatar"),
    document.getElementById("question-speaking-status")
  );
}

function renderReportView() {
  switchView("report");
  updateProgress(100, "面试终审报告");
  stopVoice();
  stopExamTimer();
  stopResponseDeadline();

  const report = state.currentStatus.overall_report;
  if (!report) return;

  document.getElementById("report-avg-score").textContent = report.average_score || 0;
  document.getElementById("report-verdict").textContent = report.verdict || "考核完成。";

  // 维度拆解
  const breakdown = report.category_breakdown || {};
  const acadScore = breakdown.academic || 0;
  const engScore = breakdown.english || 0;
  const genScore = breakdown.general || 0;

  document.getElementById("score-academic").textContent = `${acadScore} 分`;
  document.getElementById("bar-academic").style.width = `${acadScore}%`;

  document.getElementById("score-english").textContent = `${engScore} 分`;
  document.getElementById("bar-english").style.width = `${engScore}%`;

  document.getElementById("score-general").textContent = `${genScore} 分`;
  document.getElementById("bar-general").style.width = `${genScore}%`;

  // 渲染逐题复盘
  const reviewList = document.getElementById("review-list");
  reviewList.innerHTML = "";

  (state.currentStatus.records || []).forEach((rec, idx) => {
    const item = document.createElement("div");
    item.style.border = "1px solid #e2e8f0";
    item.style.borderRadius = "8px";
    item.style.padding = "10px 12px";
    item.style.background = "#f8fafc";

    item.innerHTML = `
      <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 4px;">
        <span style="font-weight: 600; color: #1e3a8a;">Q${idx + 1}. [${getCategoryName(rec.question.category)}] ${rec.question.subcategory}</span>
        <span style="font-weight: 700; color: ${rec.evaluation.score >= 60 ? '#059669' : '#dc2626'};">${rec.evaluation.score} 分</span>
      </div>
      <div style="font-size: 0.85rem; font-weight: 600; color: #334155; margin-bottom: 6px;">${rec.question.question}</div>
      <div style="font-size: 0.78rem; color: #64748b; margin-bottom: 4px;"><strong>你的回答：</strong>${escapeHtml(rec.user_answer)}</div>
      <div style="font-size: 0.78rem; color: #1e40af; background: #eff6ff; padding: 6px 8px; border-radius: 6px;"><strong>考官评语：</strong>${rec.evaluation.feedback}</div>
    `;
    reviewList.appendChild(item);
  });
}

function getCategoryName(cat) {
  switch (cat) {
    case "academic":
      return "专业问题";
    case "english":
      return "英语问题";
    case "general":
      return "综合素质";
    default:
      return "面试问题";
  }
}

function getCategoryClass(cat) {
  switch (cat) {
    case "academic":
      return "badge-academic";
    case "english":
      return "badge-english";
    case "general":
      return "badge-general";
    default:
      return "badge-academic";
  }
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
