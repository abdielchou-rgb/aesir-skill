# Æsir 故事织机 · 交接文档

> 日期: 2026-07-04
> 版本: Coze Bot v4.1 / MCP Server v4.2
> 位置: D:\Claude\

---

## 一、项目概览

Æsir 是一个故事创作引擎，核心流程：

```
模糊想法 → 发散(5条世界线) → 用户选一条 → 收敛(完整故事单元)
                                         → 未闭合线索 → 继续延展 / 计入画布
```

每条世界线带 2-3 个可能性方向，收敛支持三种粒度（short/standard/outline），故事中间有分歧点可选不同走法，审计覆盖 15 组门禁 + 15 维指纹 + 修订建议。

---

## 二、核心文件（4 个）

| 文件 | 做什么 | 用户量 |
|------|--------|--------|
| `aesir-coze-bot.json` | Coze Bot 配置，导入即用 | 任何人 |
| `aesir-mcp-server.py` | MCP Server（35 工具） | 需 Python |
| `aesir-phase1.html` | PWA 故事簿（浏览器打开） | 任何人 |
| `aesir-knowledge-base.md` | 14 章 130+ 方法论，33KB | 参考 |

### 辅助模块

| 文件 | 做什么 |
|------|--------|
| `aesir-distill.py` | 蒸馏管道 |
| `aesir-narrative-intel.py` | TMDb 关键词 + 10 维标注 |
| `aesir-atom-engine.py` | 原子兼容性 + 探索-利用平衡 |

---

## 三、Coze Bot v4.1

### 5 个工作流

| 工作流 | 输入 | 输出 | 核心能力 |
|--------|------|------|---------|
| diverge | idea + canvas | 5 条世界线 | 含可能性方向 + 类型感知 |
| converge | idea + worldline + size | 故事单元 | short/standard/outline + 分歧点内嵌 |
| extend | canvas_summary + direction | 下一段单元 | 线索承接 + 分歧点延展 |
| audit | text | 审计报告 | 15 门禁 + 15 维指纹 + 修订建议 |
| write | mode + idea + config | 文本 | fragment/chapter/rewrite/develop |

### 15 组门禁

| 组 | 检测内容 | 级别 |
|----|---------|------|
| SVT-02 | 连续平坦（转折词密度） | BLOCK |
| IIT-01 | 煽动事件偏晚 | BLOCK |
| GDA-01 | 鸿沟饥荒 | BLOCK |
| RVI-01 | 好奇引擎熄火 | WARN |
| G3-01 | 首章冲突缺位 | BLOCK |
| TPE-02 | 触点不足 | WARN |
| PLE-01 | 爽点稀疏 | WARN |
| DDT-01 | 欲望不明 | WARN |
| LANG-05 | AI 腔 | WARN |
| BRK-01 | 章尾钩子缺失 | WARN |
| CLM-01 | 冲突层次单一 | WARN |
| SPN-01 | 悬念启动不足 | WARN |
| ARC-01 | 角色欲望缺失 | WARN |
| STR-01 | SG5 结构不完整 | WARN |
| NFR-01 | 过度复述 | WARN |

### 15 维指纹

- rhythm: mean_sl / gap_density / flip_rate
- voice: first_person_ratio / dialogue_ratio
- emotion: sentiment / pos / neg
- craft: touch / pleasure / desire / curiosity / ai
- summary: chars / sentences

### 修订建议

每个门禁附带 r 字段（具体修改建议），输出含 revision 数组。

---

## 四、MCP Server（35 工具）

| 分类 | 工具 |
|------|------|
| 创意核心 | diverge, converge, write, director_pick, card, arc, emo, expand |
| 审计与指纹 | audit, fingerprint, distill |
| 方法论 | stc15, pspine, harmon, pixar_r, sg5, sgg, storr, yorke, scene, mice, kisho, manga, cron, maass |
| 角色设计 | casper, egri |
| 数据管理 | save, archive, ferment, add_round, check, drafts, script |
| 同步 | sync（CloudBase Phase 2）|

运行：`python aesir-mcp-server.py` 或 `python aesir-mcp-server.py --ollama`

---

## 五、PWA 故事簿

| 功能 | 说明 |
|------|------|
| 快速捕获 | 手机端记念头 |
| 时间线 | 按日分组展示 |
| 导出/导入 | JSON 跨设备 |
| 分享卡片 | 复制到社交媒体 |
| 架构 | localStorage，纯本地 |

---

## 六、已吸收的外部来源

| 来源 | 吸收内容 |
|------|---------|
| novel-os/文鉴 | 门禁 + 指纹 + 修订建议思路 |
| 故事灵感创作包 | Factorizer schema + Director Propositions |
| Dramatica NCP | 意图卡片 + Throughlines |
| Save the Cat / Pixar / Harmon | 节拍表 + Spine + 故事圆 |
| Story Grid | 5 诫命 + 类型惯例 |
| Cron / Maass / Storr | 神经叙事 + 微张力 + 心理定制 |

---

## 七、待办

| 事项 | 优先级 | 工作量 |
|------|--------|--------|
| merge 工作流（单元合并） | P0 | 1 天 |
| 画布增强（检索/标签） | P1 | 2 天 |
| 分歧点可视化 | P1 | 1 天 |
| CloudBase 同步 | P1 | 3 天 |
| 协作叙事 | P2 | 1 周+ |
| MCP audit 扩展 | P1 | 2 天 |

---

## 八、已知问题

- Coze 审计是纯 JS 关键词匹配，不是 LLM 分析
- 分歧点需要手动传入 extend 工作流
- 会话关闭后画布数据丢失
- MCP sync 需 CloudBase 配置
