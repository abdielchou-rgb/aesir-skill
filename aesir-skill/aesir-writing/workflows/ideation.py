"""→ 创意发散-收敛工作流"""

import time
from ..bridges.aesir_adapter import AesirAdapter
from ..bridges.novelos_adapter import NovelOSAdapter
from ..core.story import StoryModel


class IdeationWorkflow:
    """创意工作流——从模糊想法到世界线+约束收敛"""

    def __init__(self):
        self.aesir = AesirAdapter()
        self.novelos = NovelOSAdapter()

    def run(self, story: StoryModel) -> dict:
        """执行完整创意工作流"""
        # 1. 推荐弧线
        arc_suggestions = self.aesir.suggest_arcs(story.idea)

        # 2. 生成意图
        intent = self.aesir.generate_intent(
            story.idea,
            story.intent_card.get("tone", "悬疑暗流"),
            story.intent_card.get("conflict", "认知冲突"),
            story.intent_card.get("protagonist", "探索者"),
        )

        return {
            "arc_suggestions": arc_suggestions,
            "intent_card": intent,
            "atoms_info": self.aesir.get_atoms_info(),
        }

    def diverge(self, story: StoryModel, preferred_tone: str = "") -> list:
        """发散世界线"""
        wls = self.aesir.diverge_worldlines(story.idea, preferred_tone)
        story.worldlines = wls
        story.status = "diverging"
        return wls

    def converge(self, story: StoryModel, chosen_id: int, constraint: str = "") -> dict:
        """收敛——记录选择和约束"""
        wl = next((w for w in story.worldlines if w.get("id") == chosen_id), story.worldlines[0] if story.worldlines else {})
        story.chosen_worldline = wl
        if constraint:
            story.constraint_history = self.aesir.record_constraint(story.constraint_history, constraint)
        story.status = "converging"
        return {"chosen": wl, "constraint_rounds": len(story.constraint_history)}

    def set_intent(self, story: StoryModel, tone: str, conflict: str, protagonist: str, arc: str) -> dict:
        """设定叙事意图"""
        story.arc_name = arc
        story.arc_chosen_at = time.strftime("%Y-%m-%dT%H:%M")
        story.intent_card = self.aesir.generate_intent(story.idea, tone, conflict, protagonist)
        story.status = "ideation"
        return story.intent_card
