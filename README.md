# 🎓 保研面试模拟系统 (Postgraduate Interview Simulator)

专为保研/考研复试设计的模拟面试系统。支持部署在个人电脑或云服务器上，通过**手机浏览器随时随地练习**，配备移动端触控交互、语音朗读（TTS）与语音输入转文字能力。

---

## ✨ 核心特性

1. **三模块精选题库**：
   - 📚 **专业问题 (Academic)**：覆盖操作系统、计算机网络、数据结构与算法、机器学习及本科科研项目深挖等。
   - 🗣️ **英语问题 (English)**：涵盖深造动机、学术英语与研究兴趣、挑战应对、日常爱好与抗压。
   - 🌟 **一般/综合问题 (General)**：涵盖择校择专业动机、科研心态、团队协作与分歧化解、自我认知与规划。
2. **自适应动态面试状态机**：
   - 自动检测考生**自我介绍开场语言**（中文 vs 英文）：
     - **中文开场**：动态规划为优先考察综合素质与专业技术问题，后续进入英语问答。
     - **英文开场**：动态规划为优先考察英语口语与学术交流，随后进入专业与综合素质考察。
3. **手机端体验优先**：
   - 移动端原生视口与触控优化，无需额外下载 App 或小程序。
   - 题目支持**一键语音朗读**（考官发音模拟）。
   - 答题区支持键盘输入与**麦克风实时语音转文字**。
   - 答题思考要点（Tips）按需折叠查看，作答后即时获得量化评分与专家改进建议。
   - 面试结束后自动输出全套能力评估报告与维度得分。

---

## 📁 目录架构

```text
PythonProject3/
├── app/
│   ├── config.py                # 基础配置 (端口、主机、抽题量等)
│   ├── main.py                  # FastAPI 后端服务与路由定义
│   ├── models/
│   │   └── schemas.py           # Pydantic 数据规范与面试阶段枚举
│   ├── core/
│   │   ├── language_detector.py # 中/英文自我介绍开端检测器
│   │   ├── interview_engine.py  # 面试流程推进与动态路线状态机
│   │   └── evaluator.py         # 答案踩分与智能点评模块
│   ├── data/
│   │   ├── question_bank.json   # 种子题库（专业/英语/一般）
│   │   └── repository.py        # 题库管理与抽题仓库
│   └── static/                  # 移动端 Web UI
│       ├── index.html           # 前端主页面
│       ├── css/style.css        # 手机端沉浸式样式
│       └── js/app.js            # 语音录入、TTS与状态推进
├── tests/                       # 自动化单元与集成测试
│   ├── test_language_detector.py# 语言识别准确性测试
│   ├── test_interview_engine.py # 状态机跳转与完整流程测试
│   └── test_api.py              # API 接口集成冒烟测试
├── main.py                      # 根目录快速启动脚本
├── requirements.txt             # 依赖清单
└── README.md                    # 本文档
```

---

## 🐳 Docker 一键部署（推荐在服务器上使用）

本项目已完全容器化，在服务器上无需配置 Python 环境，一行命令即可运行。

### 1. 启动容器

在服务器项目目录下运行：
```bash
# 使用 docker compose 启动并在后台运行
docker compose up -d --build
```
或者直接执行启动脚本：
```bash
chmod +x docker-start.sh docker-stop.sh
./docker-start.sh
```

### 2. 常用管理命令

```bash
# 查看容器实时运行日志
docker compose logs -f

# 停止容器服务
docker compose down

# 重启容器服务
docker compose restart
```

> [!TIP]
> **题库热更新**：`docker-compose.yml` 已配置将本地 `./app/data` 目录挂载进容器。你在服务器上直接修改或上传新的 `question_bank.json`，无需重启或重新构建 Docker 镜像即可实时生效！

---

## 🚀 原生 Python 启动 (本地调试)

### 1. 安装依赖

```bash
# 激活你的 Python 虚拟环境 (Python 3.10+)
pip install -r requirements.txt
```

### 2. 本地运行

在项目根目录下执行：
```bash
python main.py
```
或使用 Uvicorn 命令：
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后在浏览器打开：
- 电脑端：`http://127.0.0.1:8000`
- API 交互文档：`http://127.0.0.1:8000/docs`

---

## 📱 手机端随时随地练习使用说明

### 场景 A：在同一局域网（家庭 Wi-Fi 或热点）下使用手机访问

1. 确保电脑/服务器与手机连接在同一个 Wi-Fi 网络下。
2. 查看电脑局域网 IP（Windows 运行 `ipconfig`，Linux/Mac 运行 `ifconfig` 或 `ip a`），例如得到 `192.168.1.100`。
3. 运行 `python main.py`（默认已绑定 `0.0.0.0`，允许外部设备访问）。
4. 在手机浏览器（Safari / Chrome / 微信）中直接打开：
   ```text
   http://192.168.1.100:8000
   ```
5. *(可选)* 在手机浏览器中点击「分享」➔「添加到主屏幕」，即可像独立 App 一样随时点击练习！

### 场景 B：部署在云服务器（阿里云 / 腾讯云 / 华为云等 VPS）

1. 将本项目上传至云服务器：
   ```bash
   git clone <你的仓库>
   cd PythonProject3
   pip install -r requirements.txt
   ```
2. 后台常驻运行（以 Linux 系统的 systemd 或 nohup 为例）：
   ```bash
   nohup python main.py > server.log 2>&1 &
   ```
3. 在云服务器控制台的安全组规则中，放行 `8000` 端口的入方向访问。
4. 手机打开任何网络（移动4G/5G流量或任意Wi-Fi），访问：
   ```text
   http://<你的服务器公网IP>:8000
   ```

---

## 💡 如何自定义或扩充题库

题库位于 `app/data/question_bank.json`，格式极其直观：

```json
{
  "id": "acad_06",
  "category": "academic", // "academic" | "english" | "general"
  "subcategory": "计算机组成原理",
  "question": "什么是缓存一致性协议（如MESI）？它解决了什么问题？",
  "tips": ["多核CPU私有L1/L2 Cache", "共享内存数据不一致", "Modified/Exclusive/Shared/Invalid 状态转移"],
  "reference_answer": "MESI协议是一种广泛应用的硬件级缓存一致性协议...",
  "keywords": ["MESI", "多核", "状态", "总线嗅探", "脏数据"]
}
```
只需按照上述格式在 JSON 文件中追加你的目标专业（如金融、自动化、机械、生物等）题目即可实时生效！

---

## 🧪 运行自动化测试

```bash
pytest -v
```
包含 12 项覆盖语言识别、流程路由、接口契约和打分评估的自动化测试。
