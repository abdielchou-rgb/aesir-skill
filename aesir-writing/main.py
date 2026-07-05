"""aesir-writing — CLI 入口 + MCP Server 入口"""

import sys, os
from pathlib import Path

# 确保 Æsir 和 Novel OS 都在 import 路径上
_HERE = Path(__file__).parent
_AEIRS_SRC = _HERE.parent / "aesir-mcp-server.py"
_NOVELOS_SRC = _HERE.parent / "novel-os" / "novel-os"
for p in [_AEIRS_SRC.parent, _NOVELOS_SRC]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def main():
    """CLI 入口"""

    if "--mcp" in sys.argv:
        from .server.mcp import run_mcp
        run_mcp()
        return

    from .core.orchestrator import Orchestrator
    orch = Orchestrator()

    if "--list" in sys.argv or "-l" in sys.argv:
        stories = orch.list_all()
        if not stories:
            print("(没有故事)")
        else:
            for s in stories:
                print(f"  {s['id'][:8]} | {s.get('idea','')[:50]} | {s.get('status','')} | {s.get('chapter_count',0)}章")
        return

    if "--new" in sys.argv or "-n" in sys.argv:
        idx = sys.argv.index("--new") if "--new" in sys.argv else sys.argv.index("-n")
        idea = " ".join(sys.argv[idx+1:]) if len(sys.argv) > idx + 1 else input("✎ 想法: ")
        s = orch.create(idea)
        print(f"  ✓ 故事已创建: {s.id}")
        print(f"  ✓ 创意阶段初始化")
        return

    if "--story" in sys.argv:
        idx = sys.argv.index("--story")
        sid = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else ""
        if not sid:
            stories = orch.list_all()
            if stories:
                sid = stories[0]["id"]
        if sid:
            orch.load(sid)
            print(f"  ✓ 已加载: {orch.current.idea[:50] if orch.current else sid}")
            return

    # 交互模式
    _run_interactive(orch)


def _run_interactive(orch: Orchestrator):
    """交互式 CLI"""
    import time

    print("  ✦ Æsir Writing — 创意→写作→审计 闭环")
    print("  ═" * 30)

    while True:
        if orch.current:
            print(f"\n  📖 {orch.current.idea[:50]} [{orch.current.status}] ✍{len(orch.current.chapters)}章")

        print("\n  ── 操作 ──")
        print("  new    — 创建新故事")
        print("  list   — 所有故事")
        print("  load   — 加载故事")
        print("  intent — 设定意图")
        print("  div    — 发散世界线")
        print("  conv   — 收敛")
        print("  draft  — 进入写作")
        print("  ch     — 写一章")
        print("  audit  — 审计")
        print("  fb     — 反馈")
        print("  status — 状态摘要")
        print("  mcp    — 启动 MCP Server")
        print("  q      — 退出")

        cmd = input("\n  > ").strip().lower()

        if cmd in ("q", "quit", "exit"):
            break

        elif cmd == "new":
            idea = input("  ✎ 想法: ").strip()
            if idea:
                orch.create(idea)
                print(f"  ✓ {orch.current.id}")

        elif cmd == "list":
            for s in orch.list_all():
                print(f"  {s['id'][:8]} | {s.get('idea','')[:50]} | {s.get('status','')}")

        elif cmd == "load":
            sid = input("  story_id: ").strip()
            if orch.load(sid):
                print(f"  ✓ {orch.current.idea[:50] if orch.current else ''}")

        elif cmd == "intent":
            if not orch.current:
                print("  (没有故事)"); continue
            print("  调性: 1冷峻写实 2温暖治愈 3黑色幽默 4悬疑暗流 5诗意思辨 6激烈狂暴")
            ti = int(input("  > ").strip() or "4") - 1
            tones = ["冷峻写实","温暖治愈","黑色幽默","悬疑暗流","诗意思辨","激烈狂暴"]
            tone = tones[max(0, min(5, ti))]
            print("  冲突: 1身份 2资源 3价值观 4关系 5生存 6认知")
            ci = int(input("  > ").strip() or "6") - 1
            conflicts = ["身份冲突","资源冲突","价值观冲突","关系冲突","生存冲突","认知冲突"]
            conflict = conflicts[max(0, min(5, ci))]
            arcs = ["英雄之旅","推理揭秘","情感波澜","逆袭流","救赎之弧","重重谜团"]
            print("  弧线:", ", ".join(f"{i+1}.{a}" for i, a in enumerate(arcs)))
            ai = int(input("  > ").strip() or "1") - 1
            arc = arcs[max(0, min(5, ai))]
            orch.set_intent(tone, conflict, "探索者", arc)
            print(f"  ✓ {tone} / {conflict} / {arc}")

        elif cmd == "div":
            if not orch.current:
                print("  (没有故事)"); continue
            result = orch.ideation.run(orch.current)
            wls = orch.diverge()
            print(f"  ✓ {len(wls)} 条世界线")
            for w in wls[:3]:
                print(f"    {w.get('id','?')}. {w.get('tone','')} · {w.get('conflict','')}")

        elif cmd == "conv":
            if not orch.current:
                print("  (没有故事)"); continue
            cid = int(input("  选中世界线编号: ").strip() or "1")
            c = input("  约束（可选）: ").strip()
            orch.converge(cid, c)
            print(f"  ✓ 已收敛（约束轮次: {len(orch.current.constraint_history)}）")

        elif cmd == "draft":
            if not orch.current:
                print("  (没有故事)"); continue
            dm = input("  草稿模式 (first/revision/polish): ").strip() or "first"
            result = orch.start_drafting(dm)
            print(f"  ✓ {result.get('principle','')}")
            print(f"  预计 {result.get('estimated_chapters',0)} 章")

        elif cmd == "ch":
            if not orch.current:
                print("  (没有故事)"); continue
            title = input(f"  标题 (第{len(orch.current.chapters)+1}章): ").strip()
            if not title:
                title = f"第{len(orch.current.chapters)+1}章"
            print("  正文（.end 结束，.cancel 取消）:")
            lines = []
            while True:
                l = input()
                if l.strip() == ".end": break
                if l.strip() == ".cancel": lines = []; break
                lines.append(l)
            if lines:
                result = orch.add_chapter(title, "\n".join(lines))
                print(f"  ✓ {result['chapter']}章 {result['words']}字")

        elif cmd == "audit":
            if not orch.current:
                print("  (没有故事)"); continue
            ci = input(f"  章节 (1-{len(orch.current.chapters)}，回车=最新): ").strip()
            idx = int(ci) - 1 if ci else -1
            result = orch.audit(idx)
            print(f"\n{result.get('summary','')}")

        elif cmd == "fb":
            if not orch.current:
                print("  (没有故事)"); continue
            suggestions = orch.feedback()
            print(f"  反馈 ({len(suggestions)} 条):")
            for s in suggestions:
                p = "🔴" if s['priority'] == 'high' else "🟡" if s['priority'] == 'medium' else "🟢"
                print(f"  {p} [{s['action']}] {s.get('issue','')}")

        elif cmd == "status":
            if not orch.current:
                print("  (没有故事)"); continue
            print(orch.status_report())

        elif cmd == "mcp":
            from .server.mcp import run_mcp
            run_mcp()

        else:
            print("  ? 未知指令")


if __name__ == "__main__":
    main()
