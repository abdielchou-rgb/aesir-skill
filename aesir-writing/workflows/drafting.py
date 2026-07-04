"""→ 写作工作流"""

from ..bridges.novelos_adapter import NovelOSAdapter
from ..bridges.aesir_adapter import AesirAdapter
from ..core.story import StoryModel
from datetime import datetime

DRAFT_MODES = {
    "first": "第一稿：写给自己。允许粗糙、允许废话、允许跑题。目标是写完，不是写对。",
    "revision": "修改稿：写给读者。砍掉所有不是故事的内容，检查每一句是否在推动故事或人物。",
    "polish": "精修稿：逐句打磨。关注用词精度、节奏美感、感官细节。",
}


class DraftingWorkflow:
    """写作工作流——管理章节写作和草稿模式"""

    def __init__(self):
        self.novelos = NovelOSAdapter()
        self.aesir = AesirAdapter()

    def start(self, story: StoryModel, draft_mode: str = "first") -> dict:
        """进入写作阶段"""
        story.draft_mode = draft_mode
        story.status = "drafting"

        # 获取弧线模板估算章节数
        arc = self.aesir.get_arc_template(story.arc_name)
        beats = arc.get("beats", []) if arc else []
        chapter_estimate = max(1, len(beats))

        return {
            "story_id": story.id,
            "arc": story.arc_name,
            "mode": draft_mode,
            "principle": DRAFT_MODES.get(draft_mode, ""),
            "estimated_chapters": chapter_estimate,
            "outline": [
                {"chapter": i + 1, "beat": b.get("name", ""), "function": b.get("function", "")}
                for i, b in enumerate(beats)
            ] if beats else [],
        }

    def add_chapter(self, story: StoryModel, title: str, text: str) -> dict:
        """写入一章"""
        analysis = self.novelos.analyze_chapter(text, title)
        story.chapters.append({
            "index": len(story.chapters) + 1,
            "title": title,
            "text": text,
            "analysis": analysis,
            "created_at": datetime.now().isoformat(),
        })
        story.version += 1
        return {
            "chapter": len(story.chapters),
            "words": len(text),
            "analysis_preview": {
                "hook": analysis.get("has_hook", False),
                "touchpoints": analysis.get("touchpoints", 0),
                "gap_density": analysis.get("gap_density", 0),
            },
        }

    def get_progress(self, story: StoryModel) -> dict:
        """获取写作进度"""
        arc = self.aesir.get_arc_template(story.arc_name)
        beats = arc.get("beats", []) if arc else []
        total = max(len(beats), 1)
        written = len(story.chapters)
        wc = sum(len(c.get("text", "")) for c in story.chapters)
        return {
            "chapters_written": written,
            "total_estimated": total,
            "progress_pct": round(written / total * 100),
            "total_words": wc,
            "mode": story.draft_mode,
        }
