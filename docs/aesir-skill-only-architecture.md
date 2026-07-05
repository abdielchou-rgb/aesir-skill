# Æsir Writing · Skill-Only 架构方案

> 目标：用户零部署成本。不需要装 Python、不需要配置 MCP、不需要 API key。
> 所有故事能力由 agent 平台的原生 skill 提供，PWA 仅作为"存档展示和分享"的客户端。

---

## 一、核心判断：Skill 能做什么，不能做什么

这是最关键的认知。

### Agent 平台的能力边界

| 能力 | Claude Desktop MCP | Coze Bot | ChatGPT GPTs | 裸 Prompt |
|------|-------------------|----------|-------------|-----------|
| 对话驱动 | ✅ | ✅ | ✅ | ✅ |
| 调用外部工具 | ✅ | ✅ | ✅(Action) | ❌ |
| 读写本地文件 | ✅(stdio) | ❌ | ❌ | ❌ |
| 持久化跨会话记忆 | ⚠️(需自建) | ✅(变量) | ⚠️ | ❌ |
| 零配置 | ❌(需装Python) | ✅ | ✅(需Plus) | ✅ |

**关键约束：Skill/Agent 本身不做文件读写**。Coze Bot 和 ChatGPT GPTs 运行在云端，不能读写用户本地文件。这意味着：

- **42 门禁审计** → Skill 可以做（直接在 LLM prompt 中分析文本片段）
- **风格指纹提取** → Skill 可以做（在 prompt 中做统计计算）
- **发散/收敛** → Skill 可以做（纯 LLM 对话）
- **保存到存档** → 不能写到本地文件。但可以写到 Coze/ChatGPT 的记忆变量
- **读取本地书库** → 不能。用户必须粘贴文本给 agent

### 结论：Skill 能做 90% 的功能

| 功能 | Skill 模式 | 替代方案 |
|------|-----------|---------|
| diverge 发散 | ✅ 纯 LLM 对话 | — |
| converge 收敛 | ✅ 纯 LLM 对话 | — |
| audit 审计 | ✅ 纯 LLM prompt 分析 | — |
| fingerprint 指纹 | ✅ prompt 内统计 | — |
| write 写作 | ✅ 纯 LLM 对话 | — |
| director_pick 思想 | ✅ 纯 LLM 对话 | — |
| **保存存档** | ❌ 不能写本地 | 写入 Coze 变量 / 发给用户副本 |
| **读取本地文件** | ❌ 不能读本地 | 用户粘贴文本 |
| **PWA 展示** | ✅ 配合使用 | PWA 只读取 agent 写的内容 |

---

## 二、产品形态

```
用户交互入口（100%）
        │
        ▼
┌─────────────────────────────────────┐
│  用户自己的 Agent                    │
│  (Claude / Coze / ChatGPT)          │
│                                     │
│  安装了 Æsir Skill                  │
│  → 用户说"我想写个故事"              │
│  → agent 自动执行发散/收敛/审计      │
│  → 所有对话在 agent 内完成           │
└──────────────────────┬──────────────┘
                       │ Agent 生成的内容
                       │ 通过粘贴 / 分享复制
                       ▼
┌─────────────────────────────────────┐
│  PWA 故事簿                         │
│  → 展示 agent 生成的内容             │
│  → 快速捕获零散想法                  │
│  → 一键生成分享卡片                  │
│  → 时间线按日浏览                   │
│  → 发酵池展示未选世界线              │
└─────────────────────────────────────┘
```

**用户行为流（全流程）：**

```
1. 用户在 agent 中说："帮我构思一个故事"
2. agent 执行 Æsir Skill → 发散 5 条世界线
3. 用户选择一条 → agent 收敛成故事片段
4. 用户说"审计这段" → agent 返回 42 门禁结果
5. 用户复制片段 → 粘贴到 PWA 故事簿 → 自动保存
6. 用户可以在 PWA 中浏览所有历史片段
7. 用户可以在 PWA 中记下零散想法
8. 用户可以在 PWA 中生成分享卡片
```

---

## 三、Skill 形态（三个平台）

### 形态 A：Coze Bot（推荐首选）

**优势：完全免费，零部署，直接在 Coze 市场安装。**

用户需要做的：
1. 打开 Coze 平台（coze.cn）
2. 搜索"Æsir 故事织机"→ 安装
3. 直接对话

**能力：**
- 5 个工作流内置（diverge / converge / audit / write / distill_style）
- System prompt 覆盖 34 个工具的能力描述
- Coze 变量保存用户风格档案（跨会话记忆）
- 用户粘贴文本即可审计
- 复制生成的片段到 PWA

**局限：**
- 不能读写本地文件（但不需要）
- 审计受 token 限制（可分批粘贴）

### 形态 B：ChatGPT GPTs

**用户需要 ChatGPT Plus 订阅。**

用户需要做的：
1. 打开 ChatGPT
2. 在 GPT Store 搜索 Æsir
3. 开始对话

能力类似 Coze Bot，但 GPTs 的 Action 能力更强（可以调外部 API）。

### 形态 C：Claude Project + 知识底座

**免费用户也可以在 Claude 中直接用。**

用户需要做的：
1. 打开 Claude
2. 创建一个 Project
3. 把知识底座文件（markdown）拖进去
4. 告诉 Claude："你现在是 Æsir 故事引擎"
5. 开始对话

**能力：** 基于 Claude 的原生能力 + 知识底座中的方法论。不如工作流精确，但零成本。

---

## 四、PWA 的重新定位

当前的 PWA（`aesir-phase1.html`）已经是在这个方向上了，但需要确认它的定位准确：

### PWA 只做三件事

| PWA 功能 | 定位 | 技术实现 |
|---------|------|---------|
| **快速捕获** | 用户在手机上有零散念头时记下 | textarea + localStorage |
| **故事时间线** | 展示 agent 生成的所有片段 | localStorage + 按日分组 |
| **分享卡片** | 一键复制到小红书/朋友圈 | 复制文本到剪贴板 |

### PWA 不做的事（明确边界）

| 不会做的事 | 原因 |
|-----------|------|
| 发散世界线 | agent 做 |
| 审计文本 | agent 做 |
| 风格分析 | agent 做 |
| 写作生成 | agent 做 |
| 用户登录 | 不需要 |
| API key 配置 | 不需要 |

### PWA 与 agent 的数据流动

当前 PWA 已经暴露了接口：
```javascript
// 从 agent 接收内容
window.aesirAddFragment({
    idea: "原始想法",
    premise: "前提句",
    tone: "冷峻写实",
    main: "故事正文",
    breakout: "破坏约束版本",
    medium: "流媒体开剧"
});

// 从 agent 接收未选世界线
window.aesirAddFerment({
    idea: "原始想法",
    worldlines: [...]
});
```

用户的工作流：
1. Agent 生成故事片段 → 复制
2. 打开 PWA → 粘贴 → 自动保存
3. 或者：PWA 记下想法 → 复制 → 粘贴到 agent 启动发散

---

## 五、34 工具 → Skill 映射

| MCP 工具 | Coze Bot 实现 | ChatGPT GPTs 实现 |
|---------|-------------|------------------|
| diverge | ✅ 工作流1 | ✅ Action |
| converge | ✅ 工作流2 | ✅ Action |
| audit | ✅ 工作流3(纯prompt分析) | ✅ Action |
| fingerprint | ✅ 工作流3同 | ✅ Action |
| write | ✅ 工作流4 | ✅ Action |
| director_pick | ✅ system prompt 内置 | ✅ system prompt |
| stc15/pspine等 | ✅ system prompt 内置 | ✅ Knowledge 文件 |
| save/archive | ❌ → 用户粘贴到 PWA | ❌ → 用户粘贴到 PWA |
| distill | ✅ system prompt 分析 | ✅ Action |

**不需要本地 MCP Server 的功能：**

| 工具 | 在 Skill 中的实现方式 |
|------|---------------------|
| diverge | 纯 LLM prompt：生成 5 条世界线 |
| converge | 纯 LLM prompt：选中→约束→开场 |
| audit | 纯 LLM prompt：分析文本是否符合 42 门禁 |
| fingerprint | 纯 LLM prompt：提取节奏/鸿沟/触点等指标 |
| write | 纯 LLM prompt：fragment/chapter/rewrite/develop |
| director_pick | system prompt 中列出 10 个命题 → 匹配 |
| stc15/pspine/harmon/sg5/sgg/storr | system prompt 中给出结构 → agent 直接回答 |
| card/arc/emo/yorke/casper/kisho/manga/scene/mice/egri/cron/maass/script/drafts | system prompt 中列出 → agent 按需输出 |
| expand | 纯 LLM prompt：分级展开 |
| distill | 纯 LLM prompt + 变量存档 |
| save/archive | agent 回复中给出，用户复制到 PWA |

---

## 六、部署路径

### 第 1 步：Coze Bot 升级（立即可以做）

当前的 `aesir-coze-bot.json` 已经有 5 个工作流，system prompt 需要调整以覆盖全部 34 工具的功能描述。用户只需要：
1. 打开 Coze
2. 导入配置文件
3. 发布 Bot → 获得分享链接

### 第 2 步：ChatGPT GPTs 配置

创建一个 GPTs，把知识底座文件和 system prompt 放进去。用户搜索安装即可。

### 第 3 步：PWA 保持现状

当前 PWA 已经对准了"展示+捕获+分享"的方向，只需要确保 user flow 顺畅。

### 第 4 步：MCP Server 保留为"高级模式"

对于有技术能力的用户（比如你本地的 Ollama 用户），MCP Server 仍然是最强大的模式——可以读写本地文件、批量分析书库。Skill 模式做不到这些。

---

## 七、总结

```
用户零部署路径（推荐）：
  用户 → 打开 Coze → 安装 Æsir Bot → 开始对话
  需要存档？→ 打开 PWA → 粘贴

技术用户路径（可选）：
  用户 → pip install mcp → 配 MCP Server → 本地完整能力
```

Skill 模式不能做到的（必须坦诚）：
1. **读写本地文件**——不能读你的书库，不能写本地存档
2. **长文本审计**——受限 token 窗口，只能粘贴关键片段
3. **风格档案积累**——Coze 变量可以存一部分，不如本地 `~/.aesir/` 灵活

但只要用户的核心需求是"从模糊想法到故事片段"，Skill 模式覆盖了 90% 的功能，且部署成本为零。

---

你要不要我先把 Coze Bot 的 system prompt 更新到覆盖全部 34 工具的版本？这样你可以直接导入用。
