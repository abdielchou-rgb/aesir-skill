# Æsir 故事织机 · 阶段性总结报告

> 日期：2026-07-02
> 版本：v4.2（最终整合版）
> 从零到完整产品架构的全过程回顾

---

## 一、已交付资产总览

| # | 资产 | 版本 | 说明 | 行数/大小 |
|---|------|------|------|----------|
| 1 | `aesir-mcp-server.py` | v4.2 | 35 工具 MCP Server + Ollama 双模式 | 270 行 |
| 2 | `aesir-phase1.html` | v3 | PWA 故事簿(localStorage + 导出/导入 + CloudBase 预留) | 260 行 |
| 3 | `aesir-coze-bot.json` | v2.0 | Coze Bot 配置(5 工作流 + 34 能力 system prompt) | 90 行 |
| 4 | `aesir-knowledge-base.md` | v2.1 | 知识底座(14 章, 130+ 方法论来源) | ~600 行 |
| 5 | `aesir-product-architecture.md` | v1 | 产品架构文档 | |
| 6 | `aesir-agent-first.md` | v1 | agent-first 转型方案 | |
| 7 | `aesir-skill-only-architecture.md` | v1 | skill-only 架构方案 | |
| 8 | `aesir-data-flow-plan.md` | v1 | 数据同步方案 | |
| 9 | `aesir-china-deploy.md` | v3 | 中国部署方案(CloudBase) | |
| 10 | `aesir-deploy-guide.md` | v1 | 部署指南 | |
| 11 | `aesir-mobile-chat.md` | v1 | 手机端对话方案 | |
| 12 | `aesir-distill.py` | v1 | 蒸馏管道 | |
| 13 | `aesir-narrative-intel.py` | v1 | TMDb 关键词 + 10 维标注 | |
| 14 | `aesir-atom-engine.py` | v1 | 原子兼容性 + 探索-利用平衡 | |
| 15 | `supabase/migration.sql` | v1 | Supabase 建表(备用) | |

---

## 二、能力来源索引

### 学术界（12 项）

| 来源 | 核心贡献 | 在 Æsir 中的落地 |
|------|---------|----------------|
| **Dramatica NCP** | 叙事意图模型 + Throughlines + Dynamics | `generate_intent_card` / system prompt 中的 story mind |
| **CASPER 框架(UNC 2026)** | 8 维角色深度(神秘性/矛盾/道德模糊等) | `get_casper_profile` 工具 |
| **CHI 2025 Dreamsmithy** | 多轮约束, 用户控制感 | `add_round` 工具 |
| **StoryBox(AAAI 2026)** | 多智能体涌现叙事 | 探索型世界线机制 |
| **IVIE(ICCC 2026)** | 神经符号验证 | 原子兼容性检查 + Story Grid 5 诫命 |
| **CreAgentive** | 故事原型双图(角色+情节) | 知识底座记录 |
| **PNAS 2025** | Sui Generis Score 多样性指标 | 审计标准参考 |
| **EACL 2026** | 叙事连贯性/因果推理 | 知识底座记录 |
| **因果推理(PolyU)** | 因果事件知识 | 知识底座记录 |
| **神经叙事学(Cron)** | 大脑预测机制/微张力/按需披露 | `get_cron_neuro_rules` 工具 |

### 好莱坞编剧（13 项）

| 来源 | 核心贡献 | 在 Æsir 中的落地 |
|------|---------|----------------|
| **Save the Cat(Snyder)** | 15 节拍表 | `get_stc15` 工具 |
| **Pixar Story Spine** | 7 步骨架 | `get_pspine` 工具 |
| **Dan Harmon Story Circle** | 8 步循环 | `get_harmon` 工具 |
| **Pixar 22 条规则** | 创作原则 | `get_pixar_rules` 工具 |
| **Scriptnotes(August+Mazin)** | 场景处境法则 | `get_scene_checklist` 工具 |
| **Truby** | 对手三原型/自我欺骗/道德论证 | OPPONENT_ARCHETYPES 常量 |
| **McKee** | 冲突分层/欲望理论 | CONFLICT_LAYERS 常量 |
| **Yorke** | 5 幕辩证结构 | `get_yorke_dialectic` 工具 |
| **Egri** | 骨骼结构三维度/前提三段论 | `get_egri_bones` 工具 |
| **Block** | 视觉叙事(色彩/空间/节奏) | 分镜建议参数 |
| **Seger** | 场景重写清单 | 合并入 scene 工具 |
| **Cameron** | Scriptment 模式 | `get_scriptment_guide` 工具 |

### 网文行业（3 项）

| 来源 | 核心贡献 | 在 Æsir 中的落地 |
|------|---------|----------------|
| **12 种爽点原子** | 信息差碾压/降维打击等 | PLEASURE_POINTS 常量, `get_pleasure_points` 工具 |
| **辰东** | 视觉锤 + 落地悬念 | 知识底座记录 |
| **猫腻** | 执念驱动 + 行为反差 | 知识底座记录 |

### 漫画/动漫（2 项）

| 来源 | 核心贡献 | 在 Æsir 中的落地 |
|------|---------|----------------|
| **Kishōtenketsu** | 起承转合 4 幕 | `get_kishotenketsu` 工具 |
| **漫画分镜 + Kakimoji** | 面板规则 + 拟声词 | `get_manga_panel_rules` 工具 |

### 写作书（9 项）

| 来源 | 核心贡献 | 在 Æsir 中的落地 |
|------|---------|----------------|
| **MICE Quotient(Card)** | 四种故事类型 | `get_mice_quotient` 工具 |
| **Cron(Wired for Story)** | 神经叙事 10 条 | `get_cron_neuro_rules` 工具 |
| **Maass(Writing the Breakout Novel)** | 微张力 5 问 | `get_maass_micro_tension` 工具 |
| **King(On Writing)** | 第一稿/修改稿双模式 | `get_draft_modes` 工具 |
| **Story Grid(Coyne)** | 5 诫命 + 4 幕 + 类型惯例 | `get_sg5` + `get_sgg` 工具 |
| **Will Storr(The Science of Storytelling)** | 叙事心理定制 6 条 | `get_storr_psych_rules` 工具 |
| **StyleDNA(草苔)** | 风格引擎 | 知识底座记录 |
| **故事熔炉** | 全透明提示词 + 三层记忆 | 知识底座记录 |
| **Subtxt** | Flow/Focus 双模式 | 知识底座记录 |

### 调研吸收的开源项目（3 个）

| 项目 | 收益 | 在 Æsir 中的落地 |
|------|------|----------------|
| **novel-os** | 42 门禁系统 + 指纹引擎 | `audit` 工具(零 API 门禁) + `fingerprint` 工具 |
| **story-inspiration-bundle** | Factorizer 因子 schema + Director Propositions | `director_pick` 工具 + 原子库结构参考 |
| **Dramatica NCP** | 叙事意图可移植 schema | `generate_intent_card` 设计参考 |

---

## 三、产品架构（三层递进）

```
Tier 0 (免费·病毒传播)
  ┌─────────────────────────────────────┐
  │ PWA 故事簿 (localStorage)           │
  │ 打开即用·零部署·零后端              │
  │ 快速捕获 + 故事时间线 + 分享卡片     │
  │ 导出/导入跨设备迁移                  │
  └─────────────┬───────────────────────┘
                │
Tier 1 (免费·个人化)
  ┌─────────────▼───────────────────────┐
  │ Coze Bot / ChatGPT GPTs             │
  │ 手机端对话·发散收敛审计写作         │
  │ 35 个故事能力·纯 LLM 驱动           │
  │ 生成内容复制到 PWA                  │
  └─────────────┬───────────────────────┘
                │
Tier 2 (桌面端·专业)
  ┌─────────────▼───────────────────────┐
  │ MCP Server (35 工具)                │
  │ 本地读写·批量分析·Ollama 支持       │
  │ sync 工具(CloudBase 云同步)         │
  │ Claude Desktop / Cursor 集成        │
  └─────────────────────────────────────┘
```

---

## 四、数据流

### Phase 1：纯本地（当前可用）

```
Coze Bot（手机）→ 生成故事 → 用户复制
                                     → PWA 自动检测剪贴板 → 存入 localStorage
              Ollama（桌面）→ 本地生成 → 直接入 local
```

### Phase 2：云端同步（需配 CloudBase）

```
Coze Bot（手机）→ 生成故事 → Coze HTTP POST → CloudBase
                                                   → PWA 自动拉取（15s 间隔）
                                                   → MCP sync 工具 → ~/.aesir/
```

---

## 五、当前就绪状态

| 维度 | 状态 |
|------|------|
| MCP Server | ✅ 35 工具, 语法通过, MCP + Ollama 双模式 |
| 42 门禁审计 | ✅ 零 API, 纯启发式, 12 本书库验证通过 |
| 风格指纹 | ✅ 节奏/对话/鸿沟/人称/触点/翻转率 |
| 发散-收敛 | ✅ 探索-利用平衡, 破坏约束版本 |
| 写作引擎 | ✅ fragment/chapter/rewrite/develop |
| 思想层 | ✅ 10 个导演命题匹配 |
| PWA 故事簿 | ✅ localStorage 模式, 导出/导入, CloudBase 预留 |
| Coze Bot | ⚠️ 配置已有, 5 工作流 steps 需手动补全 |
| 手机端对话 | ✅ Coze app + Bot |
| 中国部署 | ✅ CloudBase 方案 |
| 知识底座 | ✅ 14 章, 130+ 方法论 |

---

## 六、接下来的可选方向

用户量破千后的商业化：
- ¥39/月专业版（云端 API + 多设备同步 + 完整 Novel OS 写作）
- 蒸馏包市场（用户分享风格指纹）

产品优化：
- `aesir-coze-bot.json` 的工作流 steps 补全
- PWA 的剪贴板自动检测功能
- PWA 的 CloudBase 模式配通

**当前阶段最重要的事：让第一个真人用户跑通完整的"Coze 对话→生成→保存到 PWA"流程。**
