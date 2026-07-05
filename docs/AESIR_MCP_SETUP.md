# Æsir MCP Server — 用户配置指南

## 快速安装（Claude Desktop）

### 1. 安装依赖

```bash
pip install mcp
```

### 2. 获取脚本

```bash
# 从你的工作目录复制
cp aesir-mcp-server.py ~/aesir-mcp-server.py
# 或直接下载
```

### 3. 配置 Claude Desktop

编辑 `claude_desktop_config.json`（路径见下方），加入：

```json
{
  "mcpServers": {
    "aesir": {
      "command": "python3",
      "args": ["/绝对路径/aesir-mcp-server.py"]
    }
  }
}
```

**配置文件位置：**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

### 4. 重启 Claude Desktop

连接成功后终端会出现 `✦ Æsir MCP Server 启动` 字样。

### 5. 开始使用

在 Claude 中直接输入你的模糊想法，Claude 会自动调用 Æsir 工具。

---

## 支持的其他 Agent 平台

### Cursor

在 Cursor 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "aesir": {
      "command": "python3",
      "args": ["/绝对路径/aesir-mcp-server.py"]
    }
  }
}
```

### 其他 MCP 兼容客户端

方法相同——配置 MCP server 指向 `python3 /绝对路径/aesir-mcp-server.py`。

---

## 可用工具

| 工具 | 功能 | 触发场景 |
|------|------|---------|
| `diverge` | 发散世界线 | 用户说了模糊想法后 |
| `converge` | 收敛故事片段 | 用户选中一条世界线 + 给出约束后 |
| `distill_text` | 分析文本风格并更新档案 | 用户说"分析这篇"/上传文本后 |
| `save_archive` | 保存到存档 | 用户说"保存"后 |
| `get_archive` | 查看历史存档 | 用户说"查看存档"/"历史"后 |
| `get_style_profile` | 查看风格档案 | 用户说"我的风格"/"偏好"后 |
| `get_ferment_pool` | 查看发酵池 | 用户说"发酵"/"未选方向"后 |
| `check_atom_compatibility` | 检查原子搭配 | 用户想确认某个组合是否自洽 |

## 工作原理

```
用户输入模糊想法
  ↓
你的 agent（Claude / Cursor 等）调用 diverge 工具
  → 返回 5 条世界线配置（调性、冲突、主角类型等结构化数据）
  → agent 基于这些配置用 LLM 生成具体文本展示给用户
  ↓
用户选择一条 + 给出约束
  ↓
agent 调用 converge 工具
  → 返回世界线配置 + 破坏约束方向
  → agent 基于这些生成 500-800 字的故事开场
  ↓
用户可以选择保存
  → 未选的世界线进入发酵池，下次可唤醒

用户的所有数据存储在 ~/.aesir/ 目录下
```

## 优势

- **无需 API key**：agent 自己的 LLM 能力处理文本生成，MCP server 只做结构化数据和工具逻辑
- **模板无限**：不再是硬编码模板，LLM 基于原子配置生成完全不同的输出
- **跨平台**：任何支持 MCP 的客户端都能用
- **本地存储**：风格档案和存档都在用户自己设备上
