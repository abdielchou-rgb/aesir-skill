"""MCP Server — aesir-writing 作为 agent 工具"""

import json, sys
from typing import Any

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    import asyncio
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from ..core.orchestrator import Orchestrator


def run_mcp():
    """启动 MCP Server"""
    if not MCP_AVAILABLE:
        print("需要: pip install mcp", file=sys.stderr)
        sys.exit(1)

    orch = Orchestrator()
    server = Server("aesir-writing")

    @server.list_tools()
    async def list_tools():
        return [
            Tool(name="create_story", description="创建新故事", inputSchema={
                "type": "object",
                "properties": {"idea": {"type": "string", "description": "模糊想法"}},
                "required": ["idea"]}),
            Tool(name="start_ideation", description="开始创意阶段（推荐弧线+生成意图）", inputSchema={
                "type": "object",
                "properties": {"story_id": {"type": "string"}},
                "required": ["story_id"]}),
            Tool(name="set_intent", description="设定叙事意图", inputSchema={
                "type": "object",
                "properties": {
                    "story_id": {"type": "string"},
                    "tone": {"type": "string", "enum": ["冷峻写实","温暖治愈","黑色幽默","悬疑暗流","诗意思辨","激烈狂暴"]},
                    "conflict": {"type": "string", "enum": ["身份冲突","资源冲突","价值观冲突","关系冲突","生存冲突","认知冲突"]},
                    "arc": {"type": "string", "description": "弧线类型，可用 list_arcs 获取"}},
                "required": ["story_id","tone","conflict","arc"]}),
            Tool(name="diverge", description="发散世界线", inputSchema={
                "type": "object",
                "properties": {"story_id": {"type": "string"}, "preferred_tone": {"type": "string"}},
                "required": ["story_id"]}),
            Tool(name="converge", description="收敛（选择一条世界线）", inputSchema={
                "type": "object",
                "properties": {"story_id": {"type": "string"}, "worldline_id": {"type": "integer"}, "constraint": {"type": "string"}},
                "required": ["story_id","worldline_id"]}),
            Tool(name="start_drafting", description="进入写作阶段", inputSchema={
                "type": "object",
                "properties": {"story_id": {"type": "string"}, "draft_mode": {"type": "string", "enum": ["first","revision","polish"]}},
                "required": ["story_id"]}),
            Tool(name="add_chapter", description="添加一章节", inputSchema={
                "type": "object",
                "properties": {"story_id": {"type": "string"}, "title": {"type": "string"}, "text": {"type": "string"}},
                "required": ["story_id","title","text"]}),
            Tool(name="audit_latest", description="审计最新章节", inputSchema={
                "type": "object",
                "properties": {"story_id": {"type": "string"}},
                "required": ["story_id"]}),
            Tool(name="get_feedback", description="获取完整闭环反馈", inputSchema={
                "type": "object",
                "properties": {"story_id": {"type": "string"}},
                "required": ["story_id"]}),
            Tool(name="list_arcs", description="列出可用的叙事弧线", inputSchema={"type": "object","properties": {}}),
            Tool(name="list_stories", description="列出所有故事", inputSchema={"type": "object","properties": {}}),
            Tool(name="get_status", description="获取故事状态", inputSchema={
                "type": "object",
                "properties": {"story_id": {"type": "string"}},
                "required": ["story_id"]}),
        ]

    @server.call_tool()
    async def call_tool(name: str, args: dict) -> list:
        r = lambda d: [TextContent(type="text", text=json.dumps(d, ensure_ascii=False))]
        try:
            if name == "create_story":
                s = orch.create(args["idea"])
                return r({"story_id": s.id, "idea": s.idea})

            elif name == "start_ideation":
                orch.load(args["story_id"])
                result = orch.ideation.run(orch.current)
                return r({"arc_suggestions": result["arc_suggestions"], "atoms": result["atoms_info"]})

            elif name == "set_intent":
                orch.load(args["story_id"])
                orch.set_intent(args["tone"], args["conflict"], "探索者", args["arc"])
                return r({"status": "ok", "intent": f"{args['tone']}/{args['conflict']}/{args['arc']}"})

            elif name == "diverge":
                orch.load(args["story_id"])
                wls = orch.diverge(args.get("preferred_tone", ""))
                return r({"worldlines": wls, "total": len(wls)})

            elif name == "converge":
                orch.load(args["story_id"])
                result = orch.converge(args["worldline_id"], args.get("constraint", ""))
                return r(result)

            elif name == "start_drafting":
                orch.load(args["story_id"])
                result = orch.start_drafting(args.get("draft_mode", "first"))
                return r(result)

            elif name == "add_chapter":
                orch.load(args["story_id"])
                result = orch.add_chapter(args["title"], args["text"])
                return r(result)

            elif name == "audit_latest":
                orch.load(args["story_id"])
                result = orch.audit(-1)
                return r(result)

            elif name == "get_feedback":
                orch.load(args["story_id"])
                suggestions = orch.feedback()
                return r({"suggestions": suggestions, "summary": orch.current.last_audit_summary})

            elif name == "list_arcs":
                return r({"arcs": ["英雄之旅","推理揭秘","情感波澜","逆袭流","救赎之弧","重重谜团"]})

            elif name == "list_stories":
                return r(orch.list_all())

            elif name == "get_status":
                orch.load(args["story_id"])
                return r({"summary": orch.status_report(), "status": orch.current.status if orch.current else "none"})

        except Exception as e:
            return r({"error": str(e)})
        return r({"error": f"unknown: {name}"})

    print("✦ aesir-writing MCP Server 启动", file=sys.stderr)
    asyncio.run(server.run(stdio_server()))
