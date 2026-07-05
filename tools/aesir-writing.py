"""aesir-writing — 创意→写作→审计：完整闭环编排引擎

整合 Æsir（创意/发散/收敛）+ Novel OS（写作/审计/指纹）
三个独立项目通过 Story 数据对象对接。

架构：
                    ┌──────────────────┐
                    │   aesir-writing   │
                    │   编排引擎        │
                    └──┬────┬────┬─────┘
                       │    │    │
              ┌────────┘    │    └──────────┐
              ▼             ▼               ▼
      ┌────────────┐ ┌───────────┐ ┌──────────────┐
      │    Æsir    │ │ StoryStore │ │   Novel OS   │
      │  创意引擎   │ │ 故事仓库   │ │ 审计/写作引擎 │
      └────────────┘ └───────────┘ └──────────────┘

运行：
  python aesir-writing.py                     # 交互模式
  python aesir-writing.py --story my_story    # 继续已有故事
  python aesir-writing.py --mcp               # MCP Server 模式
"""

import json, os, re, time, uuid, sys, copy
from pathlib import Path
from datetime import datetime
from typing import Optional, Any

# ═══════════════════════════════════════════════════════════════
#  配置
# ═══════════════════════════════════════════════════════════════

STORIES_DIR = Path.home() / ".aesir-writing" / "stories"
STORIES_DIR.mkdir(parents=True, exist_ok=True)

DRAFT_MODES = {
    "first": "第一稿：写给自己，允许粗糙，目标是写完",
    "revision": "修改稿：写给读者，砍废话，推动故事",
    "polish": "精修稿：打磨语言，感官细节饱满",
}

AUDIT_LEVELS = {
    "pass": "✅ 通过",
    "warn": "⚠️ 建议优化",
    "block": "❌ 需要重写",
}

# ═══════════════════════════════════════════════════════════════
#  核心数据模型：Story
# ═══════════════════════════════════════════════════════════════

class Story:
    """完整的故事对象——贯穿创意到成品的所有阶段"""

    def __init__(self, idea: str = ""):
        self.id: str = uuid.uuid4().hex[:12]
        self.idea: str = idea
        self.original_idea: str = idea
        self.created_at: str = datetime.now().isoformat()
        self.updated_at: str = self.created_at
        self.status: str = "ideation"  # ideation | diverging | converging | drafting | auditing | revising | done

        # 创意阶段
        self.intent_card: dict = {}           # 叙事意图卡片
        self.arc_name: str = ""               # 选中的弧线类型
        self.worldlines: list = []            # 发散的世界线
        self.chosen_worldline: dict = {}      # 用户选中的世界线
        self.constraint_history: list = []    # 多轮约束记录
        self.clarify_answers: list = []       # 驯化问答

        # 写作阶段
        self.draft_mode: str = "first"
        self.chapters: list = []              # [{title, text, created_at, analysis}]
        self.current_outline: list = []       # 节拍大纲 [{beat, summary}]

        # 审计阶段
        self.audit_history: list = []         # [{gate, result, chapter_index, timestamp}]
        self.style_fingerprint: dict = {}     # Novel OS 风格指纹
        self.last_audit_summary: str = ""

        # 元数据
        self.version: int = 1

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, data: dict):
        s = cls(data.get("idea", ""))
        for k, v in data.items():
            setattr(s, k, v)
        return s

    def save(self, path: Optional[Path] = None):
        path = path or (STORIES_DIR / f"{self.id}.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding='utf-8')
        self.updated_at = datetime.now().isoformat()

    @classmethod
    def load(cls, story_id: str) -> Optional['Story']:
        path = STORIES_DIR / f"{story_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding='utf-8'))
        return cls.from_dict(data)

    @classmethod
    def list_all(cls) -> list[dict]:
        if not STORIES_DIR.exists():
            return []
        stories = []
        for f in sorted(STORIES_DIR.glob("*.json"), key=os.path.getmtime, reverse=True):
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                stories.append({
                    "id": data.get("id", f.stem),
                    "idea": data.get("idea", "")[:60],
                    "status": data.get("status", ""),
                    "updated_at": data.get("updated_at", ""),
                    "chapter_count": len(data.get("chapters", [])),
                    "version": data.get("version", 1),
                })
            except:
                pass
        return stories

    def add_chapter(self, title: str, text: str, analysis: dict = None):
        self.chapters.append({
            "index": len(self.chapters) + 1,
            "title": title,
            "text": text,
            "analysis": analysis or {},
            "created_at": datetime.now().isoformat(),
        })
        self.version += 1
        self.save()

    def add_audit(self, gate: str, result: str, chapter_index: int, details: str = ""):
        self.audit_history.append({
            "gate": gate,
            "result": result,
            "chapter_index": chapter_index,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        })
        self.save()

    def summary(self) -> str:
        """返回故事的简洁状态摘要"""
        wc = sum(len(c["text"]) for c in self.chapters)
        audit_pass = len([a for a in self.audit_history if a["result"] == "pass"])
        audit_block = len([a for a in self.audit_history if a["result"] == "block"])
        return (
            f"「{self.idea[:40]}」\n"
            f"  状态: {self.status} | 弧线: {self.arc_name or '未选择'}\n"
            f"  章节: {len(self.chapters)} 章 | 总字数: {wc}\n"
            f"  审计: {audit_pass} ✅ / {audit_block} ❌\n"
            f"  版本: v{self.version} | 约束轮次: {len(self.constraint_history)}"
        )


# ═══════════════════════════════════════════════════════════════
#  编排引擎
# ═══════════════════════════════════════════════════════════════

class AesirWriting:
    """编排引擎——管理创意→写作→审计的完整闭环"""

    def __init__(self):
        self.story: Optional[Story] = None
        self._novel_os_available = self._check_novel_os()

    def _check_novel_os(self) -> bool:
        """检查 Novel OS 是否可导入"""
        try:
            import importlib
            # 尝试作为独立进程调用
            result = os.system("novel-os --help 2>/dev/null")
            return result == 0
        except:
            return False

    # ─── 故事管理 ───────────────────────────────────

    def create_story(self, idea: str) -> Story:
        self.story = Story(idea)
        self.story.save()
        return self.story

    def load_story(self, story_id: str) -> Optional[Story]:
        self.story = Story.load(story_id)
        return self.story

    def list_stories(self) -> list[dict]:
        return Story.list_all()

    def switch_story(self, story_id: str) -> Optional[Story]:
        return self.load_story(story_id)

    # ─── 创意阶段 ───────────────────────────────────

    def set_intent(self, tone: str, conflict: str, protagonist: str, arc_name: str):
        """设定叙事意图——发散之前调用"""
        s = self.story
        if not s:
            return {"error": "没有活动的故事"}
        s.arc_name = arc_name
        s.intent_card = {
            "tone": tone,
            "conflict": conflict,
            "protagonist": protagonist,
            "core_paradox": f"关于「{s.idea[:20]}」的矛盾",
            "moral_question": "什么才是正确的选择？",
        }
        s.status = "ideation"
        s.save()

        # 建议弧线模板
        return self.get_arc_suggestions()

    def get_arc_suggestions(self) -> list[dict]:
        """根据当前意图推荐弧线模板"""
        from aesir_mcp_server import ARC_TEMPLATES
        s = self.story
        if not s:
            return [{"error": "没有活动的故事"}]

        suggestions = []
        kw = [w for w in re.split(r'[\s，。！？、；：""''（）《》/]', s.idea) if len(w) > 1]

        # 关键词匹配弧线
        arc_keywords = {
            "英雄之旅": ["冒险", "旅程", "成长", "使命", "英雄"],
            "推理揭秘": ["秘密", "谜", "真相", "侦探", "悬疑"],
            "情感波澜": ["爱", "关系", "感情", "重逢", "错过"],
            "逆袭流": ["逆袭", "崛起", "打脸", "升级", "复仇"],
            "救赎之弧": ["救赎", "罪", "赎罪", "宽恕", "悔"],
            "重重谜团": ["层层", "揭穿", "假面", "伪装", "隐藏"],
        }

        for arc_name, keywords in arc_keywords.items():
            score = sum(1 for kw in keywords if any(k in s.idea for k in kw))
            if score > 0:
                suggestions.append({"arc": arc_name, "match": score})

        return sorted(suggestions, key=lambda x: -x["match"]) if suggestions else list(ARC_TEMPLATES.keys())[:3]

    def record_constraint(self, constraint: str):
        """记录一轮约束"""
        s = self.story
        if not s:
            return {"error": "没有活动的故事"}
        s.constraint_history.append({
            "text": constraint,
            "round": len(s.constraint_history) + 1,
            "timestamp": datetime.now().isoformat(),
        })
        s.save()
        return {"round": len(s.constraint_history), "history": [c["text"] for c in s.constraint_history]}

    # ─── 写作阶段 ───────────────────────────────────

    def start_drafting(self, draft_mode: str = "first"):
        """进入写作阶段——基于世界线开始写"""
        s = self.story
        if not s:
            return {"error": "没有活动的故事"}
        s.draft_mode = draft_mode
        s.status = "drafting"
        s.save()
        return {
            "story_id": s.id,
            "arc": s.arc_name,
            "draft_mode": draft_mode,
            "draft_principle": DRAFT_MODES.get(draft_mode, ""),
            "chapters_to_write": self._estimate_chapters(),
            "suggestion": "先写完全部初稿，不要回头修改。第一稿写给自己。"
        }

    def add_written_chapter(self, title: str, text: str):
        """保存一章写好的内容"""
        s = self.story
        if not s:
            return {"error": "没有活动的故事"}
        s.add_chapter(title, text)
        return {
            "chapter": len(s.chapters),
            "word_count": len(text),
            "total_chapters": len(s.chapters),
        }

    def _estimate_chapters(self) -> int:
        """根据弧线节拍估算章节数"""
        from aesir_mcp_server import ARC_TEMPLATES
        s = self.story
        arc = ARC_TEMPLATES.get(s.arc_name)
        if arc:
            return len(arc["beats"])
        return 10

    # ─── 审计阶段 ───────────────────────────────────

    def audit_chapter(self, chapter_index: int = -1, genre: str = "xianxia_modern") -> dict:
        """审计指定章节——调用 Novel OS analyzer"""
        s = self.story
        if not s or not s.chapters:
            return {"error": "没有可审计的章节"}

        if chapter_index == -1:
            chapter_index = len(s.chapters) - 1

        ch = s.chapters[chapter_index]
        text = ch["text"]

        # 本地启发式审计（不依赖 Novel OS）
        gates = self._run_local_gates(text, ch["title"], chapter_index, genre)

        # 记录审计结果
        passed = 0
        warned = 0
        blocked = 0
        for g in gates:
            s.add_audit(g["gate"], g["result"], chapter_index, g.get("details", ""))
            if g["result"] == "pass":
                passed += 1
            elif g["result"] == "warn":
                warned += 1
            else:
                blocked += 1

        # 生成审计摘要
        summary = (
            f"第 {chapter_index+1} 章「{ch['title']}」审计结果：\n"
            f"  通过 {passed} ⚠️ 建议 {warned} ❌ 重写 {blocked}\n"
        )
        for g in gates:
            if g["result"] != "pass":
                summary += f"  {g['gate']}: {g.get('details', '')}\n"
        s.last_audit_summary = summary
        s.save()

        return {
            "chapter": chapter_index + 1,
            "title": ch["title"],
            "gates": gates,
            "summary": summary,
            "word_count": len(text),
            "passed": passed,
            "warned": warned,
            "blocked": blocked,
        }

    def _run_local_gates(self, text: str, title: str, chapter_index: int, genre: str) -> list[dict]:
        """零 API 本地门禁审计——纯启发式规则"""
        gates = []
        lines = text.split('\n')
        paragraphs = [p for p in text.split('\n\n') if p.strip()]

        # 1. 字数门禁
        wc = len(text)
        if wc < 200:
            gates.append({"gate": "章节字数", "result": "block", "details": f"仅 {wc} 字，建议至少 1000 字"})
        elif wc < 800:
            gates.append({"gate": "章节字数", "result": "warn", "details": f"{wc} 字，建议扩展到 1000+"})
        else:
            gates.append({"gate": "章节字数", "result": "pass", "details": f"{wc} 字"})

        # 2. 对话密度
        dialogue_lines = sum(1 for l in lines if l.strip().startswith('"') or l.strip().startswith('「'))
        dialogue_ratio = dialogue_lines / max(len(lines), 1)
        if dialogue_ratio < 0.05 and wc > 500:
            gates.append({"gate": "对话密度", "result": "warn", "details": f"对话占比仅 {dialogue_ratio:.0%}，建议增加对话"})
        elif dialogue_ratio > 0.7:
            gates.append({"gate": "对话密度", "result": "warn", "details": f"对话占比 {dialogue_ratio:.0%}，注意平衡叙事"})
        else:
            gates.append({"gate": "对话密度", "result": "pass", "details": f"{dialogue_ratio:.0%}"})

        # 3. 触觉触点
        touch_kw = ["手", "目光", "眼神", "沉默", "拳头", "指节", "肩膀", "呼吸", "心", "脚步"]
        touch_count = sum(text.count(kw) for kw in touch_kw)
        expected = max(2, int(wc / 300))
        if touch_count < expected:
            gates.append({"gate": "触觉触点", "result": "warn", "details": f"触点 {touch_count} 次，建议至少 {expected} 次"})
        else:
            gates.append({"gate": "触觉触点", "result": "pass", "details": f"{touch_count} 次"})

        # 4. 首段钩子（前200字内是否有悬念/冲突信号）
        opening = text[:200]
        hook_signals = ["突然", "但是", "然而", "没想到", "为什么", "什么", "秘密", "死", "杀", "追", "逃"]
        has_hook = any(s in opening for s in hook_signals)
        if not has_hook:
            gates.append({"gate": "首段钩子", "result": "warn", "details": "前200字没有明显的悬念或冲突信号"})
        else:
            gates.append({"gate": "首段钩子", "result": "pass", "details": "钩子已部署"})

        # 5. 情感锚点
        emotion_words = ["感到", "觉得", "愤怒", "悲伤", "恐惧", "喜悦", "痛苦", "温暖", "凉", "心跳"]
        emotion_count = sum(text.count(w) for w in emotion_words)
        if emotion_count < 2 and wc > 500:
            gates.append({"gate": "情感锚点", "result": "block", "details": "几乎没有情感刻画，读者无法共情"})
        elif emotion_count < 5 and wc > 500:
            gates.append({"gate": "情感锚点", "result": "warn", "details": f"只检测到 {emotion_count} 处情感词"})
        else:
            gates.append({"gate": "情感锚点", "result": "pass", "details": f"{emotion_count} 处"})

        # 6. 场景值翻转
        third = len(text) // 3
        first_val = sum(text[:third].count(w) for w in ["希望", "爱", "勇敢", "信任", "自由"])
        last_val = sum(text[-third:].count(w) for w in ["绝望", "恨", "背叛", "死亡", "束缚"])
        if abs(first_val - last_val) < 2 and wc > 800:
            gates.append({"gate": "场景值翻转", "result": "warn", "details": "开头和结尾的情感强度变化不大"})
        else:
            gates.append({"gate": "场景值翻转", "result": "pass", "details": f"变化量: {abs(first_val - last_val)}"})

        # 7. 结尾断章
        last_line = [l for l in lines if l.strip()][-1] if lines else ""
        cliffhanger_signals = ["?", "！", "突然", "原来", "竟然是", "发现"]
        has_cliff = any(s in last_line for s in cliffhanger_signals)
        if has_cliff:
            gates.append({"gate": "结尾断章", "result": "pass", "details": "以悬念结尾"})
        else:
            gates.append({"gate": "结尾断章", "result": "warn", "details": "结尾可以考虑埋下悬念或钩子"})

        # 8. 段落长度均匀性
        if paragraphs:
            para_lengths = [len(p) for p in paragraphs]
            avg = sum(para_lengths) / len(para_lengths)
            long_paras = sum(1 for p in para_lengths if p > avg * 2)
            if long_paras > len(para_lengths) * 0.3:
                gates.append({"gate": "段落节奏", "result": "warn", "details": f"有 {long_paras} 个段落明显过长"})
            else:
                gates.append({"gate": "段落节奏", "result": "pass", "details": "段落分布均匀"})
        else:
            gates.append({"gate": "段落节奏", "result": "warn", "details": "没有可分析的段落"})

        return gates

    def get_audit_summary(self, story_id: Optional[str] = None) -> str:
        """获取完整审计总结"""
        s = self.story
        if not s:
            return "没有活动的故事"
        return s.last_audit_summary or "尚未进行审计"

    # ─── 闭环反馈 ───────────────────────────────────

    def generate_revision_suggestions(self) -> list[dict]:
        """从审计结果生成修改建议——驱动闭环反馈"""
        s = self.story
        if not s:
            return [{"error": "没有活动的故事"}]

        blocks = [a for a in s.audit_history if a["result"] == "block"]
        warns = [a for a in s.audit_history if a["result"] == "warn"]

        suggestions = []
        if blocks:
            for b in blocks[:3]:
                suggestions.append({
                    "priority": "high",
                    "issue": b["details"],
                    "suggestion": f"重新收敛第 {b['chapter_index']+1} 章，标记约束：修复「{b['gate']}」",
                    "action": "reconverge",
                })
        if warns:
            for w in warns[:3]:
                suggestions.append({
                    "priority": "medium",
                    "issue": w["details"],
                    "suggestion": f"修改第 {w['chapter_index']+1} 章——{w['gate']}需要优化",
                    "action": "revise",
                })
        if not blocks and not warns:
            suggestions.append({
                "priority": "low",
                "issue": "所有门禁通过",
                "suggestion": "可以进入下一阶段的创作或精修",
                "action": "proceed",
            })

        return suggestions

    def get_full_story_status(self) -> str:
        """完整的故事状态摘要"""
        s = self.story
        if not s:
            return "没有活动的故事"

        wc = sum(len(c["text"]) for c in s.chapters)
        audit_stats = {"pass": 0, "warn": 0, "block": 0}
        for a in s.audit_history:
            audit_stats[a["result"]] = audit_stats.get(a["result"], 0) + 1

        status = (
            f"═══════════════════════════════════\n"
            f"  📖 {s.idea[:60]}\n"
            f"  ─────────────────────────────────\n"
            f"  阶段: {s.status}  弧线: {s.arc_name or '未选择'}\n"
            f"  草稿: {DRAFT_MODES.get(s.draft_mode, s.draft_mode)}\n"
            f"  章节: {len(s.chapters)} 章  字数: {wc}\n"
            f"  审计: ✅{audit_stats['pass']} ⚠️{audit_stats['warn']} ❌{audit_stats['block']}\n"
            f"  版本: v{s.version}  约束轮次: {len(s.constraint_history)}\n"
            f"  创建: {s.created_at[:16]}\n"
            f"═══════════════════════════════════"
        )
        return status


# ═══════════════════════════════════════════════════════════════
#  CLI 交互模式
# ═══════════════════════════════════════════════════════════════

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    print(f"\n  ═══ {title} ═══\n")

def print_menu():
    print("\n  ── 操作 ──")
    print("  1. 新想法        2. 选择故事      3. 查看当前故事")
    print("  4. 设定意图      5. 加约束        6. 进入写作")
    print("  7. 写一章节      8. 审计章节      9. 闭环反馈")
    print("  l. 列出所有故事  s. 保存          q. 退出\n")

def run_interactive():
    engine = AesirWriting()
    current_menu = "main"

    # 命令行参数：直接加载指定故事
    if "--story" in sys.argv:
        idx = sys.argv.index("--story")
        if idx + 1 < len(sys.argv):
            engine.load_story(sys.argv[idx + 1])

    clear_screen()
    print("  ✦ Æsir Writing — 创意→写作→审计 完整闭环")
    print("  ═" * 35)

    while True:
        if engine.story:
            print(f"\n  📖 当前: {engine.story.idea[:50]} | {engine.story.status} | v{engine.story.version}")

        print_menu()
        cmd = input("  > ").strip().lower()

        if cmd in ("q", "quit", "exit"):
            print("\n  ✦ 再见\n")
            break

        elif cmd == "1":
            clear_screen()
            idea = input("  ✎ 模糊想法: ").strip()
            if idea:
                engine.create_story(idea)
                print(f"  ✓ 故事已创建: {engine.story.id}")
                print("  下一步：设定叙事意图（选4）")

        elif cmd == "2":
            stories = engine.list_stories()
            if not stories:
                print("  (没有故事)")
                continue
            print_header("选择故事")
            for i, s in enumerate(stories):
                print(f"  {i+1}. {s['idea']} [{s['status']}] v{s['version']} — {s['chapter_count']}章")
            idx = input("\n  编号: ").strip()
            try:
                sid = stories[int(idx)-1]["id"]
                s = engine.load_story(sid)
                if s:
                    print(f"  ✓ 已加载: {s.idea[:50]}")
            except:
                print("  ❌ 无效")

        elif cmd == "3":
            if not engine.story:
                print("  (没有活动的故事)")
                continue
            clear_screen()
            print(engine.get_full_story_status())

        elif cmd == "4":
            if not engine.story:
                print("  请先创建或选择故事")
                continue
            from aesir_mcp_server import TONES, CONFLICTS, PROTAGS, ARC_TEMPLATES
            print_header("叙事意图设定")
            print("  调性:")
            for i, t in enumerate(TONES):
                print(f"    {i+1}. {t}")
            ti = int(input("  选择: ") or "1") - 1
            tone = TONES[max(0, min(len(TONES)-1, ti))]

            print("  冲突:")
            for i, c in enumerate(CONFLICTS):
                print(f"    {i+1}. {c}")
            ci = int(input("  选择: ") or "1") - 1
            conflict = CONFLICTS[max(0, min(len(CONFLICTS)-1, ci))]

            print("  弧线:")
            arc_names = list(ARC_TEMPLATES.keys())
            for i, a in enumerate(arc_names):
                print(f"    {i+1}. {a}")
            ai = int(input("  选择: ") or "1") - 1
            arc = arc_names[max(0, min(len(arc_names)-1, ai))]

            result = engine.set_intent(tone, conflict, "探索者", arc)
            print(f"  ✓ 意图已设定: {tone} / {conflict} / {arc}")
            print(f"  匹配弧线: {result}")

        elif cmd == "5":
            if not engine.story:
                print("  请先创建或选择故事")
                continue
            constraint = input("  约束: ").strip()
            if constraint:
                result = engine.record_constraint(constraint)
                print(f"  ✓ 第 {result['round']} 轮约束已记录")

        elif cmd == "6":
            if not engine.story:
                print("  请先创建或选择故事")
                continue
            print_header("进入写作阶段")
            print("  草稿模式:")
            for k, v in DRAFT_MODES.items():
                print(f"    {k}: {v}")
            dm = input("  选择 (first/revision/polish): ").strip() or "first"
            result = engine.start_drafting(dm)
            print(f"  ✓ {result['draft_principle']}")
            print(f"  预计 {result['chapters_to_write']} 节")

        elif cmd == "7":
            if not engine.story:
                print("  请先创建或选择故事")
                continue
            if engine.story.status not in ("drafting", "revising", "auditing"):
                print("  请先进入写作阶段（选6）")
                continue
            title = input(f"  第 {len(engine.story.chapters)+1} 章标题: ").strip() or f"第{len(engine.story.chapters)+1}章"
            print("  正文（输入 .end 结束，.save 保存）:")
            lines = []
            while True:
                line = input()
                if line.strip() == ".end":
                    break
                if line.strip() == ".save":
                    break
                lines.append(line)
            text = "\n".join(lines)
            if text.strip():
                result = engine.add_written_chapter(title, text)
                print(f"  ✓ 第 {result['chapter']} 章已保存 ({result['word_count']} 字)")

        elif cmd == "8":
            if not engine.story or not engine.story.chapters:
                print("  没有可审计的章节")
                continue
            ci = input(f"  章节编号 (1-{len(engine.story.chapters)}，回车=最新): ").strip()
            idx = int(ci) - 1 if ci else -1
            result = engine.audit_chapter(idx)
            print(f"\n{result['summary']}")

        elif cmd == "9":
            if not engine.story:
                print("  没有活动的故事")
                continue
            suggestions = engine.generate_revision_suggestions()
            print_header("闭环反馈")
            for s in suggestions:
                priority_tag = "🔴" if s["priority"] == "high" else "🟡" if s["priority"] == "medium" else "🟢"
                print(f"  {priority_tag} [{s['action']}] {s['suggestion']}")

        elif cmd == "l":
            stories = engine.list_stories()
            if not stories:
                print("  (没有故事)")
                continue
            print_header("所有故事")
            for s in stories:
                print(f"  {s['id'][:8]} | {s['idea']} | {s['status']} | {s['chapter_count']}章 | {s['updated_at'][:16]}")

        elif cmd == "s":
            if engine.story:
                engine.story.save()
                print(f"  ✓ 已保存")

        else:
            print("  ❌ 未知指令")


# ═══════════════════════════════════════════════════════════════
#  MCP Server 模式
# ═══════════════════════════════════════════════════════════════

def run_mcp():
    """作为 MCP Server 运行——供 agent 编排调用"""
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import Tool, TextContent
        import asyncio
    except ImportError:
        print("需要: pip install mcp")
        sys.exit(1)

    engine = AesirWriting()

    server = Server("aesir-writing")

    @server.list_tools()
    async def list_tools():
        return [
            Tool(name="create_story", description="创建新故事", inputSchema={"type":"object","properties":{"idea":{"type":"string"}},"required":["idea"]}),
            Tool(name="set_intent", description="设定叙事意图", inputSchema={"type":"object","properties":{"story_id":{"type":"string"},"tone":{"type":"string","enum":["冷峻写实","温暖治愈","黑色幽默","悬疑暗流","诗意思辨","激烈狂暴"]},"conflict":{"type":"string","enum":["身份冲突","资源冲突","价值观冲突","关系冲突","生存冲突","认知冲突"]},"arc_name":{"type":"string","description":"弧线类型"}},"required":["story_id","tone","conflict","arc_name"]}),
            Tool(name="add_chapter", description="添加一章节", inputSchema={"type":"object","properties":{"story_id":{"type":"string"},"title":{"type":"string"},"text":{"type":"string"}},"required":["story_id","title","text"]}),
            Tool(name="audit_chapter", description="审计一章节", inputSchema={"type":"object","properties":{"story_id":{"type":"string"},"chapter_index":{"type":"integer","description":"章节索引（0开始，-1=最新）"}},"required":["story_id"]}),
            Tool(name="get_feedback", description="获取闭环反馈", inputSchema={"type":"object","properties":{"story_id":{"type":"string"}},"required":["story_id"]}),
            Tool(name="list_stories", description="列出所有故事", inputSchema={"type":"object","properties":{}}),
            Tool(name="get_status", description="获取故事状态", inputSchema={"type":"object","properties":{"story_id":{"type":"string"}},"required":["story_id"]}),
        ]

    @server.call_tool()
    async def call_tool(name: str, args: dict) -> list:
        r = lambda d: [TextContent(type="text", text=json.dumps(d, ensure_ascii=False))]
        try:
            if name == "create_story":
                engine.create_story(args["idea"])
                return r({"story_id": engine.story.id, "idea": args["idea"]})
            elif name == "set_intent":
                engine.load_story(args["story_id"])
                engine.set_intent(args["tone"], args["conflict"], "探索者", args["arc_name"])
                return r({"status": "ok", "intent": f"{args['tone']}/{args['conflict']}/{args['arc_name']}"})
            elif name == "add_chapter":
                engine.load_story(args["story_id"])
                engine.story.status = "drafting"
                engine.add_written_chapter(args["title"], args["text"])
                return r({"chapter": len(engine.story.chapters), "words": len(args["text"])})
            elif name == "audit_chapter":
                engine.load_story(args["story_id"])
                result = engine.audit_chapter(args.get("chapter_index", -1))
                return r(result)
            elif name == "get_feedback":
                engine.load_story(args["story_id"])
                suggestions = engine.generate_revision_suggestions()
                return r({"suggestions": suggestions, "summary": engine.story.last_audit_summary})
            elif name == "list_stories":
                return r(engine.list_stories())
            elif name == "get_status":
                engine.load_story(args["story_id"])
                return r({"summary": engine.get_full_story_status(), "story": engine.story.to_dict()})
        except Exception as e:
            return r({"error": str(e)})
        return r({"error": f"unknown tool: {name}"})

    print("✦ Æsir Writing MCP Server 启动", file=sys.stderr)
    asyncio.run(server.run(stdio_server()))


# ═══════════════════════════════════════════════════════════════
#  入口
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if "--mcp" in sys.argv:
        run_mcp()
    else:
        run_interactive()
