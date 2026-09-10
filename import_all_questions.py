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

    en_intro_match = re.search(r'### 🎙️ 1-Minute Spoken English Script[^\n]*\n([\s\S]*?)(?=\n###|\n---|\n##|\Z)', intro_md)
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

    # 3. 解析各科目全量题库
    files_config = [
        ("academic", "专业问题/01_数字集成电路与FPGA设计_高频面试问答.md", "数字IC与FPGA设计", "acad_01"),
        ("academic", "专业问题/02_模拟集成电路与电路基础_高频面试问答.md", "模拟集成电路与电路基础", "acad_02"),
        ("academic", "专业问题/03_半导体物理与半导体器件_高频面试问答.md", "半导体物理与半导体器件", "acad_03"),
        ("academic", "专业问题/04_微电子制造工艺与先进封装_高频面试问答.md", "微电子制造工艺与先进封装", "acad_04"),
        ("academic", "专业问题/05_计算机体系结构与SoC软硬件协同_高频面试问答.md", "体系结构与SoC软硬件协同", "acad_05"),
        ("academic", "专业问题/06_三大核心国一项目与科研实践深度答辩_专项问答.md", "国一项目与科研实践答辩", "acad_06"),
        ("general", "专业问题/00_专业素质和能力测试(7min)_核心题库与全速记指南.md", "综合素质与跨学科能力", "gen"),
        ("english", "英语口语/01_推免英语口语面试与专业问答全攻略.md", "英语口语水平测试", "eng")
    ]

    for cat, rel, subcat, prefix in files_config:
        fpath = SOURCE_DIR / rel
        content = fpath.read_text(encoding="utf-8")
        blocks = re.split(r"\n###\s+", content)[1:]
        
        for idx, b in enumerate(blocks, 1):
            first_line = b.splitlines()[0].strip()
            if cat == "english":
                q_text = clean_en_title(first_line)
            else:
                q_text = clean_zh_title(first_line)
                
            cur_subcat = subcat
            if cat == "english":
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
            
            ans_text = clean_reference_answer(ans_m.group(1), cat) if ans_m else ""
            short_text = clean_shorthand(short_m.group(1), cat) if short_m else ""
            note_text = clean_highlight(note_m.group(1), cat) if note_m else ""
            
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
                
            if cat == "english":
                tr_m = re.search(r'>\s*\*\*中文翻译\*\*[:：]?\s*(.*?)(?=\n|$)', b)
                if tr_m:
                    tips.append(f"中文翻译：{tr_m.group(1).strip()}")
                    
            if cat == "academic":
                qid = f"{prefix}_{idx:02d}"
            elif cat == "general":
                qid = f"gen_{idx + 1:02d}"
            else:
                qid = f"eng_{idx:02d}"
                
            keywords = []
            if pts_m:
                kw_raw = pts_m.group(1)
                keywords = [k.strip() for k in re.split(r'[•·,，|、\s]+', kw_raw) if k.strip() and len(k.strip()) > 1]
                
            new_qb.append({
                "id": qid,
                "category": cat,
                "subcategory": cur_subcat,
                "question": q_text,
                "reference_answer": ans_text,
                "shorthand": short_text,
                "highlight": note_text,
                "tips": tips,
                "keywords": keywords[:10]
            })

    print(f"Total questions generated: {len(new_qb)}")
    from collections import Counter
    print("Categories:", Counter(q["category"] for q in new_qb))

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
