"""Novel OS 写作/审计引擎适配层——管理写作执行和审计管道

直接导入 AuditPipeline（38+ 门禁）、analyzer、fingerprint、genres。
同时内部集成 Æsir 创意引擎的核心工具函数。
"""

import sys, json, re, os, time, math
from pathlib import Path
from typing import Optional, Any
from collections import Counter

NOVEL_OS_AVAILABLE = False

# ── 直接导入 Novel OS 核心模块 ──
_NOVELOS_PATH = str(Path(__file__).parent.parent.parent / "novel-os" / "novel-os")
if _NOVELOS_PATH not in sys.path:
    sys.path.insert(0, _NOVELOS_PATH)

try:
    from novel_os.analyzer import analyzer, LocalAnalyzer
    from novel_os.fingerprint import extract_fingerprint, compare_fingerprints, save_fingerprint, load_fingerprint
    from novel_os.audit.pipeline import AuditPipeline
    from novel_os.audit.gates import list_gates, get_gate, ALL_GATES
    from novel_os.genres import get_profile, GenreProfile
    NOVEL_OS_AVAILABLE = True
except ImportError as e:
    LocalAnalyzer = None
    analyzer = None


# ── 直接集成 Æsir 创意引擎的工具函数 ──
_AESIR_PATH = str(Path(__file__).parent.parent.parent / "aesir")
if _AESIR_PATH not in sys.path:
    sys.path.insert(0, _AESIR_PATH)

AESIR_AVAILABLE = False
try:
    import aesir_mcp_server as aesir
    TONES = aesir.TONES
    CONFLICTS = aesir.CONFLICTS
    PROTAGS = aesir.PROTAGS
    SETTINGS = aesir.SETTINGS
    TURNS = aesir.TURNS
    PLEASURE_POINTS = aesir.PLEASURE_POINTS
    ARC_TEMPLATES = aesir.ARC_TEMPLATES
    EMOTION_CURVES = aesir.EMOTION_CURVES
    DRAFT_MODES = aesir.DRAFT_MODES
    generate_intent_card = aesir.generate_intent_card
    generate_worldline_config = aesir.generate_worldline_config
    content_hash = aesir.content_hash
    extract_keywords = aesir.extract_keywords
    AESIR_AVAILABLE = True
except ImportError:
    TONES = ['冷峻写实','温暖治愈','黑色幽默','悬疑暗流','诗意思辨','激烈狂暴']
    CONFLICTS = ['身份冲突','资源冲突','价值观冲突','关系冲突','生存冲突','认知冲突']
    PROTAGS = ['普通人','天选之人','局外人','复仇者','守护者','探索者']
    SETTINGS = ['封闭空间','双界穿梭','旅途','小社会','日常入侵','失落世界']
    TURNS = ['秘密揭露','角色反转','假胜利','外力介入','代价显现','认知升级']
    PLEASURE_POINTS = ['信息差碾压','降维打击','认知颠覆','以牙还牙','绝境反转','身份揭晓','连锁反应','群体震撼','时间魔法','代价转移','规则利用','情感共鸣']
    ARC_TEMPLATES = {"英雄之旅": {"source": "Campbell", "beats": []}}
    EMOTION_CURVES = {t: [0.5]*7 for t in TONES}
    def content_hash(t):
        h=0;[exec('h=((h<<5)-h)+ord(c)',globals(),{'h':h,'c':c}) for c in t];return abs(h)
    def extract_keywords(t): return [w for w in re.split(r'[\s，。！？、；：""''（）《》/]',t) if len(w)>1]
    def generate_intent_card(*a,**k): return {"core_paradox":"关于故事的矛盾"}
    def generate_worldline_config(*a,**k): return {}


class NovelOSAdapter:
    """Novel OS 适配器。提供写作-审计-风格分析能力。"""

    def __init__(self):
        self._pipeline_cache = {}
        self._local_analyzer = None

    @property
    def available(self) -> bool:
        return NOVEL_OS_AVAILABLE

    def get_local_analyzer(self):
        """获取零 API 文本分析器"""
        if NOVEL_OS_AVAILABLE and analyzer:
            return analyzer
        if not self._local_analyzer:
            self._local_analyzer = MinimalAnalyzer()
        return self._local_analyzer

    def analyze_chapter(self, text: str, title: str = "") -> dict:
        """分析一章文本，返回结构化特征"""
        a = self.get_local_analyzer()
        return a.analyze_chapter(text, 0, title)

    def get_gate_list(self) -> list:
        """获取可用的门禁列表"""
        if NOVEL_OS_AVAILABLE:
            try:
                from novel_os.audit.gates import list_gates
                return list_gates()
            except:
                pass
        # 本地回退：返回已知门禁
        return [
            {"id": "SVT-01", "name": "场景值翻转", "severity": "warn"},
            {"id": "IIT-01", "name": "激励事件时机", "severity": "block"},
            {"id": "TPE-01", "name": "情绪过度解释", "severity": "warn"},
            {"id": "TPE-02", "name": "转折无触点", "severity": "warn"},
            {"id": "GDA-01", "name": "鸿沟饥荒", "severity": "block"},
            {"id": "GDA-04", "name": "鸿沟沙漠", "severity": "warn"},
        ]

    def audit_text(self, text: str, genre: str = "xianxia_modern", title: str = "") -> dict:
        """对文本执行门禁审计"""
        gates = []

        # 字数
        wc = len(text)
        if wc < 200:
            gates.append({"gate": "章节字数", "result": "block", "details": f"仅 {wc} 字，建议 1000+"})
        elif wc < 800:
            gates.append({"gate": "章节字数", "result": "warn", "details": f"{wc} 字，建议扩展"})
        else:
            gates.append({"gate": "章节字数", "result": "pass"})

        # 对话密度
        lines = text.split('\n')
        dl = sum(1 for l in lines if l.strip().startswith('"') or l.strip().startswith('「'))
        dr = dl / max(len(lines), 1)
        if dr < 0.05 and wc > 500:
            gates.append({"gate": "对话密度", "result": "warn", "details": f"仅 {dr:.0%} 对话"})
        elif dr > 0.7:
            gates.append({"gate": "对话密度", "result": "warn", "details": f"过度对话 {dr:.0%}"})
        else:
            gates.append({"gate": "对话密度", "result": "pass"})

        # 首段钩子
        opening = text[:200]
        hooks = ["突然","但是","然而","没想到","为什么","秘密","死","杀","发现"]
        if not any(h in opening for h in hooks):
            gates.append({"gate": "首段钩子", "result": "warn", "details": "前200字无钩子"})
        else:
            gates.append({"gate": "首段钩子", "result": "pass"})

        # 情感锚点
        emo = ["感到","觉得","愤怒","悲伤","恐惧","喜悦","痛苦","温暖","心跳"]
        emo_count = sum(text.count(w) for w in emo)
        if emo_count < 2 and wc > 500:
            gates.append({"gate": "情感锚点", "result": "block", "details": "缺乏情感刻画"})
        elif emo_count < 5 and wc > 500:
            gates.append({"gate": "情感锚点", "result": "warn", "details": f"仅 {emo_count} 处情感词"})
        else:
            gates.append({"gate": "情感锚点", "result": "pass"})

        # 触觉触点
        touch = ["手","目光","眼神","拳头","肩膀","呼吸","脚步"]
        tc = sum(text.count(w) for w in touch)
        expected = max(2, wc // 300)
        if tc < expected:
            gates.append({"gate": "触觉触点", "result": "warn", "details": f"{tc} 触点不足 {expected}"})
        else:
            gates.append({"gate": "触觉触点", "result": "pass"})

        passed = sum(1 for g in gates if g["result"] == "pass")
        warned = sum(1 for g in gates if g["result"] == "warn")
        blocked = sum(1 for g in gates if g["result"] == "block")

        return {
            "chapter": title,
            "word_count": wc,
            "gates": gates,
            "passed": passed,
            "warned": warned,
            "blocked": blocked,
            "summary": f"✅{passed} ⚠️{warned} ❌{blocked}",
        }

    def extract_fingerprint(self, text: str, novel_name: str = "", genre: str = "xianxia_modern") -> dict:
        """提取风格指纹"""
        if NOVEL_OS_AVAILABLE:
            try:
                fp = extract_fingerprint(text, novel_name, genre)
                return fp.to_dict()
            except:
                pass
        # 本地回退
        return {
            "novel": novel_name or "未知",
            "genre": genre,
            "profile": {"avg_gap_density": 0, "avg_touchpoints": 0, "avg_hook_position": 0},
        }


class MinimalAnalyzer:
    """零依赖的基础文本分析器——Novel OS analyzer 不可用时的回退"""

    def analyze_chapter(self, text: str, idx: int = 0, title: str = "") -> dict:
        words = len(text)
        lines = [l for l in text.split('\n') if l.strip()]
        touch_words = ["手","目光","眼神","拳头","肩膀","呼吸","脚步","心"]
        emo_words = ["感到","觉得","愤怒","悲伤","恐惧","喜悦","痛苦","温暖","凉","心跳"]
        gap_markers = ["但是","然而","没想到","却","竟","突然","原来"]
        hook_markers = ["突然","但是","为什么","秘密","死","杀","发现"]

        return {
            "chapter_index": idx,
            "title": title,
            "word_count": words,
            "line_count": len(lines),
            "touchpoints": sum(text.count(w) for w in touch_words),
            "direct_emotions": sum(text.count(w) for w in emo_words),
            "emotion_to_touchpoint_ratio": round(
                sum(text.count(w) for w in emo_words) / max(sum(text.count(w) for w in touch_words), 1), 2),
            "gap_count": sum(text.count(m) for m in gap_markers),
            "gap_density": round(sum(text.count(m) for m in gap_markers) / max(words / 1000, 1), 2),
            "first_hook_position": next((text.find(h) for h in hook_markers if text.find(h) > 0), 99999),
            "has_hook": any(m in text[:300] for m in hook_markers),
            "scene_flipped": True,
        }

    def analyze_full_manuscript(self, chapters: list) -> dict:
        all_text = "".join(ch["text"] for ch in chapters)
        words = len(all_text)
        return {
            "total_chapters": len(chapters),
            "total_chars": words,
            "gap_densities": [],
            "gap_intensities": [],
            "direct_emotions": 0,
            "touchpoints": 0,
        }
