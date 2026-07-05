"""编排引擎——创意→写作→审计 完整闭环调度"""

import json, time, copy
from pathlib import Path
from typing import Optional

from .story import StoryModel
from .workflows.ideation import IdeationWorkflow
from .workflows.drafting import DraftingWorkflow
from .workflows.audit import AuditWorkflow


STORIES_DIR = Path(__file__).parent.parent / "stories"
STORIES_DIR.mkdir(parents=True, exist_ok=True)


# StoryModel 的持久化方法需要动态添加
def _story_save(self) -> Path:
    path = STORIES_DIR / f"{self.id}.json"
    path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    self.updated_at = datetime.now().isoformat()
    return path

def _story_load(story_id: str) -> Optional[StoryModel]:
    path = STORIES_DIR / f"{story_id}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding='utf-8'))
    return StoryModel.from_dict(data)

def _story_list_all() -> list:
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

import os as _os
StoryModel.save = _story_save
StoryModel.load = staticmethod(_story_load)
StoryModel.list_all = staticmethod(_story_list_all)


class Orchestrator:
    """编排引擎——管理故事从创意到成品的完整生命周期"""

    def __init__(self):
        self.ideation = IdeationWorkflow()
        self.drafting = DraftingWorkflow()
        self.audit = AuditWorkflow()
        self._current: Optional[StoryModel] = None

    # ─── 故事管理 ─────────────────────────────

    @property
    def current(self) -> Optional[StoryModel]:
        return self._current

    def create(self, idea: str) -> StoryModel:
        s = StoryModel(idea)
        s.save()
        self._current = s
        return s

    def load(self, story_id: str) -> Optional[StoryModel]:
        s = StoryModel.load(story_id)
        if s:
            self._current = s
        return s

    def list_all(self) -> list:
        return StoryModel.list_all()

    # ─── 创意阶段 ─────────────────────────────

    def start_ideation(self, idea: str) -> dict:
        """开始一个新创意"""
        story = self.create(idea)
        result = self.ideation.run(story)
        story.save()
        return {"story_id": story.id, **result}

    def diverge(self, preferred_tone: str = "") -> list:
        """发散世界线"""
        if not self._current:
            raise ValueError("没有活动的故事")
        return self.ideation.diverge(self._current, preferred_tone)

    def converge(self, chosen_id: int, constraint: str = "") -> dict:
        """收敛"""
        if not self._current:
            raise ValueError("没有活动的故事")
        result = self.ideation.converge(self._current, chosen_id, constraint)
        self._current.save()
        return result

    def set_intent(self, tone: str, conflict: str, protagonist: str, arc: str) -> dict:
        if not self._current:
            raise ValueError("没有活动的故事")
        result = self.ideation.set_intent(self._current, tone, conflict, protagonist, arc)
        self._current.save()
        return result

    # ─── 写作阶段 ─────────────────────────────

    def start_drafting(self, draft_mode: str = "first") -> dict:
        if not self._current:
            raise ValueError("没有活动的故事")
        result = self.drafting.start(self._current, draft_mode)
        self._current.save()
        return result

    def add_chapter(self, title: str, text: str) -> dict:
        if not self._current:
            raise ValueError("没有活动的故事")
        result = self.drafting.add_chapter(self._current, title, text)
        self._current.save()
        return result

    def draft_progress(self) -> dict:
        if not self._current:
            raise ValueError("没有活动的故事")
        return self.drafting.get_progress(self._current)

    # ─── 审计阶段 + 闭环 ──────────────────────

    def audit(self, chapter_index: int = -1) -> dict:
        if not self._current:
            raise ValueError("没有活动的故事")
        result = self.audit.audit_chapter(self._current, chapter_index)
        self._current.save()
        return result

    def feedback(self) -> list:
        if not self._current:
            raise ValueError("没有活动的故事")
        result = self.audit.generate_feedback(self._current)
        self._current.save()
        return result

    def apply_feedback(self, idx: int) -> dict:
        if not self._current:
            raise ValueError("没有活动的故事")
        result = self.audit.apply_suggestion(self._current, idx)
        self._current.save()
        return result

    # ─── 工具 ─────────────────────────────────

    def get_available_arcs(self) -> list:
        return list(StoryModel._get_arc_templates_keys())

    def status_report(self) -> str:
        if not self._current:
            return "没有活动的故事。使用 'create' 创建一个。"
        return self._current.summary()
