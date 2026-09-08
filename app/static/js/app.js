/**
 * 保研面试模拟系统前端交互与沉浸式语音控制逻辑
 * 支持考官拟真原声超快语速提问、声波跳动、20分钟全场倒计时、30秒开口强制限时与自适应状态机推进
 */

const state = {
  sessionId: null,
  mode: "full",           // "full" (20分钟考场), "quick" (3题极速), "specialized" (单项专项)
  questionsPerStage: 2,   // 2 表示 20分钟高压实战(11题)，1 表示极速自测(3题)
  specializedCategory: "academic", // "academic", "english", "general"
  specializedCount: 5,    // 专项特训题数 (默认5题)
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
  isQuestionBlurred: true, // 听力盲测：题目默认虚化
  refAudio: null,          // 标答语音播放器 Audio 实例
  isPlayingRefAudio: false,
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

// ---------------- 自我介绍黄金三段式标准回答 ----------------
const GOLDEN_INTROS = {
  zh: `各位老师好！我叫刘子俊，来自湖北工业大学芯片产业学院微电子科学与工程专业。本科前三年，我学业扎实，综合绩点 GPA 为 3.69/5.0，专业排名前 14%（17/123），《CMOS集成电路设计》取得 97 分、《半导体物理》95 分，高分通过大学英语六级；同时，我参与了脉冲激光表面微纳刻蚀课题研究，具备扎实的微电子理论功底与严谨求实的科研素养。

我深信算法唯有扎根物理硅片才能释放极致算力。大学期间，我作为核心主力斩获了三项沉甸甸的国家级一等奖：在第十届集创赛中，我在异构 SoC 芯片上自主定制了目标检测硬件加速器与高速数据传输系统，以全国第一名的成绩斩获全国总决赛一等奖及企业大奖；在第八届嵌入式芯片大赛中，我基于高层次综合工具攻克了算子并行流水，并部署了二值化神经网络，再获全国一等奖；此外还在第二十八届中国机器人及人工智能大赛中摘得全国一等奖。这些经历全面锻造了我从底层硬件逻辑、内核驱动到系统机电闭环的全栈工程落地与抗压排错能力。

贵校在集成电路与电子信息领域实力雄厚。若能在此深造，我希望深耕领域专用芯片架构、异构计算与硬件安全，把本科积累的 SoC 与硬件加速实践经验融入导师课题，踏实攻关、多出成果，为芯片自立自强贡献力量。谢谢各位老师！`,

  en1: `Good morning, respected professors! My name is Liu Zijun, a senior undergraduate student majoring in Microelectronics Science and Engineering at Hubei University of Technology. Over the past three years, I have maintained a solid academic foundation with a GPA of 3.69 out of 5.0, ranking in the top 14% of my major, and passed CET-6 with fluent English technical literature reading and communication capabilities.

During college, I focused on FPGA and SoC design. As a core member, I won three National First Prizes. In the National Integrated Circuit Competition, our team built an FPGA hardware accelerator and won the Grand Award, ranking First Place nationwide. In addition, I developed HLS modules and edge AI systems, winning two more National First Prizes in embedded and robotics competitions. These projects gave me strong hands-on engineering skills.

Driven by these experiences, I am eager to pursue my master's degree at your esteemed university, focusing on domain-specific architectures, heterogeneous computing, and hardware security. I am fully prepared to dedicate my engineering skills and academic passion to cutting-edge research and make meaningful contributions to the semiconductor industry. Thank you very much for your time and consideration!`,

  en3: `Good morning, respected professors! Thank you very much for giving me this valuable opportunity. My name is Liu Zijun, a senior undergraduate majoring in Microelectronics Science and Engineering at the School of Chip Industry, Hubei University of Technology. Over the past three years, I have pursued academic excellence with great dedication, achieving a cumulative GPA of 3.69 out of 5.0 and ranking 17th out of 123 students, placing me in the top 14% of my major. I have established a robust microelectronics knowledge foundation, earning top scores in core courses such as 97 in CMOS Integrated Circuit Design, 98 in IC Design Practice, and 95 in Semiconductor Physics. In addition, I have passed CET-4 and CET-6, equipping me with fluent English technical literature reading and academic communication capabilities. Beyond coursework, my participation in the research project on pulsed laser micro-nano structuring and SEM characterization has instilled in me a rigorous scientific attitude and a deep respect for micro-physical laws.

I firmly believe that advanced algorithms must be coupled with physical silicon to unleash their ultimate efficiency. Translating this philosophy into practice, I have led and contributed to multiple high-level national competitions, winning three prestigious National First Prizes. In the 10th National Integrated Circuit Competition, our team won the National First Prize and the Enterprise Grand Award, ranking First Place nationwide. Addressing the severe latency bottleneck in edge defect detection, I implemented a custom RTL-level DFL hardware accelerator on an Intel Cyclone V SoC FPGA, utilizing fixed-point pipelining, an on-chip exponential lookup table, and Master DMA bursts to offload non-linear operations from the CPU, achieving sub-0.05-second latency and 99.7% mechanical sorting accuracy. In the 8th Embedded Chip and System Design Competition, I resolved loop-carried dependencies in SHA-256 and Cholesky decomposition within the AMD Vitis L1 library, reconstructing parallel pipelines on PYNQ-Z2 and deploying binarized neural networks to secure another National First Prize. Furthermore, I earned a third National First Prize in the 28th China Robot and Artificial Intelligence Competition by deploying robust edge vision on Raspberry Pi 5. These experiences have forged my full-stack engineering capability spanning RTL logic, kernel drivers, and electromechanical integration, as well as an unyielding resilience when debugging complex systems.

Your esteemed university is renowned for its distinguished academic heritage, top-tier research platforms, and pioneering contributions to integrated circuits. As Moore's Law slows down, domain-specific architectures, heterogeneous hardware-software co-design, and hardware security represent critical frontiers to overcome the memory wall and secure sensitive systems. If admitted to your university, I will dedicate my master's research to high-efficiency domain-specific acceleration architectures, heterogeneous computing, and hardware security chips. In my first year, I will solidify my theoretical foundations in advanced computer architectures and diligently track top-tier literature. In the following years, I will leverage my hands-on SoC and HLS expertise to tackle core research challenges under my advisor's guidance, aiming to publish high-impact papers, file patents, and validate physical prototypes. My ultimate goal is to grow into an innovative engineer equipped with both bottom-up device insights and top-down system architectural capabilities, contributing actively to China's semiconductor independence. Thank you very much for your time and consideration!`
};

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

  // 1. 实战模式与专项配置选择
  const specPanel = document.getElementById("specialized-panel");
  const btnStart = document.getElementById("btn-start-interview");

  function updateStartButtonUI() {
    if (!btnStart) return;
    if (state.mode === "specialized") {
      const catNameMap = {
        academic: "核心专业课",
        english: "英语日常口语",
        general: "综合素质抗压",
      };
      const catName = catNameMap[state.specializedCategory] || "专项";
      btnStart.textContent = `开始【${catName}】特训 · 随机 ${state.specializedCount} 题`;
      btnStart.style.background = "linear-gradient(135deg, #059669, #10b981)";
    } else if (state.mode === "quick") {
      btnStart.textContent = "进入考场 · 开启碎片3题自测";
      btnStart.style.background = "linear-gradient(135deg, #2563eb, #3b82f6)";
    } else {
      btnStart.textContent = "进入考场 · 开启20分钟高压实战";
      btnStart.style.background = "linear-gradient(135deg, #991b1b, #dc2626)";
    }
  }

  document.querySelectorAll(".mode-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".mode-btn").forEach((b) => {
        b.classList.remove("active");
        b.style.borderColor = "#cbd5e1";
        b.style.background = "#ffffff";
        b.style.color = "#475569";
        b.style.fontWeight = "normal";
      });
      btn.classList.add("active");
      state.mode = btn.getAttribute("data-mode");

      if (state.mode === "full") {
        btn.style.borderColor = "#dc2626";
        btn.style.background = "#fef2f2";
        btn.style.color = "#991b1b";
        btn.style.fontWeight = "700";
        state.questionsPerStage = 2;
        if (specPanel) specPanel.style.display = "none";
      } else if (state.mode === "quick") {
        btn.style.borderColor = "#2563eb";
        btn.style.background = "#eff6ff";
        btn.style.color = "#1d4ed8";
        btn.style.fontWeight = "700";
        state.questionsPerStage = 1;
        if (specPanel) specPanel.style.display = "none";
      } else if (state.mode === "specialized") {
        btn.style.borderColor = "#059669";
        btn.style.background = "#ecfdf5";
        btn.style.color = "#065f46";
        btn.style.fontWeight = "700";
        if (specPanel) specPanel.style.display = "block";
      }
      updateStartButtonUI();
    });
  });

  // 专项类别选择
  document.querySelectorAll(".spec-cat-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".spec-cat-btn").forEach((b) => {
        b.classList.remove("active");
        b.style.borderColor = "#cbd5e1";
        b.style.background = "#ffffff";
        b.style.color = "#475569";
        b.style.fontWeight = "normal";
      });
      btn.classList.add("active");
      btn.style.borderColor = "#2563eb";
      btn.style.background = "#eff6ff";
      btn.style.color = "#1d4ed8";
      btn.style.fontWeight = "700";
      state.specializedCategory = btn.getAttribute("data-cat");
      updateStartButtonUI();
    });
  });

  // 专项题数快捷按钮
  document.querySelectorAll(".spec-count-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".spec-count-btn").forEach((b) => {
        b.classList.remove("active");
        b.style.borderColor = "#cbd5e1";
        b.style.background = "#ffffff";
        b.style.color = "#475569";
        b.style.fontWeight = "normal";
      });
      btn.classList.add("active");
      btn.style.borderColor = "#2563eb";
      btn.style.background = "#eff6ff";
      btn.style.color = "#1d4ed8";
      btn.style.fontWeight = "700";
      state.specializedCount = parseInt(btn.getAttribute("data-count"), 10);
      const customInput = document.getElementById("spec-custom-count");
      if (customInput) customInput.value = "";
      updateStartButtonUI();
    });
  });

  // 专项题数自定义输入
  const customCountInput = document.getElementById("spec-custom-count");
  if (customCountInput) {
    customCountInput.addEventListener("input", () => {
      const val = parseInt(customCountInput.value, 10);
      if (val && val >= 1 && val <= 50) {
        document.querySelectorAll(".spec-count-btn").forEach((b) => {
          b.classList.remove("active");
          b.style.borderColor = "#cbd5e1";
          b.style.background = "#ffffff";
          b.style.color = "#475569";
          b.style.fontWeight = "normal";
        });
        state.specializedCount = val;
        updateStartButtonUI();
      }
    });
  }

  // 2. 开始面试
  document.getElementById("btn-start-interview").addEventListener("click", startInterview);

  // 3. 预设自我介绍文案 (刘子俊背景定制黄金三段式)
  const introTextarea = document.getElementById("intro-textarea");
  document.getElementById("btn-preset-zh")?.addEventListener("click", () => {
    introTextarea.value = GOLDEN_INTROS.zh;
    updateCharCount(introTextarea, "intro-char-count");
  });

  document.getElementById("btn-preset-en")?.addEventListener("click", () => {
    introTextarea.value = GOLDEN_INTROS.en1;
    updateCharCount(introTextarea, "intro-char-count");
  });

  document.getElementById("btn-preset-en-deep")?.addEventListener("click", () => {
    introTextarea.value = GOLDEN_INTROS.en3;
    updateCharCount(introTextarea, "intro-char-count");
  });

  // 3.1 自我介绍高分标答折叠抽屉与选项卡
  let currentIntroRefTab = "zh";
  const introRefDisplay = document.getElementById("intro-ref-text-display");
  if (introRefDisplay) {
    introRefDisplay.textContent = GOLDEN_INTROS.zh;
  }

  function setIntroRefTab(tab) {
    currentIntroRefTab = tab;
    stopRefAudio();
    const tabConfigs = [
      { id: "btn-intro-tab-zh", key: "zh" },
      { id: "btn-intro-tab-en1", key: "en1" },
      { id: "btn-intro-tab-en3", key: "en3" },
    ];
    tabConfigs.forEach(({ id, key }) => {
      const b = document.getElementById(id);
      if (!b) return;
      if (key === tab) {
        b.style.background = "#eff6ff";
        b.style.borderColor = "#2563eb";
        b.style.color = "#1d4ed8";
        b.style.fontWeight = "700";
      } else {
        b.style.background = "#ffffff";
        b.style.borderColor = "#cbd5e1";
        b.style.color = "#475569";
        b.style.fontWeight = "normal";
      }
    });
    if (introRefDisplay) {
      introRefDisplay.textContent = GOLDEN_INTROS[tab] || "";
    }
  }

  document.getElementById("btn-intro-tab-zh")?.addEventListener("click", () => setIntroRefTab("zh"));
  document.getElementById("btn-intro-tab-en1")?.addEventListener("click", () => setIntroRefTab("en1"));
  document.getElementById("btn-intro-tab-en3")?.addEventListener("click", () => setIntroRefTab("en3"));

  const introRefToggle = document.getElementById("intro-ref-toggle");
  const introRefBody = document.getElementById("intro-ref-body");
  const introRefArrow = document.getElementById("intro-ref-arrow");
  if (introRefToggle && introRefBody) {
    introRefToggle.addEventListener("click", () => {
      const isHidden = introRefBody.style.display === "none";
      introRefBody.style.display = isHidden ? "block" : "none";
      if (introRefArrow) introRefArrow.textContent = isHidden ? "▲" : "▼";
      if (isHidden && introRefDisplay && !introRefDisplay.textContent) {
        setIntroRefTab("zh");
      }
    });
  }

  document.getElementById("btn-use-current-ref")?.addEventListener("click", () => {
    introTextarea.value = GOLDEN_INTROS[currentIntroRefTab] || "";
    updateCharCount(introTextarea, "intro-char-count");
  });

  document.getElementById("btn-tts-intro-ref")?.addEventListener("click", () => {
    toggleIntroRefAudio(currentIntroRefTab);
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

  // 8.1 题目虚化隐藏与听力盲测切换
  const btnToggleBlur = document.getElementById("btn-toggle-blur");
  const blurHint = document.getElementById("question-blur-hint");
  if (btnToggleBlur) {
    btnToggleBlur.addEventListener("click", () => {
      setQuestionBlur(!state.isQuestionBlurred);
    });
  }
  if (blurHint) {
    blurHint.addEventListener("click", () => {
      setQuestionBlur(false);
    });
  }

  // 8.2 “我不会 · 查看标答”
  const btnGiveUp = document.getElementById("btn-give-up");
  if (btnGiveUp) {
    btnGiveUp.addEventListener("click", giveUpAndShowAnswer);
  }

  // 8.3 弹窗标准回答 AI 朗读 / 跟读纠音
  const btnTtsModalRef = document.getElementById("btn-tts-modal-ref");
  if (btnTtsModalRef) {
    btnTtsModalRef.addEventListener("click", toggleModalRefAudio);
  }

  // 9. 提交回答
  document.getElementById("btn-submit-answer").addEventListener("click", submitAnswer);

  // 10. 模态框下一题
  document.getElementById("btn-next-question").addEventListener("click", () => {
    stopRefAudio();
    modalFeedback.style.display = "none";
    renderCurrentState();
  });

  // 11. 重新开始
  document.getElementById("btn-restart").addEventListener("click", () => {
    stopRecording();
    stopVoice();
    stopRefAudio();
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
    let url = "";
    if (state.mode === "specialized") {
      url = `/api/interview/start?mode=specialized&category=${state.specializedCategory}&count=${state.specializedCount}`;
    } else if (state.mode === "quick") {
      url = `/api/interview/start?mode=quick&questions_per_stage=1`;
    } else {
      url = `/api/interview/start?mode=full&questions_per_stage=${state.questionsPerStage}`;
    }

    const res = await fetch(url, { method: "POST" });
    if (!res.ok) throw new Error("启动考场失败");
    const data = await res.json();
    state.sessionId = data.session_id;
    state.currentStatus = data;

    if (state.mode === "specialized") {
      // 专项练习：免去冗长自我介绍，直接进入第一题提问！
      stopExamTimer();
      examTimerBar.style.display = "none";
      renderCurrentState();
    } else {
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
    }
  } catch (err) {
    alert("连接考场服务失败: " + err.message);
  } finally {
    btn.disabled = false;
    if (typeof updateStartButtonUI === "function") {
      updateStartButtonUI();
    }
  }
}

async function submitIntro() {
  stopRecording();
  stopVoice();
  stopRefAudio();

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

function setQuestionBlur(isBlurred) {
  state.isQuestionBlurred = isBlurred;
  const qText = document.getElementById("question-text");
  const hint = document.getElementById("question-blur-hint");
  const btn = document.getElementById("btn-toggle-blur");
  if (!qText || !hint || !btn) return;

  if (isBlurred) {
    qText.classList.add("blurred");
    hint.style.display = "flex";
    btn.textContent = "👁️ 取消隐藏 (听力盲测)";
    btn.style.background = "#f1f5f9";
    btn.style.borderColor = "#cbd5e1";
    btn.style.color = "#475569";
  } else {
    qText.classList.remove("blurred");
    hint.style.display = "none";
    btn.textContent = "🙈 隐藏题目 (恢复盲听)";
    btn.style.background = "#eff6ff";
    btn.style.borderColor = "#93c5fd";
    btn.style.color = "#1d4ed8";
  }
}

async function giveUpAndShowAnswer() {
  stopRecording();
  stopVoice();
  stopRefAudio();
  stopResponseDeadline();

  const curQ = state.currentStatus?.current_question;
  if (!curQ) return;

  const btnGiveUp = document.getElementById("btn-give-up");
  if (btnGiveUp) {
    btnGiveUp.disabled = true;
    btnGiveUp.textContent = "正在调取权威标答...";
  }

  try {
    const res = await fetch(`/api/interview/${state.sessionId}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question_id: curQ.id,
        answer_text: "我不会，请教老师指点。",
      }),
    });

    if (!res.ok) throw new Error("调取标答失败");
    const result = await res.json();
    state.currentStatus = result.status;

    // 清空回答输入框
    document.getElementById("answer-textarea").value = "";
    updateCharCount(document.getElementById("answer-textarea"), "answer-char-count");

    // 弹出即时反馈 Bottom Sheet（展示权威标答并支持 AI 朗读纠音）
    showFeedbackModal(result.evaluation, curQ);
  } catch (err) {
    alert("调取标答失败: " + err.message);
  } finally {
    if (btnGiveUp) {
      btnGiveUp.disabled = false;
      btnGiveUp.textContent = "🤷 我不会 · 查看标答";
    }
  }
}

function stopRefAudio() {
  if (state.refAudio) {
    state.refAudio.pause();
    state.refAudio = null;
  }
  state.isPlayingRefAudio = false;

  // 1. 重置反馈弹窗朗读按钮
  const icon = document.getElementById("tts-modal-ref-icon");
  const label = document.getElementById("tts-modal-ref-label");
  const status = document.getElementById("modal-tts-ref-status");
  const btn = document.getElementById("btn-tts-modal-ref");
  if (icon) icon.textContent = "🔊";
  if (label) label.textContent = "AI 朗读标答 · 纠音跟读";
  if (status) status.style.display = "none";
  if (btn) {
    btn.style.background = "#eff6ff";
    btn.style.borderColor = "#93c5fd";
    btn.style.color = "#1d4ed8";
  }

  // 2. 重置自我介绍标答朗读按钮
  const introIcon = document.getElementById("tts-intro-ref-icon");
  const introLabel = document.getElementById("tts-intro-ref-label");
  const introBtn = document.getElementById("btn-tts-intro-ref");
  if (introIcon) introIcon.textContent = "🔊";
  if (introLabel) introLabel.textContent = "AI 朗读此标答";
  if (introBtn) {
    introBtn.style.background = "#eff6ff";
    introBtn.style.borderColor = "#93c5fd";
    introBtn.style.color = "#1d4ed8";
  }
}

function toggleIntroRefAudio(tab) {
  if (state.isPlayingRefAudio) {
    stopRefAudio();
    return;
  }

  stopVoice();
  stopRefAudio();

  const text = GOLDEN_INTROS[tab] || GOLDEN_INTROS.zh;
  if (!text) return;

  const icon = document.getElementById("tts-intro-ref-icon");
  const label = document.getElementById("tts-intro-ref-label");
  const btn = document.getElementById("btn-tts-intro-ref");

  state.isPlayingRefAudio = true;
  if (icon) icon.textContent = "⏹️";
  if (label) label.textContent = "停止朗读";
  if (btn) {
    btn.style.background = "#fee2e2";
    btn.style.borderColor = "#fca5a5";
    btn.style.color = "#b91c1c";
  }

  const cleanText = text.substring(0, 500);
  const audioUrl = `/api/audio/tts?text=${encodeURIComponent(cleanText)}&rate=%2B0%25`;
  const audio = new Audio(audioUrl);
  state.refAudio = audio;

  audio.onended = () => {
    stopRefAudio();
  };

  audio.onerror = () => {
    console.warn("自我介绍标答音频加载失败，尝试降级本地合成");
    stopRefAudio();
    if ("speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(cleanText);
      const isEn = /[a-zA-Z]{5,}/.test(cleanText);
      utterance.lang = isEn ? "en-US" : "zh-CN";
      utterance.rate = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  };

  audio.play().catch((err) => {
    console.warn("音频播放受限:", err);
    stopRefAudio();
  });
}

function toggleModalRefAudio() {
  if (state.isPlayingRefAudio) {
    stopRefAudio();
    return;
  }

  stopVoice();
  stopRefAudio();

  const refText = document.getElementById("modal-reference-answer")?.textContent?.trim();
  if (!refText || refText.startsWith("（本题注重")) return;

  // 清洗掉示范提示词，截取合理长度用于 TTS 播放
  let cleanText = refText.replace(/^[🗣️\s]*考场标准口语化作答示范[：:\s]*/, "").trim();
  if (cleanText.length > 500) {
    cleanText = cleanText.substring(0, 500);
  }

  const icon = document.getElementById("tts-modal-ref-icon");
  const label = document.getElementById("tts-modal-ref-label");
  const status = document.getElementById("modal-tts-ref-status");
  const btn = document.getElementById("btn-tts-modal-ref");

  state.isPlayingRefAudio = true;
  if (icon) icon.textContent = "⏹️";
  if (label) label.textContent = "停止朗读";
  if (status) status.style.display = "flex";
  if (btn) {
    btn.style.background = "#fee2e2";
    btn.style.borderColor = "#fca5a5";
    btn.style.color = "#b91c1c";
  }

  // 标答朗读采用正常自然原速（rate=+0%），帮助考生听清发音细节并跟读
  const audioUrl = `/api/audio/tts?text=${encodeURIComponent(cleanText)}&rate=%2B0%25`;
  const audio = new Audio(audioUrl);
  state.refAudio = audio;

  audio.onended = () => {
    stopRefAudio();
  };

  audio.onerror = () => {
    console.warn("标答音频加载失败，尝试降级本地合成");
    stopRefAudio();
    if ("speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(cleanText);
      const isEn = /[a-zA-Z]{5,}/.test(cleanText);
      utterance.lang = isEn ? "en-US" : "zh-CN";
      utterance.rate = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  };

  audio.play().catch((err) => {
    console.warn("音频播放受限:", err);
    stopRefAudio();
  });
}

function playSingleRefAudio(text) {
  if (!text) return;
  stopVoice();
  stopRefAudio();
  const cleanText = text.replace(/^[🗣️\s]*考场标准口语化作答示范[：:\s]*/, "").trim().substring(0, 500);
  const audioUrl = `/api/audio/tts?text=${encodeURIComponent(cleanText)}&rate=%2B0%25`;
  const audio = new Audio(audioUrl);
  state.refAudio = audio;
  audio.play().catch(console.warn);
}

function showFeedbackModal(evaluation, question) {
  stopRefAudio();
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

  // 0. 听力训练盲测：每道题目默认开启高斯模糊遮罩！
  setQuestionBlur(true);

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
  const progressPercent = Math.round((status.current_question_index / Math.max(status.total_questions, 1)) * 100);
  let stageLabel = status.stage_name_cn;
  if (state.mode === "specialized" || status.mode === "specialized") {
    stageLabel = `专项特训 (${status.current_question_index}/${status.total_questions})`;
  }
  updateProgress(progressPercent, stageLabel);

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
  const isSpecialized = state.mode === "specialized" || state.currentStatus?.mode === "specialized";
  updateProgress(100, isSpecialized ? "专项复盘评估报告" : "面试终审报告");
  stopVoice();
  stopRefAudio();
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

    const refAnswerEscaped = escapeHtml(rec.question.reference_answer || "（本题注重思维阐述与逻辑完整性）");
    const rawRefJson = JSON.stringify(rec.question.reference_answer || "");

    item.innerHTML = `
      <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 4px;">
        <span style="font-weight: 600; color: #1e3a8a;">Q${idx + 1}. [${getCategoryName(rec.question.category)}] ${rec.question.subcategory}</span>
        <span style="font-weight: 700; color: ${rec.evaluation.score >= 60 ? '#059669' : '#dc2626'};">${rec.evaluation.score} 分</span>
      </div>
      <div style="font-size: 0.85rem; font-weight: 600; color: #334155; margin-bottom: 6px;">${rec.question.question}</div>
      <div style="font-size: 0.78rem; color: #64748b; margin-bottom: 4px;"><strong>你的回答：</strong>${escapeHtml(rec.user_answer)}</div>
      <div style="font-size: 0.78rem; color: #1e40af; background: #eff6ff; padding: 6px 8px; border-radius: 6px; margin-bottom: 6px;"><strong>考官评语：</strong>${rec.evaluation.feedback}</div>
      <div style="font-size: 0.78rem; color: #15803d; background: #f0fdf4; border: 1px solid #bbf7d0; padding: 6px 8px; border-radius: 6px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
          <strong>🎯 标准参考回答：</strong>
          <button type="button" class="ref-tts-btn-small" onclick='playSingleRefAudio(${rawRefJson})'>
            <span>🔊 听标答朗读</span>
          </button>
        </div>
        <div style="white-space: pre-wrap; line-height: 1.5;">${refAnswerEscaped}</div>
      </div>
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

window.playSingleRefAudio = playSingleRefAudio;
