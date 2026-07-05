"""Æsir 创意引擎适配层——管理创意发散-收敛循环的 bridge"""

import sys, re, time
from pathlib import Path
from typing import Optional

# 导入 Æsir 原子和能力
AESIR_AVAILABLE = False
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / ".."))
    from aesir_mcp_server import (
        TONES, CONFLICTS, PROTAGS, SETTINGS, TURNS, PLEASURE_POINTS,
        ARC_TEMPLATES, EMOTION_CURVES, DRAFT_MODES,
        generate_intent_card, generate_worldline_config,
        content_hash, extract_keywords,
    )
    AESIR_AVAILABLE = True
except ImportError:
    # 如果 Æsir 不可用，使用内联副本保持独立运行
    TONES = ['冷峻写实','温暖治愈','黑色幽默','悬疑暗流','诗意思辨','激烈狂暴']
    CONFLICTS = ['身份冲突','资源冲突','价值观冲突','关系冲突','生存冲突','认知冲突']
    PROTAGS = ['普通人','天选之人','局外人','复仇者','守护者','探索者']
    SETTINGS = ['封闭空间','双界穿梭','旅途','小社会','日常入侵','失落世界']
    TURNS = ['秘密揭露','角色反转','假胜利','外力介入','代价显现','认知升级']
    PLEASURE_POINTS = ['信息差碾压','降维打击','认知颠覆','以牙还牙','绝境反转','身份揭晓','连锁反应','群体震撼','时间魔法','代价转移','规则利用','情感共鸣']
    ARC_TEMPLATES = {"英雄之旅": {"source": "Campbell", "beats": []}}
    EMOTION_CURVES = {t: [0.5]*7 for t in TONES}

    def content_hash(t): h=0;[(h:=((h<<5)-h)+ord(c),h:=abs(h)) for c in t];return h
    def extract_keywords(t): return [w for w in re.split(r'[\s，。！？、；：""''（）《》/]',t) if len(w)>1]
    def generate_intent_card(*a,**k): return {"note": "Æsir 未安装"}
    def generate_worldline_config(*a,**k): return {}


class AesirAdapter:
    """Æsir 创意能力适配器。提供创意发散-收敛-意图设定。"""

    @property
    def available(self) -> bool:
        return AESIR_AVAILABLE

    def get_atoms_info(self) -> dict:
        return {
            "tones": TONES,
            "conflicts": CONFLICTS,
            "protagonists": PROTAGS,
            "settings": SETTINGS,
            "turns": TURNS,
            "pleasure_points": PLEASURE_POINTS,
            "arcs": list(ARC_TEMPLATES.keys()),
        }

    def generate_intent(self, idea: str, tone: str, conflict: str, protagonist: str) -> dict:
        """生成叙事意图卡片"""
        if AESIR_AVAILABLE:
            return generate_intent_card(idea, tone, conflict, protagonist)
        return {
            "core_paradox": f"关于「{idea[:20]}」的矛盾",
            "conflict_level": "人际关系",
            "moral_question": "什么才是正确的？",
        }

    def suggest_arcs(self, idea: str) -> list:
        """根据想法关键词推荐弧线"""
        kw = [w.lower() for w in extract_keywords(idea)]
        arc_keywords = {
            "英雄之旅": ["冒险","旅程","成长","使命","英雄","出发","寻找","命运"],
            "推理揭秘": ["秘密","谜","真相","侦探","悬疑","线索","案件","推理"],
            "情感波澜": ["爱","错过","重逢","关系","感情","心动","失恋"],
            "逆袭流": ["逆袭","打脸","升级","崛起","复仇","碾压","翻身"],
            "救赎之弧": ["救赎","赎罪","罪","宽恕","悔恨","原谅"],
            "重重谜团": ["层层","揭穿","伪装","隐藏","假面","秘密"],
        }
        scores = []
        for name, keywords in arc_keywords.items():
            score = sum(2 for k in keywords if k in idea) + sum(1 for k in keywords if any(k in w for w in kw))
            if score > 0:
                scores.append({"arc": name, "match": score})
        return sorted(scores, key=lambda x: -x["match"]) if scores else [{"arc": a, "match": 0} for a in ARC_TEMPLATES][:3]

    def diverge_worldlines(self, idea: str, preferred_tone: str = "", count: int = 5) -> list:
        """发散世界线"""
        seed = content_hash(idea + str(time.time()))
        wls = []
        for i in range(count - 1):
            tone = TONES[(i * 7 + seed) % len(TONES)]
            if preferred_tone and i < count - 2:
                tone = TONES[(TONES.index(preferred_tone) + i * 7 + seed) % len(TONES)]
            pp = PLEASURE_POINTS[(i * 5 + seed) % len(PLEASURE_POINTS)]
            wl = generate_worldline_config(idea, i, tone, False, "unspecified", pp)
            wls.append(wl)
        # 探索型
        explore_tone = TONES[(seed + 5) % len(TONES)]
        if preferred_tone:
            others = [t for t in TONES if t != preferred_tone]
            explore_tone = others[(seed + 3) % len(others)]
        wls.append(generate_worldline_config(idea, count - 1, explore_tone, True))
        return wls

    def record_constraint(self, history: list, constraint: str) -> list:
        """追加约束记录"""
        history.append({"text": constraint, "round": len(history) + 1, "at": time.strftime("%Y-%m-%dT%H:%M")})
        return history

    def get_arc_template(self, arc_name: str) -> dict:
        """获取弧线模板"""
        return ARC_TEMPLATES.get(arc_name, {})
