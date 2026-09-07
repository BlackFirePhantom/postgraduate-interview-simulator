# -*- coding: utf-8 -*-
"""
智能解析并导入用户桌面《推免材料/面试问题准备》中的全部专业题、英语题、一般问题到题库 JSON
"""
import os
import re
import json
import glob
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(r"C:\Users\blackfire\Desktop\推免材料\面试问题准备")
OUTPUT_JSON = Path(r"c:\Users\blackfire\Documents\PythonProject3\app\data\question_bank.json")


def read_docx_paragraphs(file_path):
    """从 docx 中提取段落列表"""
    try:
        with zipfile.ZipFile(file_path) as z:
            tree = ET.fromstring(z.read("word/document.xml"))
            paras = []
            for p in tree.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                text = "".join(node.text for node in p.iter() if node.text)
                if text.strip():
                    paras.append(text.strip())
            return paras
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []


def clean_question_title(text):
    """清洗题目字符串，去掉 Q01、星号、标签等，使其适合考官发音"""
    t = re.sub(r'^[#\s]*Q\d+[\.、\s]*', '', text)
    t = re.sub(r'【.*?】', '', t)
    t = re.sub(r'\(.*?\)$', '', t)
    t = t.strip()
    return t


def extract_keywords_heuristic(text, count=6):
    """粗提取关键词作为踩分点"""
    en_terms = re.findall(r'[a-zA-Z]{3,}(?:[-_][a-zA-Z0-9]+)?', text)
    zh_terms = re.findall(r'[\u4e00-\u9fff]{2,6}', text)
    
    stop_words = {"可以", "通过", "进行", "以及", "我们", "主要", "对于", "这个", "并且", "由于", "同时", "根据", "如果", "因此", "为了", "因为", "从而", "一个", "两个", "不同", "要求", "能够"}
    zh_filtered = [w for w in zh_terms if w not in stop_words and len(w) >= 2]
    
    combined = list(dict.fromkeys(en_terms[:3] + zh_filtered[:8]))
    return combined[:count] if combined else ["核心原理", "工程实现", "关键技术"]


def parse_markdown_60_questions():
    """解析《湖南大学_电子信息_保研面试60问精解.md》"""
    md_file = BASE_DIR / "湖南大学_电子信息_保研面试60问精解.md"
    if not md_file.exists():
        return []

    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r'\n##\s+(Q\d+[\.、\s].*?)\n', content)
    questions = []

    for i in range(1, len(blocks), 2):
        header = blocks[i].strip()
        body = blocks[i+1].strip() if i+1 < len(blocks) else ""

        q_num_match = re.search(r'Q(\d+)', header)
        q_num = int(q_num_match.group(1)) if q_num_match else (i // 2 + 1)
        qid = f"hnu_q{q_num:02d}"

        subcat = "电子信息综合专业课"
        if q_num in [1, 2, 3, 8, 16, 19, 20, 25, 26, 30, 39, 45, 49, 57]:
            subcat = "通信原理与信号处理"
        elif q_num in [4, 14, 21, 31, 37, 46, 55]:
            subcat = "模拟电子技术与电路分析"
        elif q_num in [5, 7, 13, 17, 29, 32, 36, 40, 50, 54, 58]:
            subcat = "数字电路与微电子芯片"
        elif q_num in [6, 9, 10, 18, 27, 28, 33, 41, 42, 51, 59]:
            subcat = "计算机系统结构与操作系统"
        elif q_num in [11, 12, 15, 22, 23, 24, 34, 35, 38, 43, 44, 47, 48, 52, 53, 56, 60]:
            subcat = "人工智能与智能系统"

        clean_q = clean_question_title(header)

        tips = []
        intent_match = re.search(r'🎯\s*命题意图与核心考点[：:](.*?)(?:\n|$)', body)
        if intent_match:
            raw_intent = intent_match.group(1).strip()
            tips = [t.strip() for t in re.split(r'[,，、；;]', raw_intent) if t.strip()]
        if not tips:
            tips = ["逻辑严谨清晰", "切中核心物理/工程本质", "结合具体实践案例阐述"]

        ans_match = re.search(r'###\s*🎙️\s*考场高分口头作答示范.*?\n(.*?)(?:###\s*💡|$)', body, re.DOTALL)
        ref_ans = ""
        if ans_match:
            raw_ans = ans_match.group(1).strip()
            raw_ans = re.sub(r'[*#>`]', '', raw_ans)
            ref_ans = re.sub(r'\s+', ' ', raw_ans)[:350]
        else:
            ref_ans = "建议从物理本质、数学推导、工程实际应用三个维度层层展开。"

        keywords = extract_keywords_heuristic(clean_q + " " + ref_ans)

        questions.append({
            "id": qid,
            "category": "academic",
            "subcategory": subcat,
            "question": clean_q,
            "tips": tips[:4],
            "reference_answer": ref_ans,
            "keywords": keywords
        })

    return questions


def parse_docx_general_questions():
    """解析《一般问题/01_推免综合素质与导师常见面试问答.docx》"""
    doc_path = BASE_DIR / "一般问题" / "01_推免综合素质与导师常见面试问答.docx"
    questions = []
    if doc_path.exists():
        paras = read_docx_paragraphs(doc_path)
        current_q = None
        current_tips = []
        current_ans = []

        for p in paras:
            q_match = re.match(r'^(Q\d+[\.、\s].*)', p)
            if q_match:
                if current_q:
                    clean_q = clean_question_title(current_q)
                    questions.append({
                        "id": f"gen_{len(questions)+1:02d}",
                        "category": "general",
                        "subcategory": "推免综合素质与导师问答",
                        "question": clean_q,
                        "tips": current_tips if current_tips else ["真诚自信", "条理清晰", "展现自驱力与科研潜力"],
                        "reference_answer": " ".join(current_ans)[:350],
                        "keywords": extract_keywords_heuristic(clean_q + " " + " ".join(current_ans))
                    })
                current_q = q_match.group(1)
                current_tips = []
                current_ans = []
            elif "🎯" in p or "💡" in p:
                parts = re.split(r'[🎯💡]', p)
                for part in parts:
                    clean_p = part.strip()
                    if clean_p:
                        current_tips.append(clean_p[:80])
            elif current_q and not p.startswith("【") and not p.startswith("―"):
                current_ans.append(p)

        if current_q:
            clean_q = clean_question_title(current_q)
            questions.append({
                "id": f"gen_{len(questions)+1:02d}",
                "category": "general",
                "subcategory": "推免综合素质与导师问答",
                "question": clean_q,
                "tips": current_tips if current_tips else ["真诚自信", "条理清晰"],
                "reference_answer": " ".join(current_ans)[:350],
                "keywords": extract_keywords_heuristic(clean_q + " " + " ".join(current_ans))
            })

    # 补充高频保研通用考查
    supplementary_general = [
        {
            "id": "gen_supp_01",
            "category": "general",
            "subcategory": "读研规划与学术定位",
            "question": "如果进入课题组后，导师分配的研究方向与你的预想差距较大，或者实验连续数月毫无正向进展，你如何面对？",
            "tips": ["科研探索的挫折是常态", "主动向导师与师兄沟通汇报", "深入挖掘课题背后的工业与学术价值"],
            "reference_answer": "首先端正心态，科研本身就是试错与攻坚的过程。面对非第一意愿方向，我会广泛精读顶级文献挖掘其学术与产业价值；遇到瓶颈时主动复盘实验参数并定期向导师汇报探讨，脚踏实地将基础做到极致。",
            "keywords": ["端正心态", "试错", "主动沟通", "文献调研", "攻坚克难"]
        },
        {
            "id": "gen_supp_02",
            "category": "general",
            "subcategory": "团队协作与分歧化解",
            "question": "在本科科研团队或重大竞赛攻坚中，组内成员产生严重技术分歧或进度严重滞后时，你通常如何化解并推进交付？",
            "tips": ["对事不对人", "用实验数据与原型测试说话", "重新梳理里程碑协同分担"],
            "reference_answer": "坚持‘对事不对人’。如果是技术路线分歧，提倡搭建最小原型或跑仿真对比数据，用客观事实说话；如果是进度滞后，重新梳理关键里程碑，摸排困难并协助攻坚，保障团队凝聚力与项目按时交付。",
            "keywords": ["对事不对人", "数据说话", "里程碑", "团队凝聚力", "原型验证"]
        },
        {
            "id": "gen_supp_03",
            "category": "general",
            "subcategory": "自我认知与扬长补短",
            "question": "请客观评价你的核心工程优势与相对学术短板，在硕士阶段你将如何扬长补短？",
            "tips": ["优势结合具体成果（如竞赛与工程落地）", "短板坦诚（学术顶会论文规范）", "给出落地的精进计划"],
            "reference_answer": "我的优势在于极强的硬件落地执行力和软硬件调试攻坚能力；相对短板在于国际顶会规范学术写作与高阶数学推导经验尚浅。我计划在研一期间深度精读高水平文献，主动参与组会研讨，扎实提升科研严谨度与学术论文水平。",
            "keywords": ["工程落地", "执行力", "文献精读", "学术论文", "扬长补短"]
        }
    ]
    questions.extend(supplementary_general)
    return questions


def parse_docx_english_questions():
    """解析《英语口语/01_推免英语口语面试与专业问答全攻略.docx》并扩充专业英语"""
    doc_path = BASE_DIR / "英语口语" / "01_推免英语口语面试与专业问答全攻略.docx"
    questions = []
    if doc_path.exists():
        paras = read_docx_paragraphs(doc_path)
        current_q = None
        current_tips = []
        current_ans = []

        for p in paras:
            q_match = re.match(r'^(Q\d+[\.、\s].*)', p)
            if q_match:
                if current_q:
                    clean_q = clean_question_title(current_q)
                    questions.append({
                        "id": f"eng_doc_{len(questions)+1:02d}",
                        "category": "english",
                        "subcategory": "English Spoken & Academic",
                        "question": clean_q,
                        "tips": current_tips if current_tips else ["Speak fluently", "Accurate terms", "Clear structure"],
                        "reference_answer": " ".join(current_ans)[:350],
                        "keywords": extract_keywords_heuristic(clean_q + " " + " ".join(current_ans))
                    })
                current_q = q_match.group(1)
                current_tips = []
                current_ans = []
            elif "🎯" in p or "💡" in p:
                parts = re.split(r'[🎯💡]', p)
                for part in parts:
                    clean_p = part.strip()
                    if clean_p:
                        current_tips.append(clean_p[:80])
            elif current_q and not p.startswith("【") and not p.startswith("―"):
                current_ans.append(p)

        if current_q:
            clean_q = clean_question_title(current_q)
            questions.append({
                "id": f"eng_doc_{len(questions)+1:02d}",
                "category": "english",
                "subcategory": "English Spoken & Academic",
                "question": clean_q,
                "tips": current_tips if current_tips else ["Fluent expression", "Clear structure"],
                "reference_answer": " ".join(current_ans)[:350],
                "keywords": extract_keywords_heuristic(clean_q + " " + " ".join(current_ans))
            })

    # 补充专业英语与学术表达题单
    supp_english = [
        {
            "id": "eng_supp_01",
            "category": "english",
            "subcategory": "Academic Motivation & Research",
            "question": "Could you please explain why you decided to pursue a master's degree instead of directly finding a job in industry?",
            "tips": ["Express passion for in-depth research", "Bridge gap between course foundations and cutting-edge silicon architecture", "Long-term vision"],
            "reference_answer": "During my undergraduate study, I realized that while coursework provided broad foundational knowledge, solving cutting-edge chip design and hardware bottlenecks requires deep theoretical understanding. Pursuing a master's degree will allow me to immerse myself in advanced research and prepare for a high-level engineering and academic career.",
            "keywords": ["postgraduate", "undergraduate", "research", "theoretical", "in-depth", "career"]
        },
        {
            "id": "eng_supp_02",
            "category": "english",
            "subcategory": "Research Interest",
            "question": "What specific research direction in integrated circuits and electronic engineering interests you the most, and why?",
            "tips": ["Mention specific areas (e.g., FPGA hardware accelerator, SoC design, analog CMOS, PUF security)", "Connect with undergraduate experience"],
            "reference_answer": "I am deeply interested in domain-specific hardware accelerators and energy-efficient SoC architecture. In my undergraduate competition, our team customized an FPGA regression accelerator, which showed me the immense power of hardware-software co-design in breaking memory walls and compute bottlenecks.",
            "keywords": ["hardware accelerator", "SoC", "FPGA", "co-design", "energy-efficient"]
        },
        {
            "id": "eng_supp_03",
            "category": "english",
            "subcategory": "Technical English",
            "question": "Could you explain the difference between FPGA and ASIC in English, especially regarding cost, performance, and development turnaround?",
            "tips": ["NRE cost vs unit cost", "Reconfigurability and flexibility", "Clock speed, area, and power consumption"],
            "reference_answer": "FPGA offers reconfigurability, zero NRE cost, and rapid development turnaround, making it ideal for prototyping and low-to-medium volume deployment. In contrast, ASIC requires high NRE costs and long tapeout cycles, but delivers superior performance, minimal silicon area, and the lowest power consumption at massive volumes.",
            "keywords": ["FPGA", "ASIC", "reconfigurability", "NRE", "prototyping", "turnaround", "power consumption"]
        },
        {
            "id": "eng_supp_04",
            "category": "english",
            "subcategory": "Academic English",
            "question": "Can you introduce one of your major undergraduate projects or competitions in English, highlighting your personal contribution?",
            "tips": ["STAR framework: Situation, Task, Action, Result", "Specific module you designed", "Quantifiable metrics"],
            "reference_answer": "In the National Integrated Circuit Innovation Competition, my team designed a customized FPGA hardware accelerator on an Intel Cyclone V SoC. I was responsible for RTL implementation of the batch DMA controller and hardware regression pipeline, improving end-to-end detection throughput by 3.2 times.",
            "keywords": ["STAR", "Intel Cyclone", "RTL", "throughput", "DMA", "hardware accelerator"]
        },
        {
            "id": "eng_supp_05",
            "category": "english",
            "subcategory": "Problem Solving & Stress",
            "question": "How do you handle severe academic stress or debugging obstacles during long-term research?",
            "tips": ["Systematic debugging methodology", "Healthy sports or hobbies to refresh mind", "Communication with advisors"],
            "reference_answer": "When facing difficult debugging bottlenecks, I first step back and break down the problem methodically using waveforms and isolation tests. Outside the lab, I relieve stress through running and playing badminton, which helps me clear my mind and return with fresh perspectives.",
            "keywords": ["debugging", "methodical", "stress", "isolation test", "running", "resilience"]
        },
        {
            "id": "eng_supp_06",
            "category": "english",
            "subcategory": "Future Plan",
            "question": "What is your academic and career plan for your three years of master's study?",
            "tips": ["Year 1: coursework and paper reading", "Year 2: project and tapeout / publication", "Year 3: thesis and career choice"],
            "reference_answer": "In the first year, I plan to solidify advanced coursework and read top conference literature in our field. In the second year, I will focus on research projects, striving for chip tapeout and high-quality conference publication. In the third year, I aim to complete my master's dissertation with high academic standards.",
            "keywords": ["coursework", "literature", "tapeout", "conference", "dissertation"]
        }
    ]
    questions.extend(supp_english)
    return questions


def parse_academic_docx_files():
    """解析《专业问题/》目录下的 11 份深度专业追问 docx 文件"""
    docx_files = glob.glob(str(BASE_DIR / "专业问题" / "*.docx"))
    all_questions = []

    for doc_path in docx_files:
        filename = os.path.basename(doc_path)
        subcat = re.sub(r'^\d+_', '', filename)
        subcat = re.sub(r'(_面试连环追问题解|_高频面试问答|_专项问答)\.docx$', '', subcat)

        paras = read_docx_paragraphs(doc_path)
        current_q = None
        current_tips = []
        current_ans = []

        for p in paras:
            q_match = re.match(r'^(Q\d+[\.、\s].*)', p)
            if q_match:
                if current_q:
                    clean_q = clean_question_title(current_q)
                    if len(clean_q) >= 6:
                        all_questions.append({
                            "id": f"acad_deep_{len(all_questions)+1:03d}",
                            "category": "academic",
                            "subcategory": subcat,
                            "question": clean_q,
                            "tips": current_tips if current_tips else ["抓住物理图像与数学推导", "结合半导体/电路具体场景", "直击核心要点"],
                            "reference_answer": " ".join(current_ans)[:350],
                            "keywords": extract_keywords_heuristic(clean_q + " " + " ".join(current_ans))
                        })
                current_q = q_match.group(1)
                current_tips = []
                current_ans = []
            elif "🎯" in p or "💡" in p:
                parts = re.split(r'[🎯💡]', p)
                for part in parts:
                    clean_p = part.strip()
                    if clean_p:
                        current_tips.append(clean_p[:80])
            elif current_q and not p.startswith("【") and not p.startswith("―"):
                current_ans.append(p)

        if current_q:
            clean_q = clean_question_title(current_q)
            if len(clean_q) >= 6:
                all_questions.append({
                    "id": f"acad_deep_{len(all_questions)+1:03d}",
                    "category": "academic",
                    "subcategory": subcat,
                    "question": clean_q,
                    "tips": current_tips if current_tips else ["抓住物理图像", "直击核心要点"],
                    "reference_answer": " ".join(current_ans)[:350],
                    "keywords": extract_keywords_heuristic(clean_q + " " + " ".join(current_ans))
                })

    return all_questions


def main():
    print("Parsing user materials...")
    q_md = parse_markdown_60_questions()
    q_gen = parse_docx_general_questions()
    q_eng = parse_docx_english_questions()
    q_acad = parse_academic_docx_files()

    total_pool = q_md + q_gen + q_eng + q_acad
    print(f"Parsed total questions: {len(total_pool)}")
    
    acad_cnt = sum(1 for q in total_pool if q["category"] == "academic")
    eng_cnt = sum(1 for q in total_pool if q["category"] == "english")
    gen_cnt = sum(1 for q in total_pool if q["category"] == "general")
    print(f"  - Academic: {acad_cnt}")
    print(f"  - English: {eng_cnt}")
    print(f"  - General: {gen_cnt}")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(total_pool, f, ensure_ascii=False, indent=2)

    print(f"Successfully saved to: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
