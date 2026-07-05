"""→ 审计+闭环反馈工作流"""

from ..bridges.novelos_adapter import NovelOSAdapter
from ..core.story import StoryModel


class AuditWorkflow:
    """审计工作流——对已完成章节执行质量检查+闭环反馈"""

    def __init__(self):
        self.novelos = NovelOSAdapter()

    def audit_chapter(self, story: StoryModel, chapter_index: int = -1, genre: str = "xianxia_modern") -> dict:
        """审计指定章节"""
        if not story.chapters:
            return {"error": "没有可审计的章节"}

        if chapter_index == -1:
            chapter_index = len(story.chapters) - 1

        ch = story.chapters[chapter_index]
        result = self.novelos.audit_text(ch["text"], genre, ch.get("title", ""))

        # 记录审计结果
        for g in result["gates"]:
            story.audit_history.append({
                "gate": g["gate"],
                "result": g["result"],
                "chapter_index": chapter_index,
                "details": g.get("details", ""),
                "at": __import__("time").strftime("%Y-%m-%dT%H:%M"),
            })

        # 更新摘要
        story.last_audit_summary = (
            f"第 {chapter_index+1} 章审计：{result['summary']}\n"
        )
        for g in result["gates"]:
            if g["result"] != "pass":
                story.last_audit_summary += f"  · {g['gate']}: {g.get('details', '')}\n"

        story.status = "auditing"
        return result

    def generate_feedback(self, story: StoryModel) -> list:
        """从审计历史生成修改建议——驱动闭环"""
        blocks = [a for a in story.audit_history if a["result"] == "block"]
        warns = [a for a in story.audit_history if a["result"] == "warn"]

        suggestions = []
        if blocks:
            for b in blocks[:3]:
                suggestions.append({
                    "priority": "high",
                    "issue": f"{b['gate']}: {b.get('details', '')}",
                    "action": "reconverge",
                    "suggestion": f"返回创意阶段重写第 {b['chapter_index']+1} 章，针对性修复「{b['gate']}」",
                })
        if warns:
            for w in warns[:3]:
                suggestions.append({
                    "priority": "medium",
                    "issue": f"{w['gate']}: {w.get('details', '')}",
                    "action": "revise",
                    "suggestion": f"修改第 {w['chapter_index']+1} 章——优化「{w['gate']}」",
                })
        if not blocks and not warns:
            suggestions.append({
                "priority": "low",
                "issue": "所有门禁通过",
                "action": "proceed",
                "suggestion": "可进入下一阶段或开始精修",
            })

        story.revision_suggestions = suggestions
        return suggestions

    def apply_suggestion(self, story: StoryModel, suggestion_index: int) -> dict:
        """应用一条修改建议（将故事状态回退到 converging）"""
        if suggestion_index >= len(story.revision_suggestions):
            return {"error": "无效建议索引"}
        sug = story.revision_suggestions[suggestion_index]
        if sug["action"] == "reconverge":
            story.status = "revising"
            story.constraint_history = story.constraint_history or []
            story.constraint_history.append({
                "text": f"修复: {sug['issue']}",
                "round": len(story.constraint_history) + 1,
                "at": __import__("time").strftime("%Y-%m-%dT%H:%M"),
            })
        return {"applied": sug["action"], "new_status": story.status}

    def audit_all(self, story: StoryModel) -> dict:
        """审计所有未审计的章节"""
        results = []
        for i, ch in enumerate(story.chapters):
            already = any(a["chapter_index"] == i for a in story.audit_history)
            if not already:
                results.append(self.audit_chapter(story, i))
        return {
            "audited": len(results),
            "total_chapters": len(story.chapters),
            "summary": story.last_audit_summary,
        }
