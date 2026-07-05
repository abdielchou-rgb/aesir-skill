# Æsir 故事织机 / Æsir Story Weaver

> 把模糊的念头变成完整的故事单元。一个 SKILL.md 文件，拖入任意 AI agent，零配置即可使用。

> Turn vague ideas into complete narrative units. One SKILL.md file. Drop into any AI agent. Zero config.

**中文** | [English](web/aesir-skill-en.md)

---

## 它做什么

1. **发散**——从模糊想法生成 5 条不同创意人格视角的世界线
2. **收敛**——生成 800-1200 字的完整故事单元，有开头有结尾
3. **延展**——沿未闭合线索续写，线索可跨多个单元
4. **合并**——自动检测单元间的线索交叉，融合为更大故事
5. **画布**——管理所有故事单元、开放线索和发展方向
6. **审计**——15 组启发式门禁，不分析文笔，只分析结构

---

## 使用方法

1. 下载 `web/aesir-skill.md`
2. 拖入任意 AI agent 的附件 / 知识区 / System Prompt
3. 说"帮我想个故事"

支持所有主流 AI agent 平台。

---

## 深度审计

配合 [文鉴 WenJian](https://github.com/wenjian/wenjian) 使用：

```bash
pip install wenjian
wenjian mcp-server
```

获得 131 道门禁 + 15 维风格指纹 + 爆款对标——全本地，零 API Key。

---

## 知识底座

吸收了 30+ 个理论来源：Story Grid、Save the Cat、Truby 对手设计、McKee 三层冲突、Cron 神经科学叙事、Maass 微张力、MICE Quotient、Yorke 5 幕辩证、12 种爽点原子、NarrativeLoom 多智能体等。

附完整知识底座文档：`docs/aesir-knowledge-base.md`（668 行，14 章，130+ 方法论来源）。

---

## 文件结构

```
aesir-skill/
├── README.md                    ← 你在这里
├── web/aesir-skill.md           ← 主 SKILL 文件（拖入 agent 即可用）
├── docs/
│   ├── aesir-knowledge-base.md  ← 完整知识底座
│   ├── aesir-summary-report.md  ← 阶段性总结
│   └── ...                      ← 设计讨论文档
└── tools/                       ← 旧版 Python 工具（已废弃，由文鉴接管）
```

---

## 协议

MIT License. 零配置，零费用，零 API Key。

*每个想讲故事的人，都该有一个不嫌麻烦的搭档。*
