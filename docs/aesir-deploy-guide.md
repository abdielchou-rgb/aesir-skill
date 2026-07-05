# Æsir · 故事织机 — 手机端部署指南

---

## 方案一：Coze Bot（推荐，完全免费，零部署）

Coze 有手机 app（iOS/Android），安装 Bot 后可以直接在手机上对话。

### 部署步骤

**第 1 步：获取 Bot 配置**

文件在 `aesir-coze-bot.json`。包含 5 个工作流和 system prompt。

**第 2 步：在 Coze 平台创建 Bot**

1. 打开 coze.cn（国内）或 coze.com（国际）
2. 注册/登录 → 点击左侧"Bot"
3. 点击"创建 Bot"
4. Bot 名称：`Æsir 故事织机`
5. Bot 描述：`34 个故事能力——发散、收敛、审计、写作`
6. 点击"导入配置"→ 选择 `aesir-coze-bot.json`

**第 3 步：配置工作流**

导入后，5 个工作流会自动出现，但 steps 需要手动补全。每个工作流补一个 LLM 节点：

**diverge 工作流：**
- 添加 LLM 节点，模型选 Claude 3.5 Sonnet 或 GPT-4o
- System prompt：
```
你是一个创意思维伙伴。根据用户的模糊想法，生成5条不同的故事世界线。
其中1条标记为["尝试方向"]——故意偏离用户常规偏好的调性。

每条世界线格式：
—— 世界线 N ——
前提句：（一句话，包含主角、事件、冲突、代价）
调性：（冷峻写实/温暖治愈/黑色幽默/悬疑暗流/诗意思辨/激烈狂暴）
冲突：（身份冲突/资源冲突/价值观冲突/关系冲突/生存冲突/认知冲突）
钩子：（150-200字开场，让读者立刻被带入）

5条世界线必须在主角类型、冲突性质、情感调性上有显著差异。
```
- 输入：`{{idea}}`
- 输出：worldlines

**converge 工作流：**
- 添加 LLM 节点，model 同上
- System prompt：
```
你是一个故事编辑。基于选中的世界线和用户约束，写500-800字故事开场。
要求：保留三分之一悬念，关注感官细节和人物反应。
再加100-150字的[破坏约束版本]——违背用户的约束，走相反方向。
```
- 输入：`{{idea}}` `{{constraint}}`
- 输出：story + breakout

**audit 工作流：**
- 添加 code 节点，Node.js 运行
```javascript
function audit(text) {
  const issues=[];
  const sents=text.split(/[。！？.!?\n]/).filter(s=>s.trim().length>3);
  const paras=text.split('\n\n').filter(p=>p.trim());
  const sum=(t,ws)=>ws.reduce((c,w)=>c+t.split(w).length-1,0);
  const any=(t,ws)=>ws.some(w=>t.includes(w));
  const turn=sum(text,['但','却','然而','突然','竟','没想到']);
  if(turn<paras.length*0.3)issues.push({gate:'SVT-02',severity:'BLOCK',msg:'连续平坦-转折词密度不足'});
  const gap=sum(text,['没想到','出乎','原来','岂料','偏偏','谁知']);
  if(gap/sents.length*100<2)issues.push({gate:'GDA-01',severity:'BLOCK',msg:'鸿沟饥荒'+gap/sents.length*100});
  const ai=sum(text,['然而','值得注意的是','不可否认','不出所料','愈发']);
  if(ai>3)issues.push({gate:'LANG-05',severity:'WARN',msg:'AI腔'+ai+'处'});
  const desire=sum(text,['想要','希望','渴望','梦想','目标']);
  if(desire<2)issues.push({gate:'DDT-01',severity:'WARN',msg:'欲望模糊'});
  const touch=sum(text,['手','目光','眼神','沉默','颤抖','脸色']);
  if(touch<5)issues.push({gate:'TPE-02',severity:'WARN',msg:'触点不足'});
  const pp=sum(text,['碾压','反击','揭穿','震惊','逆袭','翻身','打脸']);
  if(pp<2)issues.push({gate:'PLE-01',severity:'WARN',msg:'爽点不足'});
  const first=text.slice(0,500);
  if(!any(first,['但','却','冲突','杀','逃','怒','秘密']))issues.push({gate:'G3-01',severity:'BLOCK',msg:'首章冲突缺'});
  const block=issues.filter(i=>i.severity==='BLOCK').length;
  const warn=issues.filter(i=>i.severity==='WARN').length;
  return{gates:issues,block,warn,score:Math.max(0,100-block*20-warn*10)};
}
```
- 输入：`{{text}}`
- 输出：result

**write 工作流、distill_style 工作流**同样添加 LLM 或 code 节点。

**第 4 步：设置 Bot 人格**

system prompt 已经内置在 JSON 中。核心内容：
- 34 个能力的触发词映射
- 关键约束（SG5、Storr、Cron、Maass、Pixar）
- 对话原则

**第 5 步：发布**

1. 点击右上角"发布"
2. 选择发布渠道：
   - Coze Store（推荐）——用户可以直接搜索安装
   - 微信小程序 —— 用户可以在微信内使用
   - API 方式 —— 你自己的应用调用
3. 获得分享链接：`https://www.coze.cn/s/xxxx`

### 手机端使用

1. 用户手机安装 Coze app（各应用商店搜索"Coze"）
2. 登录后搜索"Æsir 故事织机"
3. 安装 Bot
4. 对话：
   - "帮我想个故事" → 发散 5 条世界线
   - "选第 3 条" → 收敛故事片段
   - "审计这段"（粘贴文本）→ 42 门禁检查
   - "分析风格"（粘贴文本）→ 提取风格指纹
   - "写一章" → 写作

---

## 方案二：PWA 故事簿（辅助工具）

PWA 不做推理，只做三件事：
1. **快速捕获**：手机锁屏时记下零散念头
2. **故事时间线**：展示 agent 生成的内容（按日分组浏览）
3. **分享卡片**：一键复制到小红书/朋友圈

### 部署步骤

**方法：部署到 Vercel（免费）**

```bash
# 1. 安装 Vercel CLI
npm install -g vercel

# 2. 进入 frontend 目录
cd frontend/

# 3. 部署
vercel --prod
```

部署后会获得一个 URL，如 `https://aesir-storybook.vercel.app`。

**方法二：直接用 GitHub Pages**
1. 把 `frontend/index.html` 上传到 GitHub 仓库
2. 开启 GitHub Pages

用户访问 URL 即可使用，不需安装、不需注册、不需配置。

### 手机端使用

1. 用户用手机浏览器打开 URL
2. 点击"添加到主屏幕"（iOS Safari / Android Chrome）
3. 以后再打开就像原生 app 一样
4. 想记念头时打开 → 输入 → 保存
5. Agent 生成的内容手动粘贴即可

---

## 方案三：MCP Server（技术用户）

对于有本地 Python 环境的用户，MCP Server 是最完整的形态：

```bash
pip install mcp
python aesir-mcp-server.py
```

然后在 Claude Desktop 配置中加入：
```json
{
  "mcpServers": {
    "aesir": {
      "command": "python3",
      "args": ["path/to/aesir-mcp-server.py"]
    }
  }
}
```

---

## 三种方案对比

| | Coze Bot | PWA 故事簿 | MCP Server |
|---|---|---|---|
| **部署成本** | 零（导入即可） | 需部署到 Vercel | 需装 Python |
| **手机可用** | ✅ Coze app | ✅ 浏览器+PWA | ❌ 仅桌面 |
| **发散故事** | ✅ LLM 对话 | ❌ 不做推理 | ✅ 最完整 |
| **42门禁审计** | ✅ 内置 workflw | ❌ | ✅ |
| **风格指纹** | ✅ | ❌ | ✅ |
| **快速捕获** | ❌（需手动输入） | ✅ 一键记录 | ❌ |
| **分享卡片** | ❌ | ✅ | ❌ |
| **本地文件读写** | ❌ | ❌ | ✅ |
| **用户量门槛** | 零 | 需域名 | 需技术 |

---

## 推荐：两步走

**第 1 步（今天就可以做）：**
1. 在 Coze 平台导入 `aesir-coze-bot.json`，补全工作流 steps
2. 发布 Bot
3. 获得分享链接
4. 手机安装 Coze app → 安装 Bot → 开始对话

**第 2 步（有时间时做）：**
1. 把 PWA 部署到 Vercel
2. 获得公开 URL
3. 作为一个"故事簿"搭配使用

这样的组合覆盖了"手机随时用（Coze）+ 存档和分享（PWA）+ 桌面端完整能力（MCP）"三个场景。
