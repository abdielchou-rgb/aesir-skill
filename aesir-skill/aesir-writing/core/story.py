"""Story 数据模型——从创意到成品的完整生命周期"""

import json, uuid
from pathlib import Path
from datetime import datetime
from typing import Optional


class StoryModel:
    """完整的故事对象。所有阶段共享同一个数据模型。"""

    def __init__(self, idea: str = ""):
        self.id: str = uuid.uuid4().hex[:12]
        self.idea: str = idea
        self.original_idea: str = idea
        self.created_at: str = datetime.now().isoformat()
        self.updated_at: str = self.created_at
        self.status: str = "ideation"
        # ideation | diverging | converging | drafting | auditing | revising | done

        # 创意阶段（Æsir）
        self.intent_card: dict = {}
        self.arc_name: str = ""
        self.arc_chosen_at: str = ""
        self.worldlines: list = []
        self.chosen_worldline: dict = {}
        self.constraint_history: list = []
        self.clarify_answers: list = []

        # 写作阶段（Novel OS）
        self.draft_mode: str = "first"
        self.chapters: list = []
        self.current_outline: list = []

        # 审计阶段（Novel OS gates）
        self.audit_history: list = []
        self.style_fingerprint: dict = {}
        self.last_audit_summary: str = ""

        # 闭环反馈
        self.revision_suggestions: list = []

        # 元数据
        self.version: int = 1

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, data: dict) -> "StoryModel":
        s = cls(data.get("idea", ""))
        for k, v in data.items():
            setattr(s, k, v)
        return s

    def summary(self) -> str:
        wc = sum(len(c.get("text", "")) for c in self.chapters)
        return (
            f"「{self.idea[:50]}」\n"
            f"  阶段: {self.status}  弧线: {self.arc_name or '未选'}\n"
            f"  章节: {len(self.chapters)}  字数: {wc}\n"
            f"  约束轮次: {len(self.constraint_history)}  v{self.version}"
        )
