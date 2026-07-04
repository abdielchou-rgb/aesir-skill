#!/usr/bin/env python3
"""Æsir 叙事智能层 — TMDb 关键词 + 10 维标注 + 原子预测器

一个文件，三种能力：

  python3 aesir-narrative-intel.py --text "一段故事概要..."
  python3 aesir-narrative-intel.py --file novel.txt
  python3 aesir-narrative-intel.py --server --port 8766

输出：
  {
    "keywords": ["时间旅行", "反乌托邦", ...],
    "dimensions": { ... 10 维标注 ... },
    "atom_predictions": { ... 原子分布概率 ... }
  }
"""

import json, re, math, sys, os
from pathlib import Path
from collections import Counter
from typing import Optional

# ═══════════════════════════════════════════════════════════════
#  1. TMDb 关键词库（本地内嵌版，~300 个关键词）
# ═══════════════════════════════════════════════════════════════

TMDB_KEYWORD_DB = {
    # ── 调性/情绪 ──
    "tone": {
        "dark": ["黑暗", "阴暗", "阴沉", "压抑", "晦暗", "沉重", "dystopian", "apocalyptic", "gloomy", "grim", "bleak"],
        "light": ["轻松", "明亮", "明快", "轻快", "欢快", "温暖", "uplifting", "heartwarming", "feel-good", "lighthearted"],
        "suspenseful": ["悬疑", "紧张", "扣人心弦", "步步紧逼", "thriller", "suspenseful", "tense", "edge-of-your-seat"],
        "humorous": ["幽默", "搞笑", "喜剧", "诙谐", "滑稽", "comedy", "humorous", "witty", "satirical", "parody"],
        "melancholic": ["忧伤", "忧郁", "悲伤", "感伤", "惆怅", "melancholy", "bittersweet", "poignant", "nostalgic"],
        "whimsical": ["奇幻", "梦幻", "超现实", "荒诞", "magical", "whimsical", "surreal", "dreamlike", "fantastical"],
    },
    # ── 情节类型 ──
    "plot": {
        "coming_of_age": ["成长", "青春", "成年", "蜕变", "coming of age", "growing up", "adolescence", "self-discovery"],
        "revenge": ["复仇", "报仇", "报复", "vengeance", "retribution", "payback"],
        "redemption": ["救赎", "赎罪", "改过", "redemption", "atonement", "forgiveness", "second chance"],
        "journey": ["旅程", "旅途", "远征", "冒险", "journey", "quest", "expedition", "odyssey", "adventure"],
        "fish_out_of_water": ["格格不入", "异类", "局外人", "水土不服", "fish out of water", "outsider", "stranger in a strange land"],
        "love_story": ["爱情", "恋爱", "浪漫", "缘分", "romance", "love story", "romantic", "star-crossed"],
        "mystery": ["谜团", "秘密", "解谜", "悬案", "mystery", "whodunit", "enigma", "puzzle", "unravel"],
        "heist": ["盗窃", "劫案", "偷窃", "heist", "caper", "robbery", "con job"],
        "survival": ["生存", "求生", "荒野", "幸存", "survival", "stranded", "survivor", "endurance"],
        "betrayal": ["背叛", "出卖", "告密", "betrayal", "treachery", "double cross", "traitor"],
        "transformation": ["变形", "变身", "转变", "进化", "transformation", "metamorphosis", "change", "rebirth"],
        "investigation": ["调查", "侦查", "追查", "investigation", "detective", "sleuthing", "search for truth"],
        "race_against_time": ["限时", "倒计时", "争分夺秒", "race against time", "countdown", "deadline", "urgency"],
        "underdog": ["逆袭", "弱者", "逆転", "underdog", "against all odds", "rise from nothing"],
    },
    # ── 角色原型 ──
    "character": {
        "chosen_one": ["天选", "预言", "命运之子", "chosen one", "prophecy", "destined", "the one"],
        "mentor": ["导师", "师父", "引路人", "mentor", "guide", "teacher", "wise old man"],
        "antihero": ["反英雄", "灰色角色", "antihero", "morally ambiguous", "flawed hero"],
        "detective": ["侦探", "警探", "刑警", "detective", "investigator", "inspector"],
        "outlaw": [" outlaw", "亡命徒", "罪犯", "outlaw", "fugitive", "criminal", "rogue"],
        "scientist": ["科学家", "研究者", "博士", "scientist", "researcher", "inventor"],
        "artist": ["艺术家", "画家", "作家", "诗人", "artist", "painter", "writer", "poet", "musician"],
        "warrior": ["战士", "武士", "勇士", "骑士", "warrior", "fighter", "knight", "soldier"],
        "orphan": ["孤儿", "弃儿", "孤独", "orphan", "abandoned", "lonely"],
        "trickster": ["骗子", "狡诈", "诡计", "trickster", "con man", "deceiver", "shape-shifter"],
    },
    # ── 设定/背景 ──
    "setting": {
        "small_town": ["小镇", "乡村", "村庄", "small town", "village", "countryside", "rural"],
        "big_city": ["都市", "城市", "大都会", "big city", "urban", "metropolis", "city life"],
        "post_apocalyptic": ["末世", "废土", "末日", "post-apocalyptic", "wasteland", "after the end"],
        "historical": ["历史", "古装", "年代", "historical", "period piece", "era", "period drama"],
        "fantasy_world": ["奇幻世界", "魔法", "异世界", "fantasy world", "magical realm", "other world"],
        "space": ["太空", "宇宙", "星际", "space", "outer space", "interstellar", "galaxy"],
        "underwater": ["水下", "海底", "海洋", "underwater", "ocean", "深海", "submarine"],
        "school": ["校园", "学校", "学院", "school", "campus", "university", "academy"],
        "family_home": ["家庭", "家宅", "老家", "family", "home", "house", "ancestral home"],
        "prison": ["监狱", "牢房", "囚禁", "prison", "jail", "incarceration", "captivity"],
        "island": ["岛屿", "孤岛", "荒岛", "island", "isolated", "desert island"],
        "war_zone": ["战场", "战争", "前线", "war", "battlefield", "front line", "military"],
        "suburbia": ["郊区", "社区", " suburb", "suburbia", "neighborhood", "suburban"],
    },
    # ── 主题/信息 ──
    "theme": {
        "identity": ["身份", "认同", "自我", "identity", "self", "who am I", "self-discovery"],
        "freedom": ["自由", "解放", "挣脱", "freedom", "liberation", "emancipation", "breaking free"],
        "justice": ["正义", "公正", "公平", "justice", "fairness", "righteousness", "moral justice"],
        "family": ["家庭", "亲情", "血缘", "family", "family bonds", "siblings", "parent-child"],
        "friendship": ["友情", "友谊", "伙伴", "friendship", "loyalty", "companionship", "brotherhood"],
        "sacrifice": ["牺牲", "奉献", "代价", "sacrifice", "selflessness", "pay the price"],
        "power": ["权力", "力量", "控制", "power", "control", "authority", "domination"],
        "greed": ["贪婪", "欲望", "野心", "greed", "ambition", "avarice", "desire"],
        "loss": ["失去", "失落", "丧", "loss", "grief", "mourning", "absence"],
        "hope": ["希望", "信念", "坚持", "hope", "faith", "perseverance", "believing"],
        "truth": ["真相", "真实", "欺骗", "truth", "deception", "lies", "revelation"],
        "belonging": ["归属", "接纳", "融入", "belonging", "acceptance", "fitting in", "home"],
    }
}

# 展平为关键词→分类的映射表，用于快速匹配
_FLAT_KW_MAP = {}
for cat, subcats in TMDB_KEYWORD_DB.items():
    for subcat, kws in subcats.items():
        for kw in kws:
            _FLAT_KW_MAP[kw] = {"category": cat, "subcategory": subcat}


def match_keywords(text: str, top_n: int = 10) -> list:
    """从用户文本中匹配最相关的 TMDb 关键词"""
    text_lower = text.lower()
    matches = []
    for kw, meta in _FLAT_KW_MAP.items():
        if kw in text_lower:
            # 计算匹配权重：精确匹配 > 部分匹配
            weight = 1.0 if len(kw) > 3 else 0.5
            # 长关键词权重更高
            weight *= 1 + math.log(1 + len(kw)) / 10
            matches.append({"keyword": kw, "category": meta["category"], "subcategory": meta["subcategory"], "weight": round(weight, 3)})

    # 去重（同 subcategory 只保留最高权重的）
    seen = set()
    deduped = []
    for m in sorted(matches, key=lambda x: -x["weight"]):
        key = m["subcategory"]
        if key not in seen:
            seen.add(key)
            deduped.append(m)

    return deduped[:top_n]


# ═══════════════════════════════════════════════════════════════
#  2. 10 维标注体系
# ═══════════════════════════════════════════════════════════════

DIMENSION_META = {
    "narrative_perspective": {
        "name": "叙事视角",
        "range": [1, 5],
        "labels": {1: "第一人称", 2: "近身第三人称", 3: "自由间接", 4: "全知", 5: "多重视角切换"},
        "description": "叙述者与故事世界的距离",
    },
    "temporal_structure": {
        "name": "时间结构",
        "range": [1, 5],
        "labels": {1: "线性", 2: "顺叙有插叙", 3: "双线交错", 4: "非线性/碎片", 5: "环形"},
        "description": "事件在时间轴上的组织方式",
    },
    "dialogue_density": {
        "name": "对话密度",
        "range": [1, 5],
        "labels": {1: "纯叙事", 2: "叙事为主", 3: "均衡", 4: "对话为主", 5: "纯对话/剧本"},
        "description": "对话文本占总文本的比例",
    },
    "conflict_internal_external": {
        "name": "冲突内外比",
        "range": [1, 5],
        "labels": {1: "纯外部冲突", 2: "外主内辅", 3: "均衡", 4: "内主外辅", 5: "纯内部冲突"},
        "description": "冲突是角色内心挣扎还是与外部力量的对抗",
    },
    "emotional_peak_position": {
        "name": "情感峰值位置",
        "range": [1, 4],
        "labels": {1: "开头", 2: "中段", 3: "结尾", 4: "分散/多次起伏"},
        "description": "情感张力最高点的位置",
    },
    "ambiguity": {
        "name": "多义性",
        "range": [1, 5],
        "labels": {1: "说满", 2: "基本说清", 3: "有留白", 4: "多义开放", 5: "极度不确定"},
        "description": "文本允许多少种不同的解读",
    },
    "information_release_speed": {
        "name": "信息释放速度",
        "range": [1, 5],
        "labels": {1: "极慢（层层铺垫）", 2: "偏慢", 3: "中等", 4: "偏快", 5: "极快（开头即爆点）"},
        "description": "关键信息披露给读者的节奏",
    },
    "sensory_anchor": {
        "name": "感官锚点",
        "range": [1, 4],
        "labels": {1: "视觉主导", 2: "听觉主导", 3: "触觉/体感主导", 4: "多感官平衡"},
        "description": "描写依赖的感官通道",
    },
    "paragraph_rhythm": {
        "name": "段落节奏",
        "range": [1, 3],
        "labels": {1: "短段落密集", 2: "长段落舒展", 3: "交替变化"},
        "description": "段落的长度和切换节奏",
    },
    "moral_complexity": {
        "name": "道德复杂度",
        "range": [1, 5],
        "labels": {1: "黑白分明", 2: "灰色偏明", 3: "道德灰色", 4: "深度灰色", 5: "无法判断对错"},
        "description": "故事中角色行为的道德可判断性",
    },
}


def extract_dimensions(text: str) -> dict:
    """从文本中提取 10 维标注值

    基于表层蒸馏特征 + 简单启发式规则，不需要 LLM。
    """
    if not text or len(text) < 20:
        return {k: {"value": 3, "confidence": 0} for k in DIMENSION_META}

    sentences = re.split(r'[。！？！？.!?\n]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 3]
    words = text.split()
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    lines = text.split('\n')
    text_lower = text.lower()

    # ── 统计特征 ──
    # 对话比例
    dialogue_lines = [l for l in lines if l.strip().startswith('"') or l.strip().startswith('「') or l.strip().startswith('"')]
    dialogue_ratio = len(dialogue_lines) / max(len(lines), 1)

    # 人称
    first_p = len(re.findall(r'\b我\b|\b我们\b', text))
    third_p = len(re.findall(r'\b他\b|\b她\b|\b它\b|\b他们\b|\b她们\b', text))
    total_ref = first_p + third_p
    first_ratio = first_p / max(total_ref, 1) if total_ref > 0 else 0.5

    # 句长
    sent_lengths = [len(s.split()) for s in sentences] if sentences else [15]
    mean_sl = sum(sent_lengths) / max(len(sent_lengths), 1)
    std_sl = math.sqrt(sum((l - mean_sl)**2 for l in sent_lengths) / max(len(sent_lengths), 1)) if len(sent_lengths) > 1 else 0

    # 段落长度
    para_lengths = [len(p.split()) for p in paragraphs] if paragraphs else [100]
    mean_pl = sum(para_lengths) / max(len(para_lengths), 1)

    # 感官通道
    visual = len(re.findall(r'看[见到]?|目光|眼神|颜色|光|阴影|形状|look|see|gaze|color|light', text_lower))
    auditory = len(re.findall(r'听[见到]?|声音|脚步|呼吸|说|道|tell|hear|sound|voice|footstep', text_lower))
    tactile = len(re.findall(r'触摸|温度|冷|热|粗糙|柔软|痛|touch|cold|warm|pain', text_lower))
    total_sense = visual + auditory + tactile

    # 情感波动检测（'但''却''然而''突然''竟然' 等转折词密集度）
   转折词 = len(re.findall(r'但|却|然而|突然|竟然|没想到|谁知', text))
   转折密度 = 转折词 / max(len(sentences), 1)

    # 问句比例（多义性的代理）
    问句比例 = len(re.findall(r'[？?]', text)) / max(len(sentences), 1)

    # ── 维度推断 ──

    # 1. 叙事视角
    if first_ratio > 0.6:
        perspective = 1
    elif first_ratio > 0.3:
        perspective = 2
    else:
        perspective = 4

    # 2. 时间结构（检测时间词）
    时间跳跃词 = len(re.findall(r'多年[后前]|几天[后前]|回忆|记[得起]|曾经|那时|后来|before|after|years later|flashback|memory', text_lower))
    if 时间跳跃词 > 5:
        temporal = 4
    elif 时间跳跃词 > 2:
        temporal = 2
    else:
        temporal = 1

    # 3. 对话密度
    if dialogue_ratio > 0.6:
        dialogue_d = 4
    elif dialogue_ratio > 0.35:
        dialogue_d = 3
    elif dialogue_ratio > 0.15:
        dialogue_d = 2
    else:
        dialogue_d = 1

    # 4. 冲突内外比（用第一人称+心理动词做代理）
    心理动词 = len(re.findall(r'想|觉得|感到|知道|希望|害怕|担心|think|feel|wonder|hope|fear', text_lower))
    外部动词 = len(re.findall(r'说|走|来|去|拿|放|打|run|walk|take|fight|grab', text_lower))
    internal_ratio = 心理动词 / max(心理动词 + 外部动词, 1)
    conflict_val = round(1 + internal_ratio * 4)

    # 5. 情感峰值位置（用转折词分布做代理）
    # 简单启发：转折词集中在后半段则为结尾高峰
    if 转折密度 > 0.3:
        peak = 4  # 多次起伏
    elif 转折密度 > 0.15:
        peak = 2  # 中段
    else:
        peak = 3  # 结尾

    # 6. 多义性
    if 问句比例 > 0.2:
        ambiguity_val = 4
    elif 问句比例 > 0.1:
        ambiguity_val = 3
    else:
        ambiguity_val = 2

    # 7. 信息释放速度
    # 短句多 + 转折多 = 信息释放快
    short_sent_ratio = sum(1 for s in sentences if len(s.split()) <= 5) / max(len(sentences), 1)
    info_speed = round(1 + (short_sent_ratio + 转折密度 / max(转折密度, 0.1)) * 2)
    info_speed = max(1, min(5, info_speed))

    # 8. 感官锚点
    if total_sense > 0:
        视觉比 = visual / total_sense
        听觉比 = auditory / total_sense
        触觉比 = tactile / total_sense
        if 视觉比 > 0.5:
            sensory = 1
        elif 听觉比 > 0.5:
            sensory = 2
        elif 触觉比 > 0.5:
            sensory = 3
        else:
            sensory = 4
    else:
        sensory = 1

    # 9. 段落节奏
    if mean_pl < 50:
        rhythm = 1
    elif mean_pl > 120:
        rhythm = 2
    else:
        rhythm = 3

    # 10. 道德复杂度
    # 用"灰色"词的密度做代理
    灰色词 = len(re.findall(r'矛盾|复杂|两难|对错|善恶|纠结|犹豫|ambiguous|dilemma|gray|complex|moral', text_lower))
    if 灰色词 > 4:
        moral = 4
    elif 灰色词 > 2:
        moral = 3
    else:
        moral = 2

    results = {
        "narrative_perspective": {"value": perspective, "confidence": 0.7},
        "temporal_structure": {"value": temporal, "confidence": 0.6},
        "dialogue_density": {"value": dialogue_d, "confidence": 0.8},
        "conflict_internal_external": {"value": conflict_val, "confidence": 0.55},
        "emotional_peak_position": {"value": peak, "confidence": 0.5},
        "ambiguity": {"value": ambiguity_val, "confidence": 0.6},
        "information_release_speed": {"value": info_speed, "confidence": 0.65},
        "sensory_anchor": {"value": sensory, "confidence": 0.7},
        "paragraph_rhythm": {"value": rhythm, "confidence": 0.75},
        "moral_complexity": {"value": moral, "confidence": 0.5},
    }

    return results


# ═══════════════════════════════════════════════════════════════
#  3. 原子分布预测器
# ═══════════════════════════════════════════════════════════════

ATOM_TYPE_MAP = {
    "protagonist": {
        "普通人": ["ordinary", "everyday", "normal", "common", "平凡", "普通"],
        "天选之人": ["chosen", "destiny", "prophecy", "special", "天选", "命运", "预言"],
        "局外人": ["outsider", "stranger", "alienated", "格格不入", "局外", "异类"],
        "复仇者": ["revenge", "vengeance", "复仇", "报仇", "报复"],
        "守护者": ["protect", "guardian", "shield", "守护", "保护", "卫士"],
        "探索者": ["explore", "discover", "seek", "quest", "探索", "发现", "追寻"],
    },
    "conflict": {
        "身份冲突": ["identity", "who am i", "self", "身份", "自我", "认同"],
        "资源冲突": ["resource", "money", "power", "scarce", "资源", "金钱", "权力", "争夺"],
        "价值观冲突": ["value", "belief", "principle", "morality", "价值观", "信念", "信仰"],
        "关系冲突": ["relationship", "love", "family", "friend", "关系", "爱情", "亲情"],
        "生存冲突": ["survive", "survival", "death", "life or death", "生存", "活下来", "生死"],
        "认知冲突": ["truth", "discover", "realize", "真相", "认知", "知道", "发现"],
    },
    "tone": {
        "冷峻写实": ["realistic", "cold", "detached", "bare", "写实", "冷", "克制", "冷静"],
        "温暖治愈": ["warm", "healing", "comfort", "gentle", "温暖", "治愈", "温柔", "暖"],
        "黑色幽默": ["dark comedy", "black humor", "satirical", "讽刺", "黑色幽默", "荒诞"],
        "悬疑暗流": ["suspense", "mysterious", "unease", "悬疑", "不安", "暗流", "紧张"],
        "诗意思辨": ["poetic", "philosophical", "contemplative", "诗意", "思辨", "哲思"],
        "激烈狂暴": ["intense", "violent", "fierce", "激烈", "狂暴", "激烈", "紧张"],
    },
    "setting": {
        "封闭空间": ["closed", "room", "isolated", "密室", "封闭", "孤岛", "密闭"],
        "双界穿梭": ["two worlds", "between", "穿梭", "两个世界", "穿越"],
        "旅途": ["journey", "travel", "road", "旅途", "旅行", "路上"],
        "小社会": ["community", "small group", "society", "社群", "社区", "小社会"],
        "日常入侵": ["daily", "ordinary", "intrusion", "日常", "入侵", "平凡"],
        "失落世界": ["lost", "hidden", "ancient", "失落", "隐藏", "古老"],
    },
    "turn": {
        "秘密揭露": ["secret", "reveal", "truth", "秘密", "揭露", "真相"],
        "角色反转": ["reversal", "switch", "betray", "反转", "颠倒", "背叛"],
        "假胜利": ["fake", "false victory", "trick", "假", "欺骗", "陷阱"],
        "外力介入": ["intervention", "outside", "force", "介入", "外力", "干预"],
        "代价显现": ["cost", "price", "consequence", "代价", "后果", "付出"],
        "认知升级": ["realize", "awaken", "understand", "觉醒", "明白", "认知"],
    },
}


def predict_atoms(text: str) -> dict:
    """基于文本内容预测故事原子的分布概率

    使用关键词匹配 + 频率归一化，返回每个原子上级的预测置信度。
    不需要训练数据，零成本运行。
    """
    if not text or len(text) < 10:
        return {}

    text_lower = text.lower()
    results = {}

    for atom_type, atoms in ATOM_TYPE_MAP.items():
        type_scores = {}
        for atom_name, keywords in atoms.items():
            score = 0
            for kw in keywords:
                if kw in text_lower:
                    # 匹配度权重：越长越精确
                    score += 1 + math.log(1 + len(kw)) / 5
            type_scores[atom_name] = round(score, 3)

        # 归一化为 0-1 置信度
        max_score = max(type_scores.values()) if type_scores else 0
        if max_score > 0:
            normalized = {k: round(v / max_score, 3) for k, v in type_scores.items()}
        else:
            normalized = {k: 0 for k in type_scores}

        # 排序
        sorted_atoms = sorted(normalized.items(), key=lambda x: -x[1])
        results[atom_type] = {
            "predictions": [{"atom": k, "confidence": v} for k, v in sorted_atoms if v > 0.1],
            "top": sorted_atoms[0][0] if sorted_atoms else None,
            "top_confidence": sorted_atoms[0][1] if sorted_atoms else 0,
        }

    return results


# ═══════════════════════════════════════════════════════════════
#  4. 联合 API
# ═══════════════════════════════════════════════════════════════

def analyze_text(text: str, source_name: str = "") -> dict:
    """对一段文本执行完整叙事智能分析

    返回：关键词 + 10 维标注 + 原子分布预测
    """
    if not text.strip():
        return {"error": "文本不能为空"}

    keywords = match_keywords(text, top_n=10)
    dimensions = extract_dimensions(text)
    atoms = predict_atoms(text)

    # 合并维度为简写风格档案
    style_snapshot = {}
    for dim_key, dim_data in dimensions.items():
        meta = DIMENSION_META.get(dim_key, {})
        标签 = meta.get("labels", {}).get(dim_data["value"], str(dim_data["value"]))
        style_snapshot[dim_key] = {
            "value": dim_data["value"],
            "label": 标签,
            "confidence": dim_data["confidence"],
        }

    # 原子概要
    atom_summary = {}
    for atype, adata in atoms.items():
        if adata["top"]:
            atom_summary[atype] = f"{adata['top']} ({round(adata['top_confidence']*100)}%)"

    return {
        "source": source_name or "未命名",
        "text_length": len(text),
        "keywords": keywords,
        "keywords_by_category": {
            cat: [k for k in keywords if k["category"] == cat]
            for cat in ["tone", "plot", "character", "setting", "theme"]
        },
        "dimensions": style_snapshot,
        "atom_predictions": atoms,
        "atom_summary": atom_summary,
        "merged_profile": {
            "dominant_tone": atom_summary.get("tone", "未识别"),
            "dominant_conflict": atom_summary.get("conflict", "未识别"),
            "narrative_style": f"视角: {style_snapshot.get('narrative_perspective',{}).get('label','-')}, "
                              f"节奏: {style_snapshot.get('paragraph_rhythm',{}).get('label','-')}",
        }
    }


# ═══════════════════════════════════════════════════════════════
#  CLI / API Server
# ═══════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Æsir 叙事智能层")
    parser.add_argument('--text', '-t', help='直接输入文本')
    parser.add_argument('--file', '-f', help='输入文本文件路径')
    parser.add_argument('--server', '-s', action='store_true', help='启动 API 服务')
    parser.add_argument('--port', type=int, default=8766, help='API 端口')
    parser.add_argument('--output', '-o', default='', help='输出文件路径')
    args = parser.parse_args()

    text = ""
    source = ""

    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"文件不存在: {args.file}")
            sys.exit(1)
        text = path.read_text(encoding='utf-8', errors='replace')
        source = path.name
    elif args.text:
        text = args.text
        source = "直接输入"
    elif args.server:
        run_server(args.port)
        return
    else:
        print("✦ Æsir 叙事智能层 — 输入文本（Ctrl+D 结束）:")
        text = sys.stdin.read()
        source = "标准输入"

    if not text.strip():
        print("没有输入文本。")
        sys.exit(1)

    result = analyze_text(text, source)

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"结果已写入: {args.output}")
    else:
        print(output)


def run_server(port=8766):
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import urllib.parse
    except ImportError:
        print("需要 Python 标准库 http.server")
        sys.exit(1)

    class IntelHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            path = urllib.parse.urlparse(self.path).path
            if path == '/analyze':
                try:
                    length = int(self.headers.get('Content-Length', 0))
                    body = self.rfile.read(length)
                    data = json.loads(body)
                    text = data.get('text', '')
                    source = data.get('source', 'API 调用')
                    if not text.strip():
                        self._json(400, {"error": "text 不能为空"})
                        return
                    result = analyze_text(text, source)
                    self._json(200, result)
                except Exception as e:
                    self._json(500, {"error": str(e)})
            elif path == '/keywords':
                # 仅返回关键词匹配结果（轻量版本）
                try:
                    length = int(self.headers.get('Content-Length', 0))
                    body = self.rfile.read(length)
                    data = json.loads(body)
                    text = data.get('text', '')
                    if not text.strip():
                        self._json(400, {"error": "text 不能为空"})
                        return
                    keywords = match_keywords(text, top_n=10)
                    self._json(200, {"keywords": keywords})
                except Exception as e:
                    self._json(500, {"error": str(e)})
            elif path == '/health':
                self._json(200, {"status": "ok", "keyword_db_size": len(_FLAT_KW_MAP)})
            else:
                self._json(404, {"error": "not_found"})

        def do_OPTIONS(self):
            self.send_response(200)
            self._cors_headers()
            self.end_headers()

        def _cors_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')

        def _json(self, code, data):
            self.send_response(code)
            self._cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

        def log_message(self, format, *args):
            print(f"  [{self.address_string()}] {format % args}", file=sys.stderr)

    server = HTTPServer(('0.0.0.0', port), IntelHandler)
    print(f"✦ Æsir 叙事智能 API 运行在 http://localhost:{port}")
    print(f"  POST /analyze   — 完整分析（关键词+维度+原子预测）")
    print(f"  POST /keywords  — 仅关键词匹配")
    print(f"  GET  /health    — 健康检查")
    print(f"  关键词库大小: {len(_FLAT_KW_MAP)} 个关键词")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n关闭服务器")
        server.server_close()


if __name__ == "__main__":
    main()
