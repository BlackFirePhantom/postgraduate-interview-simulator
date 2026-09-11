# -*- coding: utf-8 -*-
"""
从 C:\\Users\\blackfire\\Desktop\\推免材料\\面试问题准备
全量提取最新题目、标准答案、极速速记、思考要点与工程亮点
"""
import re
import json
from pathlib import Path

SOURCE_DIR = Path(r"C:\Users\blackfire\Desktop\推免材料\面试问题准备")
TARGET_JSON = Path(r"c:\Users\blackfire\Documents\PythonProject3\app\data\question_bank.json")

def clean_zh_title(title_line):
    # 移除 Qxx. / ZH_Qxx. / EN_Qxx.
    t = re.sub(r'^(?:EN_|ZH_)?Q\d+[\.:：]?\s*', '', title_line).strip()
    # 移除开头的【...】提示标签
    while t.startswith('【'):
        t = re.sub(r'^【[^】]+】\s*', '', t).strip()
    # 移除中文题目中的英文翻译括号，如（Setup Time）、（Violation）、（STA）、（Metastability）
    t = re.sub(r'[（\(][A-Za-z0-9\s,\-_/]+[）\)]', '', t).strip()
    # 清理多余连续空格
    t = re.sub(r'\s{2,}', ' ', t)
    return t

def clean_en_title(title_line):
    t = re.sub(r'^EN_Q\d+[\.:：]?\s*', '', title_line).strip()
    t = re.sub(r'[\(（][^\)）]*[\u4e00-\u9fa5]+[^\)）]*[\)）]', '', t).strip()
    t = re.sub(r'\s{2,}', ' ', t)
    return t

def clean_reference_answer(raw_text, category):
    lines = []
    for l in raw_text.splitlines():
        line = l.lstrip('> ').strip()
        if not line:
            continue
        if category == 'english':
            if line.startswith('*(') and ('中文' in line or '参考' in line):
                continue
            if line.startswith('(') and ('中文' in line or '参考' in line):
                continue
            line = re.sub(r'[\(（][^\)）]*[\u4e00-\u9fa5]+[^\)）]*[\)）]', '', line).strip()
            if len(re.findall(r'[\u4e00-\u9fa5]', line)) > 2:
                continue
        lines.append(line)
    res = '\n'.join(lines).strip()
    if category != 'english':
        res = re.sub(r'[（\(]([A-Za-z]{2,}(?:\s+[A-Za-z]+)+)[）\)]', '', res)
    return res.strip()

def clean_shorthand(raw_text, category):
    lines = []
    for l in raw_text.splitlines():
        line = l.lstrip('> ').strip()
        if not line:
            continue
        if line.startswith('[!TIP]') or line.startswith('[!NOTE]') or line.startswith('⚡'):
            continue
        if category == 'english':
            line = re.sub(r'[\(（][^\)）]*[\u4e00-\u9fa5]+[^\)）]*[\)）]', '', line).strip()
            if len(re.findall(r'[\u4e00-\u9fa5]', line)) > 2:
                continue
        lines.append(line)
    res = '\n'.join(lines).strip()
    if category != 'english':
        res = re.sub(r'[（\(]([A-Za-z]{2,}(?:\s+[A-Za-z]+)+)[）\)]', '', res)
    return res.strip()

def clean_highlight(raw_text, category):
    lines = []
    for l in raw_text.splitlines():
        line = l.lstrip('> ').strip()
        if not line or line.startswith('[!NOTE]') or line.startswith('[!TIP]'):
            continue
        lines.append(line)
    res = '\n'.join(lines).strip()
    if category != 'english':
        res = re.sub(r'[（\(]([A-Za-z]{2,}(?:\s+[A-Za-z]+)+)[）\)]', '', res)
    return res.strip()

def main():
    intro_md_path = SOURCE_DIR / "推免复试自我介绍_中英文精解(三段式).md"
    intro_md = intro_md_path.read_text(encoding="utf-8")

    zh_intro_match = re.search(r'### 🎙️ 考场标准口头作答发言文稿[^\n]*\n([\s\S]*?)(?=\n---|\n##|\Z)', intro_md)
    raw_zh = zh_intro_match.group(1).strip()
    clean_zh_intro = re.sub(r'\*\*【段落[一二三] [·•] [^】]+】\*\*\s*', '', raw_zh).strip()

    en_intro_match = re.search(r'### 🎙️ Spoken English Script[^\n]*\n([\s\S]*?)(?=\n###|\n---|\n##|\Z)', intro_md)
    raw_en = en_intro_match.group(1).strip()
    clean_en_intro = re.sub(r'\*\*\[Paragraph \d [·•] [^\]]+\]\*\*\s*', '', raw_en).strip()

    new_qb = []

    # 1. 中文自我介绍 (首题 gen_01)
    new_qb.append({
        "id": "gen_01",
        "category": "general",
        "subcategory": "自我介绍与综合素养",
        "question": "请你用一到两分钟时间，简要作一个自我介绍。",
        "tips": [
            "第一段【基本信息】：学业成绩（GPA 3.69/前14% 17/123）、核心课97/95、四六级、激光微纳实验认知",
            "第二段【比赛经历】：三大国家级一等奖硬核展开（集创赛企业大奖全国第1、嵌赛FPGA国一、机器人AI国一）与软硬件全栈闭环",
            "第三段【未来规划】：深耕DSA领域专用架构、异构计算与硬件安全，把SoC实践融入导师课题"
        ],
        "reference_answer": clean_zh_intro,
        "shorthand": "1. 基本信息：微电子排名17/123、四六级、激光微纳实验认知。\n2. 竞赛硬核：集创赛全国一等奖企业大奖第1、嵌赛FPGA国一、机器人AI国一，全栈落地与抗压排错。\n3. 未来规划：深耕DSA专用架构、异构计算与硬件安全，融入课题踏实攻关。",
        "highlight": "以通俗严谨的中文表述降低口语卡壳风险；若导师追问具体芯片型号再报出Intel Cyclone V与AMD Vitis HLS，展现底层硬核细节。",
        "keywords": ["刘子俊", "微电子", "GPA", "集创赛", "企业大奖", "FPGA", "Vitis HLS", "异构计算", "DSA", "硬件安全"]
    })

    # 2. 英文自我介绍 (首题 eng_intro_01)
    new_qb.append({
        "id": "eng_intro_01",
        "category": "english",
        "subcategory": "Self-Introduction & Background",
        "question": "Could you please give us a brief self-introduction within one minute?",
        "tips": [
            "Paragraph 1: Academic background, major, GPA (top 14%), core courses and CET-6",
            "Paragraph 2: Focused on FPGA and SoC design, three National First Prizes (IC Grand Award #1, HLS & edge AI)",
            "Paragraph 3: Master's aspirations in DSA, heterogeneous computing, and hardware security"
        ],
        "reference_answer": clean_en_intro,
        "shorthand": "1. Basic Info: Microelectronics, GPA 3.69 (top 14%), CET-6.\n2. Competitions: Focused on FPGA/SoC, won 3 National 1st Prizes (IC Grand Award #1, HLS & Edge AI).\n3. Future Goals: Master's in DSA, heterogeneous computing & hardware security.",
        "highlight": "Deliver with confident pace (140-150 words/min), emphasize 'Enterprise Grand Award, ranking First Place nationwide'.",
        "keywords": ["Liu Zijun", "Microelectronics", "Hubei University of Technology", "GPA", "National First Prize", "Integrated Circuit", "FPGA", "SoC", "HLS", "heterogeneous computing", "hardware security"]
    })

    # 3. 英语口语题库 (78题)
    eng_fpath = SOURCE_DIR / "英语口语/01_推免英语口语面试与专业问答全攻略.md"
    eng_content = eng_fpath.read_text(encoding="utf-8")
    eng_blocks = re.split(r"\n###\s+", eng_content)[1:]
    for idx, b in enumerate(eng_blocks, 1):
        first_line = b.splitlines()[0].strip()
        q_text = clean_en_title(first_line)
        if idx <= 28:
            cur_subcat = "Daily Life & Interests"
        elif idx <= 44:
            cur_subcat = "Family & Hometown"
        elif idx <= 70:
            cur_subcat = "Work, Study & Teamwork"
        else:
            cur_subcat = "Technical IC - Ultra-Short"

        ans_m = re.search(r"\*\*🎙️[^\n]*\*\*[:：]?\s*\n([\s\S]*?)(?=\n\*\*⚡|\Z)", b)
        short_m = re.search(r"\*\*⚡[^\n]*\*\*[:：]?\s*\n([\s\S]*?)(?=\n\*\*🌟|\n---\s*|\Z)", b)
        note_m = re.search(r"\*\*🌟[^\n]*\*\*[:：]?\s*\n([\s\S]*?)(?=\n---\s*|\Z)", b)

        ans_text = clean_reference_answer(ans_m.group(1), "english") if ans_m else ""
        short_text = clean_shorthand(short_m.group(1), "english") if short_m else ""
        note_text = clean_highlight(note_m.group(1), "english") if note_m else ""

        tips = []
        target_m = re.search(r'>\s*\*\*🎯[^\n]*\*\*[:：]?\s*(.*?)(?=\n|$)', b)
        if target_m:
            tips.append(target_m.group(1).strip())
        clue_m = re.search(r'>\s*\*\*💡[^\n]*\*\*[:：]?\s*(.*?)(?=\n|$)', b)
        if clue_m:
            tips.append(clue_m.group(1).strip())
        pts_m = re.search(r'>\s*\*\*🔑[^\n]*\*\*[:：]?\s*(.*?)(?=\n|$)', b)
        if pts_m:
            tips.append(pts_m.group(1).strip())
        tr_m = re.search(r'>\s*\*\*中文翻译\*\*[:：]?\s*(.*?)(?=\n|$)', b)
        if tr_m:
            tips.append(f"中文翻译：{tr_m.group(1).strip()}")

        keywords = []
        if pts_m:
            kw_raw = pts_m.group(1)
            keywords = [k.strip() for k in re.split(r'[•·,，|、\s]+', kw_raw) if k.strip() and len(k.strip()) > 1]

        new_qb.append({
            "id": f"eng_{idx:02d}",
            "category": "english",
            "subcategory": cur_subcat,
            "question": q_text,
            "reference_answer": ans_text,
            "shorthand": short_text,
            "highlight": note_text,
            "tips": tips,
            "keywords": keywords[:10]
        })

    # 4. 综合素质与跨学科能力题库 (18题)
    gen_fpath = SOURCE_DIR / "专业问题/00_专业素质和能力测试(7min)_核心题库与全速记指南.md"
    gen_content = gen_fpath.read_text(encoding="utf-8")
    gen_blocks = re.split(r"\n###\s+", gen_content)[1:]
    for idx, b in enumerate(gen_blocks, 1):
        first_line = b.splitlines()[0].strip()
        q_text = clean_zh_title(first_line)

        ans_m = re.search(r"\*\*🎙️[^\n]*\*\*[:：]?\s*\n([\s\S]*?)(?=\n\*\*⚡|\Z)", b)
        short_m = re.search(r"\*\*⚡[^\n]*\*\*[:：]?\s*\n([\s\S]*?)(?=\n\*\*🌟|\n---\s*|\Z)", b)
        note_m = re.search(r"\*\*🌟[^\n]*\*\*[:：]?\s*\n([\s\S]*?)(?=\n---\s*|\Z)", b)

        ans_text = clean_reference_answer(ans_m.group(1), "general") if ans_m else ""
        short_text = clean_shorthand(short_m.group(1), "general") if short_m else ""
        note_text = clean_highlight(note_m.group(1), "general") if note_m else ""

        tips = []
        target_m = re.search(r'>\s*\*\*🎯[^\n]*\*\*[:：]?\s*(.*?)(?=\n|$)', b)
        if target_m:
            tips.append(target_m.group(1).strip())
        clue_m = re.search(r'>\s*\*\*💡[^\n]*\*\*[:：]?\s*(.*?)(?=\n|$)', b)
        if clue_m:
            tips.append(clue_m.group(1).strip())
        pts_m = re.search(r'>\s*\*\*🔑[^\n]*\*\*[:：]?\s*(.*?)(?=\n|$)', b)
        if pts_m:
            tips.append(pts_m.group(1).strip())

        keywords = []
        if pts_m:
            kw_raw = pts_m.group(1)
            keywords = [k.strip() for k in re.split(r'[•·,，|、\s]+', kw_raw) if k.strip() and len(k.strip()) > 1]

        new_qb.append({
            "id": f"gen_{idx + 1:02d}",
            "category": "general",
            "subcategory": "综合素质与跨学科能力",
            "question": q_text,
            "reference_answer": ans_text,
            "shorthand": short_text,
            "highlight": note_text,
            "tips": tips,
            "keywords": keywords[:10]
        })

    # =========================================================================
    # 5. 专业课核心题库深度优化（严格聚焦五大核心必修课，彻底剔除FPGA/SoC/竞赛）
    # =========================================================================
    SUBCAT_SHUDIAN = "数电（数字电路与逻辑设计）"
    SUBCAT_MODIAN = "模电（模拟电子技术与电路基础）"
    SUBCAT_CMOS = "CMOS（CMOS集成电路与器件设计）"
    SUBCAT_CAILIAO = "半导体材料（半导体物理与能带理论）"
    SUBCAT_QIJIAN = "半导体器件（半导体微电子器件物理）"

    # 5.1 解析 01_数字集成电路与FPGA设计 (严格剔除 Q08 FPGA底层架构, Q09 FPGA vs ASIC, Q18 AXI4-Stream)
    p01_path = SOURCE_DIR / "专业问题/01_数字集成电路与FPGA设计_高频面试问答.md"
    p01_blocks = re.split(r"\n###\s+", p01_path.read_text(encoding="utf-8"))[1:]
    shudian_count = 0
    for idx, b in enumerate(p01_blocks, 1):
        if idx in [8, 9, 18]:  # 剔除 FPGA 底层、FPGA vs ASIC、AXI4 总线握手
            continue
        shudian_count += 1
        first_line = b.splitlines()[0].strip()
        q_text = clean_zh_title(first_line)

        ans_m = re.search(r"\*\*🎙️[^\n]*\*\*[:：]?\s*\n([\s\S]*?)(?=\n\*\*⚡|\Z)", b)
        short_m = re.search(r"\*\*⚡[^\n]*\*\*[:：]?\s*\n([\s\S]*?)(?=\n\*\*🌟|\n---\s*|\Z)", b)
        note_m = re.search(r"\*\*🌟[^\n]*\*\*[:：]?\s*\n([\s\S]*?)(?=\n---\s*|\Z)", b)

        tips = []
        target_m = re.search(r'>\s*\*\*🎯[^\n]*\*\*[:：]?\s*(.*?)(?=\n|$)', b)
        if target_m: tips.append(target_m.group(1).strip())
        clue_m = re.search(r'>\s*\*\*💡[^\n]*\*\*[:：]?\s*(.*?)(?=\n|$)', b)
        if clue_m: tips.append(clue_m.group(1).strip())
        pts_m = re.search(r'>\s*\*\*🔑[^\n]*\*\*[:：]?\s*(.*?)(?=\n|$)', b)
        if pts_m: tips.append(pts_m.group(1).strip())

        keywords = []
        if pts_m:
            keywords = [k.strip() for k in re.split(r'[•·,，|、\s]+', pts_m.group(1)) if k.strip() and len(k.strip()) > 1]

        new_qb.append({
            "id": f"acad_de_{shudian_count:02d}",
            "category": "academic",
            "subcategory": SUBCAT_SHUDIAN,
            "question": q_text,
            "reference_answer": clean_reference_answer(ans_m.group(1), "academic") if ans_m else "",
            "shorthand": clean_shorthand(short_m.group(1), "academic") if short_m else "",
            "highlight": clean_highlight(note_m.group(1), "academic") if note_m else "",
            "tips": tips,
            "keywords": keywords[:10]
        })

    # 5.2 解析 02_模拟集成电路与电路基础 (精确分流为 模电 与 CMOS)
    p02_path = SOURCE_DIR / "专业问题/02_模拟集成电路与电路基础_高频面试问答.md"
    p02_blocks = re.split(r"\n###\s+", p02_path.read_text(encoding="utf-8"))[1:]
    cmos_indices = {1, 2, 3, 4, 5, 6, 9, 11, 14, 15, 16, 17, 19, 20}
    modian_count = 0
    cmos_count = 0

    for idx, b in enumerate(p02_blocks, 1):
        first_line = b.splitlines()[0].strip()
        q_text = clean_zh_title(first_line)

        ans_m = re.search(r"\*\*🎙️[^\n]*\*\*[:：]?\s*\n([\s\S]*?)(?=\n\*\*⚡|\Z)", b)
        short_m = re.search(r"\*\*⚡[^\n]*\*\*[:：]?\s*\n([\s\S]*?)(?=\n\*\*🌟|\n---\s*|\Z)", b)
        note_m = re.search(r"\*\*🌟[^\n]*\*\*[:：]?\s*\n([\s\S]*?)(?=\n---\s*|\Z)", b)

        tips = []
        target_m = re.search(r'>\s*\*\*🎯[^\n]*\*\*[:：]?\s*(.*?)(?=\n|$)', b)
        if target_m: tips.append(target_m.group(1).strip())
        clue_m = re.search(r'>\s*\*\*💡[^\n]*\*\*[:：]?\s*(.*?)(?=\n|$)', b)
        if clue_m: tips.append(clue_m.group(1).strip())
        pts_m = re.search(r'>\s*\*\*🔑[^\n]*\*\*[:：]?\s*(.*?)(?=\n|$)', b)
        if pts_m: tips.append(pts_m.group(1).strip())

        keywords = []
        if pts_m:
            keywords = [k.strip() for k in re.split(r'[•·,，|、\s]+', pts_m.group(1)) if k.strip() and len(k.strip()) > 1]

        if idx in cmos_indices:
            cmos_count += 1
            qid = f"acad_cmos_{cmos_count:02d}"
            subcat = SUBCAT_CMOS
        else:
            modian_count += 1
            qid = f"acad_ae_{modian_count:02d}"
            subcat = SUBCAT_MODIAN

        new_qb.append({
            "id": qid,
            "category": "academic",
            "subcategory": subcat,
            "question": q_text,
            "reference_answer": clean_reference_answer(ans_m.group(1), "academic") if ans_m else "",
            "shorthand": clean_shorthand(short_m.group(1), "academic") if short_m else "",
            "highlight": clean_highlight(note_m.group(1), "academic") if note_m else "",
            "tips": tips,
            "keywords": keywords[:10]
        })

    # 5.3 解析 03_半导体物理与半导体器件 (精确分流为 半导体材料 与 半导体器件)
    p03_path = SOURCE_DIR / "专业问题/03_半导体物理与半导体器件_高频面试问答.md"
    p03_blocks = re.split(r"\n###\s+", p03_path.read_text(encoding="utf-8"))[1:]
    cailiao_indices = {1, 2, 11, 12, 13, 19}
    cailiao_count = 0
    qijian_count = 0

    for idx, b in enumerate(p03_blocks, 1):
        first_line = b.splitlines()[0].strip()
        q_text = clean_zh_title(first_line)

        ans_m = re.search(r"\*\*🎙️[^\n]*\*\*[:：]?\s*\n([\s\S]*?)(?=\n\*\*⚡|\Z)", b)
        short_m = re.search(r"\*\*⚡[^\n]*\*\*[:：]?\s*\n([\s\S]*?)(?=\n\*\*🌟|\n---\s*|\Z)", b)
        note_m = re.search(r"\*\*🌟[^\n]*\*\*[:：]?\s*\n([\s\S]*?)(?=\n---\s*|\Z)", b)

        tips = []
        target_m = re.search(r'>\s*\*\*🎯[^\n]*\*\*[:：]?\s*(.*?)(?=\n|$)', b)
        if target_m: tips.append(target_m.group(1).strip())
        clue_m = re.search(r'>\s*\*\*💡[^\n]*\*\*[:：]?\s*(.*?)(?=\n|$)', b)
        if clue_m: tips.append(clue_m.group(1).strip())
        pts_m = re.search(r'>\s*\*\*🔑[^\n]*\*\*[:：]?\s*(.*?)(?=\n|$)', b)
        if pts_m: tips.append(pts_m.group(1).strip())

        keywords = []
        if pts_m:
            keywords = [k.strip() for k in re.split(r'[•·,，|、\s]+', pts_m.group(1)) if k.strip() and len(k.strip()) > 1]

        if idx in cailiao_indices:
            cailiao_count += 1
            qid = f"acad_mat_{cailiao_count:02d}"
            subcat = SUBCAT_CAILIAO
        else:
            qijian_count += 1
            qid = f"acad_dev_{qijian_count:02d}"
            subcat = SUBCAT_QIJIAN

        new_qb.append({
            "id": qid,
            "category": "academic",
            "subcategory": subcat,
            "question": q_text,
            "reference_answer": clean_reference_answer(ans_m.group(1), "academic") if ans_m else "",
            "shorthand": clean_shorthand(short_m.group(1), "academic") if short_m else "",
            "highlight": clean_highlight(note_m.group(1), "academic") if note_m else "",
            "tips": tips,
            "keywords": keywords[:10]
        })

    # 5.4 从 湖南大学_电子信息_保研面试60问精解.md 精准提取经典核心课真题（数电、模电、材料、器件）
    phd_path = SOURCE_DIR / "湖南大学_电子信息_保研面试60问精解.md"
    phd_text = phd_path.read_text(encoding="utf-8")

    hd_supplements = [
        (
            "05",
            SUBCAT_SHUDIAN,
            "1. 核心区别：组合逻辑无记忆元件，输出仅取决于当前输入；时序逻辑包含存储单元（触发器/锁存器）与反馈回路，输出取决于当前输入和历史状态。\n2. 时序约束：时序逻辑受时钟驱动，必须满足建立时间与保持时间约束；组合逻辑主要受门传输延时与竞争冒险影响。\n3. 经典代表：组合逻辑如加法器、编码器；时序逻辑如寄存器、计数器、有限状态机FSM。",
            ["时序逻辑", "组合逻辑", "触发器", "锁存器", "记忆元件", "时钟驱动", "状态转移", "建立保持时间"]
        ),
        (
            "17",
            SUBCAT_SHUDIAN,
            "1. D触发器：特性方程Q(n+1)=D，时钟上升沿锁存输入D，抗干扰强、时序清晰，是现代数字IC与标准时序单元基石。\n2. JK触发器：特性方程Q(n+1)=J(~Q)+(~K)Q，属于万能触发器，具有保持(00)、置0(01)、置1(10)和翻转计数(11)四种功能。\n3. 互相转换：令J=D且K=~D可将JK转为D触发器；令J=K=T可将JK转为T触发器实现二进制分频。",
            ["D触发器", "JK触发器", "特性方程", "次态方程", "状态翻转", "时序逻辑", "计数器", "时钟触发"]
        ),
        (
            "04",
            SUBCAT_MODIAN,
            "1. 共射（CE）：反相高电压与电流放大，输出功率最高，输入输出阻抗中等，受密勒效应影响高频特性较差，用作主放大级。\n2. 共集（CC/射随器）：同相电压增益约1，高输入阻抗（减小信号衰减）、低输出阻抗（带载能力强），用于输入缓冲与输出驱动。\n3. 共基（CB）：同相高电压放大但无电流放大，低输入阻抗、高输出阻抗，无密勒效应且频带极宽，用于射频低噪放与Cascode。",
            ["共射组态", "共集组态", "共基组态", "电压增益", "输入电阻", "输出电阻", "密勒效应", "射极跟随器"]
        ),
        (
            "21",
            SUBCAT_MODIAN,
            "1. 稳定增益：闭环增益稳定性提升(1+AF)倍，极大减小晶体管参数分散与温度漂移对增益的影响。\n2. 展宽通频带：以牺牲增益为代价，使上限截止频率提高(1+AF)倍、下限截止频率降低，实现增益-带宽积守恒。\n3. 改善失真与阻抗：减小内部非线性失真与噪声；串联负反馈提高输入电阻，并联负反馈降低输入电阻；电压负反馈稳定输出电压并降低输出电阻，电流负反馈稳定输出电流并提高输出电阻。",
            ["负反馈", "增益稳定性", "展宽频带", "减小失真", "输入阻抗", "输出阻抗", "反馈深度", "闭环增益"]
        ),
        (
            "46",
            SUBCAT_MODIAN,
            "1. 甲类（Class-A）：Q点在交流负载线中点，导通角360度（全周期导通），线性度极佳但静态功耗巨大，理论最高转换效率仅50%（纯电阻负载为25%）。\n2. 乙类（Class-B）：Q点设在截止边界，导通角180度（半周期导通），效率大幅提升至理论上限78.5%，但推挽互补结构在过零点存在严重的交越失真。\n3. 甲乙类（Class-AB）：微导通偏置（Q点略高于截止区），导通角在180到360度之间，兼顾70%左右高效率且彻底消除交越失真，是音频与工业功放最经典主流拓扑。",
            ["功率放大器", "甲类功放", "乙类功放", "甲乙类功放", "导通角", "转换效率", "交越失真", "互补推挽"]
        ),
        (
            "55",
            SUBCAT_MODIAN,
            "1. 坐标与曲线：波特图采用对数坐标系，由幅频特性（纵轴dB=20lg|H|，横轴频率对数lgω）和相频特性（纵轴相角度，横轴lgω）组成。\n2. 渐近线法则：低频起始斜率由零极点阶数决定，每个一阶实极点使幅频斜率下降-20dB/dec并在转折频率处相移滞后-45度；每个实零点使幅频斜率上升+20dB/dec并在转折频率处相移超前+45度。\n3. 工程应用：快速分析放大器通频带与高低频截止频率；直观求解增益交点频率（0dB点）、相位裕度（PM）与增益裕度（GM），判定闭环负反馈系统的绝对稳定性。",
            ["波特图", "对数坐标", "幅频特性", "相频特性", "转折频率", "相位裕度", "增益裕度", "稳定性判据"]
        ),
        (
            "54",
            SUBCAT_CAILIAO,
            "1. N型半导体：掺入第V族元素（磷P、砷As），施主能级紧靠导带底；室温下施主杂质完全电离释放电子进入导带，多子为电子，少子为空穴。\n2. P型半导体：掺入第III族元素（硼B、镓Ga），受主能级紧靠价带顶；受主杂质捕获价带电子产生空穴，多子为空穴，少子为电子。\n3. 物理守恒：不论N型还是P型，热平衡下均严格服从载流子浓度积质量作用定律n0*p0=ni^2，且半导体整体宏观保持严格的电中性。",
            ["N型半导体", "P型半导体", "施主杂质", "受主杂质", "能带结构", "多子与少子", "质量作用定律", "电中性"]
        ),
        (
            "36",
            SUBCAT_QIJIAN,
            "1. 控制机理：FET为电压控制型器件，栅极几乎不取电流，输入阻抗极高；BJT为电流控制型器件，基极需连续偏置电流，输入阻抗较低。\n2. 载流子输运：FET为单极型器件，依靠多数载流子漂移导电，无少子复合与存储延时，热稳定性好、噪声低；BJT为双极型器件，多数与少数载流子共同参与，跨导效率更高、驱动力强。\n3. 工程分工：FET（CMOS）因超低静态功耗和极小尺寸主导超大规模数字IC与微处理器；BJT因高跨导、高线性度与低相位噪声在射频前端、超高速接口与超精模拟基准中占据主导。",
            ["场效应管", "双极型晶体管", "压控器件", "流控器件", "单极型", "双极型", "跨导效率", "输入阻抗"]
        )
    ]

    for qnum, subcat, short_txt, kw_list in hd_supplements:
        m = re.search(r'## (Q' + qnum + r'\.[\s\S]*?)(?=\n## Q|\Z)', phd_text)
        if not m:
            continue
        b = m.group(1)
        first_line = b.splitlines()[0].strip()
        q_text = clean_zh_title(first_line)

        target_m = re.search(r'>\s*\*\*🎯[^\n]*\*\*[:：]?\s*(.*?)(?=\n|$)', b)
        ans_m = re.search(r'### 🎙️[^\n]*\n([\s\S]*?)(?=\n### 💡|\Z)', b)
        hl_m = re.search(r'### 💡[^\n]*\n([\s\S]*?)(?=\n---\s*|\Z)', b)

        tips = [target_m.group(1).strip()] if target_m else []
        ans_text = clean_reference_answer(ans_m.group(1).strip(), "academic") if ans_m else ""
        hl_text = clean_highlight(hl_m.group(1).strip(), "academic") if hl_m else ""

        if subcat == SUBCAT_SHUDIAN:
            shudian_count += 1
            qid = f"acad_de_{shudian_count:02d}"
        elif subcat == SUBCAT_MODIAN:
            modian_count += 1
            qid = f"acad_ae_{modian_count:02d}"
        elif subcat == SUBCAT_CAILIAO:
            cailiao_count += 1
            qid = f"acad_mat_{cailiao_count:02d}"
        elif subcat == SUBCAT_QIJIAN:
            qijian_count += 1
            qid = f"acad_dev_{qijian_count:02d}"
        else:
            qid = f"acad_misc_{qnum}"

        new_qb.append({
            "id": qid,
            "category": "academic",
            "subcategory": subcat,
            "question": q_text,
            "reference_answer": ans_text,
            "shorthand": short_txt,
            "highlight": hl_text,
            "tips": tips,
            "keywords": kw_list[:10]
        })

    print(f"Total questions generated: {len(new_qb)}")
    from collections import Counter
    print("Categories:", Counter(q["category"] for q in new_qb))
    print("Academic Subcategories:")
    for sub, cnt in Counter(q["subcategory"] for q in new_qb if q["category"] == "academic").items():
        print(f"  - {sub}: {cnt} 题")

    # 4. 校验中英文纯度与非空
    errors = []
    zh_pattern = re.compile(r"[\u4e00-\u9fa5]")
    full_width_punct = set("，。！？：“”（）【】—、…")

    for q in new_qb:
        qid = q["id"]
        cat = q["category"]
        ref = q["reference_answer"]
        short = q["shorthand"]
        q_txt = q["question"]
        
        if not ref:
            errors.append(f"{qid}: empty reference_answer")
        if not short:
            errors.append(f"{qid}: empty shorthand")
        if not q_txt:
            errors.append(f"{qid}: empty question")
            
        if cat == "academic":
            if "FPGA" in q_txt:
                errors.append(f"{qid}: academic question contains FPGA: {q_txt}")
            if "FPGA" in q["subcategory"]:
                errors.append(f"{qid}: academic subcategory contains FPGA: {q['subcategory']}")

        if cat == "english":
            if zh_pattern.search(ref):
                errors.append(f"{qid}: EN ref contains Chinese")
            if zh_pattern.search(q_txt):
                errors.append(f"{qid}: EN question contains Chinese")
            if zh_pattern.search(short):
                errors.append(f"{qid}: EN shorthand contains Chinese")
            if any(c in full_width_punct for c in ref):
                errors.append(f"{qid}: EN ref contains full-width punctuation")
            if qid != "eng_intro_01":
                sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', ref.replace('\n', ' ')) if s.strip()]
                if not (2 <= len(sents) <= 3):
                    errors.append(f"{qid}: EN ref must have 2-3 sentences, got {len(sents)}")
        else:
            bracket_en = re.findall(r"[（\(]([A-Za-z]{2,}(?:\s+[A-Za-z]+)+)[）\)]", q_txt)
            if bracket_en:
                errors.append(f"{qid}: ZH Q contains bracketed english translation: {bracket_en}")

    if errors:
        print(f"Validation failed with {len(errors)} errors:")
        for e in errors[:10]:
            print("  ", e)
        return False

    with open(TARGET_JSON, "w", encoding="utf-8") as f:
        json.dump(new_qb, f, ensure_ascii=False, indent=2)

    print(f"Successfully validated and written to {TARGET_JSON}!")
    return True

if __name__ == "__main__":
    main()
