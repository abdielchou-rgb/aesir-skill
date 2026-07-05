# Æsir 数据流方案：一键丝滑传递

---

## 核心要求

用户在手机 Coze Bot 聊完→产生的故事、想法、蒸馏结果→零操作到达 PWA 和桌面 MCP。

三个组件之间不共享运行环境，必须通过一个中间层中转。但中间层不能给用户增加任何操作负担。

---

## 方案：Supabase Free Tier 中转

### 架构

```
用户手机                          用户桌面
┌─────────┐     ┌──────────┐     ┌─────────┐
│ Coze    │────▶│ Supabase │────▶│ MCP     │
│ Bot     │     │ 中转服务  │     │ Server  │
└─────────┘     │ (免费)   │     └─────────┘
       │        └────┬─────┘        │
       │             │              │
       ▼             ▼              ▼
  Coze回复    PWA拉取展示    拉取数据到本地
  包含链接    分享卡片生成    继续创作
```

### 为什么用 Supabase 而不是其他

| 平台 | 免费额度 | Coze 能否 POST | PWA 能否 GET | MCP 能否读取 |
|------|---------|---------------|-------------|-------------|
| Supabase | 500MB DB + 免费 Edge Func | ✅ HTTP 调用 | ✅ REST API | ✅ REST API |
| Vercel KV | 100 条/天 | ✅ | ✅ | ✅ |
| 自建服务器 | 需付费 | ✅ | ✅ | ✅ |

Supabase 免费层足够——每个故事片段 1KB 以下，500MB 可以存 50 万条。

---

## 具体实现

### 数据结构

```
supabase_stories 表：
  id: UUID (自动生成)
  user_id: TEXT (Coze 用户的会话 ID)
  type: TEXT (fragment | idea | worldline | ferment | distillation)
  content: JSONB {
    premise: "前提句",
    tone: "冷峻写实",
    main: "故事正文",
    breakout: "破坏约束版本",
    medium: "流媒体剧集开场"
  }
  created_at: TIMESTAMP
```

### 组件 A：Coze Bot

Coze Bot 生成内容后，在 workflow 中调用 HTTP Request 节点，POST 到 Supabase：

```
URL: https://xxx.supabase.co/rest/v1/stories
Method: POST
Headers:
  apikey: {SUPABASE_ANON_KEY}
  Content-Type: application/json
Body:
{
  "user_id": "{{session.user_id}}",
  "type": "fragment",
  "content": {
    "premise": "...",
    "tone": "冷峻写实",
    "main": "...",
    "breakout": "..."
  }
}
```

Coze 回复中直接生成 PWA 的短链接：

```
✦ 故事片段已生成

（正文...）

📎 查看存档：https://aesir.pages.dev/s/{UUID}
```

点击链接直接在 PWA 中打开这个片段。

### 组件 B：PWA 故事簿

PWA 做三件事：

1. **展示时间线**：从 Supabase 拉取该用户的全部片段
2. **接收共享**：通过 URL 参数接收单个片段 ID 并展示
3. **快速捕获**：用户记下的零散念头 POST 到 Supabase

```javascript
// 拉取时间线
async function loadTimeline() {
  const res = await fetch(`https://xxx.supabase.co/rest/v1/stories?user_id=${uid}&order=created_at.desc`);
  const data = await res.json();
  renderTimeline(data);
}

// 批量拉取模式——用户打开 PWA 时自动拉取
setInterval(loadTimeline, 10000); // 每 10 秒自动拉取新内容
```

用户可以设置一个"设备 ID"（首次使用时生成，存在 localStorage），同一个 ID 的 Coze Bot 和 PWA 共享数据。

### 组件 C：MCP Server

MCP Server 新增一个 `sync` 工具：

```python
async def call(name, args):
    if name == "sync":
        """从 Supabase 拉取用户在 Coze 中生成的故事"""
        user_id = args.get("user_id", "")
        if not user_id:
            return {"error": "需要 user_id"}
        
        # 拉取新内容
        resp = requests.get(
            f"https://xxx.supabase.co/rest/v1/stories",
            headers={"apikey": SUPABASE_KEY},
            params={
                "user_id": f"eq.{user_id}",
                "order": "created_at.desc",
                "limit": 50,
                "select": "id,type,content,created_at"
            }
        )
        stories = resp.json()
        
        # 写入本地 ~/.aesir/ 存档
        local = Path.home() / ".aesir" / "synced_stories.json"
        existing = json.loads(local.read_text()) if local.exists() else []
        existing.extend(stories)
        local.write_text(json.dumps(existing))
        
        return {"synced": len(stories), "total": len(existing)}
```

用户在桌面端说"同步"或"拉取手机上的故事"→ MCP 从 Supabase 拉取→写入本地存档→用户可以在桌面端继续创作。

---

## 完整用户旅程

### 场景 A：手机上产生灵感

```
1. 用户打开 Coze app，说"帮我想个故事"
2. Coze Bot 发散 5 条世界线 → 用户选择第 3 条 → 收敛故事片段
3. Coze Bot 自动把片段 POST 到 Supabase，同时在回复中附带链接
4. 用户点击链接直接打开 PWA 看到这条片段
5. 或者：用户锁屏，离线
6. 回到家，打开电脑上的 PWA 故事簿
7. PWA 自动从 Supabase 加载所有新内容 → 用户可以浏览、分享
8. 用户可以打开 Claude Desktop，说"帮我看看手机上的新故事"
9. MCP Server 的 sync 工具从 Supabase 拉取 → 存入本地 → 继续创作
```

### 场景 B：快速捕获想法

```
1. 用户在地铁上想起一个念头
2. 打开手机 PWA → 快速捕获输入框 → 写下"地铁上看到一个女孩在哭"
3. PWA 自动 POST 到 Supabase（同时存本地 localStorage）
4. 回到家，打开 Coze Bot，说"帮我看看刚才的想法"
5. Coze Bot 从 Supabase 拉取最近捕获 → 说"我看到你记了一个关于地铁女孩的想法"
6. 用户说"对，帮我扩展这个"
7. Coze Bot 发散世界线 → 收敛片段 → 存回 Supabase
8. PWA 自动拉取新内容 → 用户刷到新片段
```

### 场景 C：蒸馏结果同步

```
1. 用户在 Coze Bot 中说"分析这篇小说的风格"
2. Bot 调用 distill_style 工作流 → 提取风格指纹
3. 结果 POST 到 Supabase
4. 用户回到桌面端，说"同步"
5. MCP Server 拉取指纹 → 写入风格档案 → 下次发散时自动使用
```

---

## 部署成本

| 组件 | 成本 | 说明 |
|------|------|------|
| Supabase 免费层 | ¥0/月 | 500MB DB，10 万行以下 |
| PWA 部署 (Cloudflare Pages) | ¥0/月 | 免费额度足够 |
| Coze Bot | ¥0/月 | 免费额度内 |
| MCP Server | 已有 | 本地运行 |

**总计月成本：¥0。** 所有组件都有免费层。

---

## 与当前架构的兼容性

当前已有的资产在这个方案中的位置：

| 已有资产 | 在此方案中的角色 | 需要修改 |
|---------|---------------|---------|
| `aesir-coze-bot.json` | Coze Bot + 5 workflows | 每个 workflow 末尾加 HTTP Request 节点 |
| `aesir-phase1.html` | PWA 故事簿 | 加 Supabase 客户端（jsr 包或直接 fetch） |
| `aesir-mcp-server.py` | MCP Server + sync 工具 | 加一个 `sync` 工具 |
| `aesir-knowledge-base.md` | 方法论底座 | 不需要改 |

**修改量估算：**
- Coze Bot：每个 workflow 加 1 个 HTTP 节点，约 1 小时
- PWA：加 Supabase 客户端 + 自动拉取逻辑，约 3 小时
- MCP Server：加 sync 工具，约 2 小时
- **总计：约 2 天**

---

## 补充：分享功能

PWA 的分享卡片功能也走 Supabase 链接：

```
用户点击"分享" → PWA 生成 URL `https://aesir.pages.dev/s/{UUID}`
                     ↓
              用户复制到小红书/朋友圈
                     ↓
              他人打开 → 看到完整片段
              （含"生成自 Æsir 故事织机"尾标）
```

不需要用户自建后端——Supabase 免费层全包了。
