# Æsir Story Weaver

> Turn vague ideas into complete narrative units.
> One SKILL.md file. Drop into any AI agent. Zero config.

[中文](README.zh.md)

---

## What It Does

1. **Diverge** — A half-formed thought splits into 5 worldlines from 5 distinct creative personas
2. **Converge** — Pick one. Get a complete 800–1200 word narrative unit with beginning, middle, and end
3. **Extend** — Follow open threads forward. Threads can span multiple units
4. **Merge** — Auto-detects thread crossovers between units. Fuse them into larger stories
5. **Canvas** — Manage all units, open threads, and possible directions in one view
6. **Audit** — 15 built-in structural gates. Not checking prose — checking story architecture

---

## Why This Exists

Everyone has stories in their head. The person on the subway. The "what if" that keeps you up. Most never get written — not because you can't write, but because nobody helped you turn that foggy feeling into a direction you can actually start from.

Most AI writing tools are ghostwriters. They generate text and walk away. The output reads at 61% completion rate of human writing, with 55% emotional resonance. It gets rejected by platform AI detectors before anyone reads it.

Æsir is not a ghostwriter. It's a writer's room in one file. You're the director. It's the room.

---

## How to Use

1. Download `web/aesir-skill-en.md` (English) or `web/aesir-skill.md` (中文)
2. Drop it into any AI agent's attachments / knowledge base / system prompt
3. Say "help me think of a story"

Works with all major AI agent platforms. No API keys. No Python. No sign-up.

---

## Deep Audit

Pair with [WenJian](https://github.com/wenjian/wenjian):

```bash
pip install wenjian
wenjian mcp-server
```

131 structural gates + 15-dimension style fingerprinting + bestseller benchmarking. Fully local. Zero API keys.

---

## What's Under the Hood

30+ narrative theory sources, each mapped to a specific behavior in the system:

- **Structural layer** — Story Grid's 5 commandments, Save the Cat's 15 beats, Pixar's Story Spine
- **Character & conflict layer** — Truby's opponent design, McKee's three-layer conflict, Egri's bone structure
- **Micro-craft layer** — Cron's neuroscience of story (show, never explain), Maass's micro-tension (every page needs something unexplained), Swain's MRU chain
- **Web/serial fiction layer** — 12 pleasure point atoms catalogued from hundreds of top-ranked webnovels, genre-specific reader contracts, platform survival guide
- **Academic frontier** — NarrativeLoom's multi-persona creative divergence (CHI 2026), DiriGent's dynamic belief systems (AAAI 2025)

Full knowledge base: `docs/aesir-knowledge-base.md` (668 lines, 14 chapters, 130+ methodology sources).

---

## File Structure

```
aesir-skill/
├── README.md                    ← You're here (English)
├── README.zh.md                 ← Chinese version
├── web/
│   ├── aesir-skill-en.md        ← English SKILL (drop into AI agent)
│   └── aesir-skill.md           ← Chinese SKILL
├── docs/                        ← Design docs & knowledge base
├── tools/                       ← Legacy Python tools (deprecated, now covered by WenJian)
└── aesir-writing/               ← Legacy orchestrator (deprecated)
```

---

## License

MIT. Zero config. Zero cost. Zero API keys.

*Everyone with a story to tell deserves a partner who won't get tired.*
