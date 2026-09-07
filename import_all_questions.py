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
    """生成口语化、纯生活与日常交流的高频保研英语面试真题"""
    daily_english_questions = [
        {
            "id": "eng_life_01",
            "category": "english",
            "subcategory": "Hometown & Living",
            "question": "Could you tell us a bit about your hometown? What do you like most about living or growing up there?",
            "tips": [
                "Geographical location and climate",
                "Famous attractions or local culture (e.g. Macheng's Azaleas or local delicacies)",
                "Personal emotional connection and warmth"
            ],
            "reference_answer": "I come from Macheng, a historic and picturesque city in northeastern Hubei Province. What I love most about my hometown is its natural beauty and warm community atmosphere. Every spring, millions of red azaleas bloom across the Guifeng Mountain, which is breathtaking. The local cuisine is delightful, and the people are kind and hospitable, which deeply shaped my optimistic personality.",
            "keywords": [
                "hometown", "Macheng", "natural beauty", "azalea", "cuisine", "culture", "growing up", "community"
            ]
        },
        {
            "id": "eng_life_02",
            "category": "english",
            "subcategory": "Hobbies & Leisure",
            "question": "What do you usually enjoy doing in your spare time or on weekends to relax?",
            "tips": [
                "Specific hobbies (e.g. running, playing badminton, music, reading)",
                "Why you enjoy it and how it helps you recharge",
                "Balance between study and daily life"
            ],
            "reference_answer": "In my spare time, I am a big fan of outdoor sports, especially running and playing badminton. Regular running helps me build physical stamina, clear my head, and release stress after a long day of intense mental work. On weekends, I also enjoy listening to acoustic music or reading science fiction, which broadens my imagination and keeps me energized.",
            "keywords": [
                "spare time", "running", "badminton", "stamina", "release stress", "music", "weekends", "relax"
            ]
        },
        {
            "id": "eng_life_03",
            "category": "english",
            "subcategory": "Stress Relief & Health",
            "question": "When you feel stressed or exhausted in daily life, how do you usually adjust your mood and unwind?",
            "tips": [
                "Acknowledge stress as a natural part of daily life",
                "Practical coping habits (sports, listening to music, talking with close friends)",
                "Maintaining emotional resilience and good sleep"
            ],
            "reference_answer": "Whenever I feel high pressure or mental fatigue, I usually step back rather than pushing myself blindly. I enjoy going for a 5-kilometer run on the campus playground; sweating it out always restores my mental clarity. I also like chatting with family or friends over a good meal to gain fresh perspectives. Staying calm and maintaining regular sleep helps me bounce back quickly.",
            "keywords": [
                "stressed", "unwind", "running", "mental clarity", "family", "friends", "resilience", "positive mindset"
            ]
        },
        {
            "id": "eng_life_04",
            "category": "english",
            "subcategory": "Campus Life",
            "question": "Could you share a memorable or interesting daily experience from your college life outside the classroom?",
            "tips": [
                "Non-academic campus event (e.g. sports festival, dorm camaraderie, volunteer activities)",
                "What happened and what you learned from it",
                "Warm and engaging conversational tone"
            ],
            "reference_answer": "A very memorable experience was participating in our university's annual sports festival as a relay runner for our department team. We trained together every evening after class for two weeks. Although we faced strong opponents, our team spirit and seamless baton handover earned us second place. That experience taught me the true joy of companionship, trust, and collective effort in daily college life.",
            "keywords": [
                "college life", "sports festival", "team spirit", "companionship", "relay runner", "memorable", "experience"
            ]
        },
        {
            "id": "eng_life_05",
            "category": "english",
            "subcategory": "Personality & Self-Awareness",
            "question": "How would your close friends or roommates describe your personality in daily life?",
            "tips": [
                "2-3 key positive traits (e.g. reliable, patient, easy-going, optimistic)",
                "A concrete everyday example (e.g. organizing dorm trips, helping peers)",
                "Self-awareness and good interpersonal skills"
            ],
            "reference_answer": "My roommates would describe me as reliable, patient, and easy-going. Whenever we plan a trip or dorm activity, they usually trust me to coordinate the itinerary because I am detail-oriented and organized. At the same time, they know I have a good sense of humor and can always lighten the mood when someone is feeling down. I am a patient listener and value sincere friendships.",
            "keywords": [
                "roommates", "friends", "personality", "reliable", "patient", "easy-going", "organized", "sense of humor"
            ]
        },
        {
            "id": "eng_life_06",
            "category": "english",
            "subcategory": "Reading & Entertainment",
            "question": "Do you have a favorite book, movie, or documentary? Could you briefly tell us what impressed you most about it?",
            "tips": [
                "Name of the book, movie, or documentary",
                "Core message or most touching scene",
                "Personal inspiration for your daily attitude towards life"
            ],
            "reference_answer": "One of my favorite books is 'The Three-Body Problem' by Liu Cixin. Beyond its dazzling cosmic imagination, what impressed me most is the persistent human spirit in the face of immense uncertainty and challenges. It taught me to stay curious about the unknown and remain humble and resilient in front of complex problems, which deeply inspires my everyday attitude towards life.",
            "keywords": [
                "favorite book", "The Three-Body Problem", "imagination", "curiosity", "resilience", "human spirit", "movie"
            ]
        },
        {
            "id": "eng_life_07",
            "category": "english",
            "subcategory": "Daily Routine & Habits",
            "question": "What does a typical day look like for you, and how do you organize your daily schedule?",
            "tips": [
                "Morning routine and regularity",
                "Balancing study, exercise, and rest",
                "Use of planning tools (to-do lists, notebook)"
            ],
            "reference_answer": "On a typical day, I usually get up around 7:30 a.m. and start with a nutritious breakfast. I like to write down three top priorities in my notebook for the day to keep myself focused. The daytime is dedicated to classes and productive work, while evenings are reserved for exercise and light reading. Going to bed around 11:30 p.m. ensures I stay energized and healthy every single day.",
            "keywords": [
                "typical day", "routine", "priorities", "notebook", "exercise", "focused", "healthy habit"
            ]
        },
        {
            "id": "eng_life_08",
            "category": "english",
            "subcategory": "City & Campus Living",
            "question": "What is your impression of this city, and how do you feel about living and studying here for your master's life?",
            "tips": [
                "City's culture, food, climate, and pace of living",
                "Campus atmosphere and facilities",
                "Enthusiasm for starting a fresh chapter of life here"
            ],
            "reference_answer": "I have a wonderful impression of this city. It combines profound cultural heritage with modern vitality and convenience. The campus environment here is beautiful and full of youthful energy, while the local cuisine and cultural life are rich and welcoming. I am truly looking forward to spending the next few years living here, exploring the city, and creating wonderful memories.",
            "keywords": [
                "impression", "city", "vitality", "culture", "campus", "welcoming", "living", "memories"
            ]
        },
        {
            "id": "eng_life_09",
            "category": "english",
            "subcategory": "Role Model & Influence",
            "question": "Is there a person who has greatly inspired or influenced you in your personal life?",
            "tips": [
                "Can be a family member, teacher, or personal mentor",
                "Specific qualities (e.g. dedication, patience, integrity, optimism)",
                "How their example shapes your daily actions and values"
            ],
            "reference_answer": "My grandfather has had the greatest influence on my life. As a retired teacher, he was always disciplined, humble, and passionately curious about the world. He taught me that true fulfillment comes from staying honest, patient, and dedicated to what you love every single day. His calm wisdom always gives me strength whenever I face obstacles.",
            "keywords": [
                "inspired", "influence", "grandfather", "teacher", "disciplined", "humble", "patience", "integrity"
            ]
        },
        {
            "id": "eng_life_10",
            "category": "english",
            "subcategory": "Work-Life Balance",
            "question": "As a prospective graduate student, how do you plan to maintain a healthy work-life balance during your postgraduate years?",
            "tips": [
                "Importance of physical and mental wellbeing",
                "Setting clear boundaries between study and leisure",
                "Participating in sports and socializing to avoid burnout"
            ],
            "reference_answer": "I believe high academic efficiency comes from a balanced lifestyle. During my graduate years, I will adhere to regular physical exercise, such as playing basketball or jogging three times a week, to keep my energy high. I also plan to actively communicate with fellow lab mates and participate in campus activities. Keeping a clear boundary between intensive work and restorative rest ensures sustainable personal growth.",
            "keywords": [
                "work-life balance", "lifestyle", "exercise", "mental health", "efficiency", "restorative", "sustainable"
            ]
        },
        {
            "id": "eng_life_11",
            "category": "english",
            "subcategory": "Food & Cooking",
            "question": "Can you cook, and what is your favorite dish to make or eat? Could you tell us a little bit about it?",
            "tips": [
                "Cooking abilities or favorite local dish (e.g. Hubei lotus root rib soup or homemade noodles)",
                "How preparing food or eating with family/friends brings joy and relaxation",
                "Nutritional balance and self-care away from home"
            ],
            "reference_answer": "Yes, I enjoy cooking simple and nutritious meals. My favorite dish is Hubei-style lotus root and pork rib soup, a specialty from my home province. Cooking teaches me patience, as simmering the soup slowly brings out its rich, sweet flavor. Enjoying a warm bowl of soup with family or roommates is one of my favorite ways to unwind and take good care of my health.",
            "keywords": [
                "cooking", "lotus root", "rib soup", "favorite dish", "patience", "nutritious", "unwind", "self-care"
            ]
        },
        {
            "id": "eng_life_12",
            "category": "english",
            "subcategory": "Travel & Exploration",
            "question": "Do you like traveling? Could you tell us about a memorable trip you took or a place you would love to visit?",
            "tips": [
                "A specific trip (e.g. hiking Yuelu Mountain, visiting historical sites, or natural parks)",
                "What impressed you most (scenery, local culture, historical atmosphere)",
                "How traveling broadens your worldview"
            ],
            "reference_answer": "I love traveling because it broadens my horizons. A memorable trip was visiting Changsha, where I climbed Yuelu Mountain and walked across Orange Isle. Standing by the Xiang River and visiting Yuelu Academy gave me a deep appreciation for classical Chinese culture and modern urban vibrancy. Traveling allows me to step out of my daily bubble and return with renewed energy.",
            "keywords": [
                "traveling", "Yuelu Mountain", "Changsha", "culture", "horizons", "scenery", "vibrancy", "memorable trip"
            ]
        },
        {
            "id": "eng_life_13",
            "category": "english",
            "subcategory": "Friendship & Socializing",
            "question": "How do you usually get along with people from diverse backgrounds, and what qualities do you value most in a good friend?",
            "tips": [
                "Qualities valued in friendship (sincerity, empathy, trustworthiness, mutual support)",
                "How to communicate openly and respect diverse viewpoints",
                "An example of maintaining strong friendships in college"
            ],
            "reference_answer": "In friendships, I value sincerity, empathy, and mutual support above all else. When meeting people from different regions or backgrounds, I always approach them with an open mind and respect their perspectives. A true friend is someone you can celebrate victories with, but also lean on during tough times. Maintaining honest and generous communication is key to building lifelong friendships.",
            "keywords": [
                "friendship", "sincerity", "empathy", "trustworthiness", "mutual support", "open mind", "communication"
            ]
        },
        {
            "id": "eng_life_14",
            "category": "english",
            "subcategory": "Music & Arts",
            "question": "What role does music or art play in your daily life? Do you have any favorite genres or artists?",
            "tips": [
                "Favorite music genres (e.g. classical, acoustic folk, pop, instrumental)",
                "When and why you listen (while coding, relaxing, commuting)",
                "How music uplifts your mood and sparks creativity"
            ],
            "reference_answer": "Music is an indispensable part of my daily routine. I especially love listening to acoustic guitar and instrumental soundtracks. When I am working on complex tasks, light ambient music helps me enter a flow state and stay concentrated. In the evening, soft melodies help me soothe mental tension and reflect on the day. Music brings emotional color and calm into my engineering life.",
            "keywords": [
                "music", "instrumental", "acoustic", "flow state", "relax", "tension", "creativity", "mindfulness"
            ]
        },
        {
            "id": "eng_life_15",
            "category": "english",
            "subcategory": "Volunteering & Community",
            "question": "Have you ever participated in any volunteer work or community service during your college years? What did you gain from it?",
            "tips": [
                "Volunteer experiences (welcoming freshmen, campus environmental drives, library assistant)",
                "Teamwork and communication skills gained",
                "Sense of social responsibility and personal fulfillment"
            ],
            "reference_answer": "During my sophomore year, I volunteered to welcome new freshmen and guide them through dorm registrations and campus tours. It was tiring under the summer heat, but answering their questions and easing their parents' worries gave me great satisfaction. That experience strengthened my communication skills and reinforced my belief that giving back to the community is deeply rewarding.",
            "keywords": [
                "volunteer", "community service", "freshmen", "giving back", "responsibility", "communication", "satisfaction"
            ]
        },
        {
            "id": "eng_life_16",
            "category": "english",
            "subcategory": "Overcoming Setbacks",
            "question": "Life doesn't always go as planned. Could you tell us about a small failure or disappointment you experienced and how you bounced back?",
            "tips": [
                "A genuine, relatable life setback (e.g. losing a sports match or failing a driving test)",
                "Constructive attitude: acknowledging emotions without being defeated",
                "The lesson learned and resulting growth"
            ],
            "reference_answer": "In my freshman year, our dorm basketball team lost a match by just one point in the closing seconds. We were disappointed initially, but instead of blaming each other, we gathered to analyze our defense mistakes and practiced harder together. That setback taught me that temporary failures are the best feedback for growth. Developing a resilient mindset matters far more than avoiding every stumble.",
            "keywords": [
                "setback", "disappointment", "basketball", "resilience", "bounced back", "growth mindset", "lesson learned"
            ]
        },
        {
            "id": "eng_life_17",
            "category": "english",
            "subcategory": "Curiosity & Self-Learning",
            "question": "Have you learned any new hobby or practical skill on your own recently? What motivated you to learn it?",
            "tips": [
                "A self-taught skill (e.g. photography, video editing, swimming, a musical instrument)",
                "Overcoming early learning curves",
                "The joy of self-driven curiosity and mastery"
            ],
            "reference_answer": "Recently, I taught myself basic smartphone photography and photo composition. I wanted to capture the fleeting moments of campus life and nature before graduation. Learning how light, contrast, and angles work was challenging at first, but seeing my pictures improve was immensely fulfilling. It reminded me that staying curious about new everyday skills keeps life vibrant and fresh.",
            "keywords": [
                "self-learning", "photography", "curiosity", "composition", "practical skill", "fulfilling", "vibrant"
            ]
        },
        {
            "id": "eng_life_18",
            "category": "english",
            "subcategory": "Daily Energy Management",
            "question": "Are you more of an early bird or a night owl? How do you maintain high energy throughout a demanding day?",
            "tips": [
                "Circadian preference (early bird / night owl)",
                "Strategies for steady energy (proper hydration, power naps, regular exercise)",
                "Aligning high-focus tasks with peak energy hours"
            ],
            "reference_answer": "I consider myself an early bird. I feel most creative and alert in the morning between 8:30 and 11:30 a.m., so I always reserve that window for my most demanding tasks. In the afternoon, a short 20-minute power nap completely restores my focus. Coupled with regular running and staying well-hydrated, I am able to sustain consistent mental stamina throughout demanding days.",
            "keywords": [
                "early bird", "stamina", "power nap", "peak energy", "alert", "focused", "healthy routine"
            ]
        },
        {
            "id": "eng_life_19",
            "category": "english",
            "subcategory": "Seasons & Campus Life",
            "question": "Which season of the year do you like the most, and why? How is that season on your university campus?",
            "tips": [
                "Favorite season (e.g. autumn with golden ginkgo leaves, or spring with blooming flowers)",
                "Campus scenery and pleasant atmosphere",
                "Personal activities enjoyed during that season"
            ],
            "reference_answer": "Autumn is undoubtedly my favorite season. The scorching summer heat fades away, and the weather turns crisp and clear. On our campus, the ginkgo trees along the main boulevard turn golden yellow, creating a picturesque golden carpet. It is the best time of the year for evening jogs and reading outdoors on campus benches, filling me with a sense of peace and inspiration.",
            "keywords": [
                "autumn", "season", "ginkgo trees", "campus", "crisp weather", "scenery", "jogging", "inspiration"
            ]
        },
        {
            "id": "eng_life_20",
            "category": "english",
            "subcategory": "Life Philosophy & Fulfillment",
            "question": "Looking beyond academic achievements, what does a fulfilling and happy life mean to you personally?",
            "tips": [
                "Core personal values: physical health, loving relationships, giving back",
                "Inner peace and lifelong curiosity",
                "Warm, authentic conclusion"
            ],
            "reference_answer": "To me, a fulfilling life is built on good health, loving family bonds, and sincere friendships. While academic and professional achievements are important, true happiness comes from staying kind, curious, and grateful every day. Being able to contribute positive value to the people around me and having the passion to learn something new every day is my definition of a meaningful life.",
            "keywords": [
                "fulfilling life", "happiness", "health", "family bonds", "curiosity", "kindness", "gratitude", "positive value"
            ]
        }
    ]

    paper_english_questions = [
        {
            "id": "eng_paper_01",
            "category": "english",
            "subcategory": "Paper Reading Methodology",
            "question": "How do you usually read an English research paper? Could you share your reading process or habits when dealing with complex academic articles?",
            "tips": [
                "Three-pass reading strategy: title/abstract/conclusion -> figures & architecture -> detailed methodology",
                "How to handle unfamiliar technical vocabulary without interrupting reading flow",
                "Taking structured notes (e.g. using Zotero, Notion, or paper summaries)"
            ],
            "reference_answer": "When reading an English paper, I usually adopt a structured three-pass approach. First, I carefully read the title, abstract, and conclusion to understand the core research problem and major contributions. Second, I look through all the diagrams, tables, and system architectures, which give me an intuitive grasp of their methodology. Finally, I dive into the implementation details. I also use reference managers like Zotero to highlight key insights and annotate recurring academic phrases.",
            "keywords": [
                "English paper", "three-pass", "abstract", "conclusion", "methodology", "architecture", "Zotero", "structured notes"
            ]
        },
        {
            "id": "eng_paper_02",
            "category": "english",
            "subcategory": "Literature Search & Tracking",
            "question": "Where do you typically search for literature, and how do you keep up with the latest international research progress in your field?",
            "tips": [
                "Academic databases and platforms (IEEE Xplore, Google Scholar, arXiv)",
                "Following top-tier international conferences in your domain (e.g. ISSCC, DAC, FPGA, ISCA)",
                "Habit of reading survey/review papers to grasp overall research landscapes"
            ],
            "reference_answer": "I mainly use IEEE Xplore and Google Scholar to retrieve peer-reviewed literature, and arXiv to track preprints. In the field of integrated circuits and hardware acceleration, I pay close attention to top conferences like ISSCC, DAC, and FPGA. When entering a new research topic, I always start with high-impact survey papers to establish a comprehensive big-picture understanding before drilling down into specific state-of-the-art designs.",
            "keywords": [
                "IEEE Xplore", "Google Scholar", "arXiv", "literature search", "top conferences", "survey papers", "state-of-the-art"
            ]
        },
        {
            "id": "eng_paper_03",
            "category": "english",
            "subcategory": "Impressive Paper Discussion",
            "question": "Could you briefly introduce an English research paper that impressed you the most, and tell us what you learned from it?",
            "tips": [
                "Paper topic and key contribution (e.g. Google's TPU architecture paper or a domain-specific accelerator review)",
                "The specific bottleneck it solved (e.g. memory wall, compute efficiency, hardware-software co-design)",
                "Personal reflection and academic takeaway"
            ],
            "reference_answer": "One paper that left a deep impression on me is the classic TPU architecture paper by Norm Jouppi's team published at ISCA. What fascinated me most was how they tailored the matrix multiplication unit with a systolic array architecture, achieving order-of-magnitude improvements in energy efficiency over conventional CPUs and GPUs. It inspired me deeply because it proved that breakthroughs in domain-specific hardware accelerators come from tight co-design with workload characteristics.",
            "keywords": [
                "TPU", "systolic array", "hardware accelerator", "matrix multiplication", "ISCA", "energy efficiency", "co-design"
            ]
        },
        {
            "id": "eng_paper_04",
            "category": "english",
            "subcategory": "Academic English & Writing",
            "question": "What are the biggest challenges you face when reading or writing academic English, and how do you plan to enhance your academic writing skills in graduate school?",
            "tips": [
                "Honest self-assessment (e.g. specialized terminology and concise sentence structures)",
                "Actionable improvement plans (reading high-level literature daily, building an academic phrase bank)",
                "Writing practice (revising thesis drafts, actively participating in group paper seminars)"
            ],
            "reference_answer": "My main challenge currently lies in concise academic expression and transitioning from passive reading to active academic writing. To overcome this, I am actively building my personal academic phrase bank by noting down standard transition phrases from high-impact IEEE journals. In graduate school, I plan to write weekly literature summaries, present regularly in lab seminars, and draft workshop papers to systematically polish my academic writing under advisor guidance.",
            "keywords": [
                "academic writing", "concise expression", "phrase bank", "IEEE journals", "literature summaries", "lab seminars"
            ]
        }
    ]

    return daily_english_questions + paper_english_questions


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
