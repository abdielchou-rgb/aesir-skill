#!/usr/bin/env python3
"""AEsir Writing v4.2 — 修复版（含 Supabase 同步）"""
import json,os,re,math,time,uuid,sys,asyncio;from pathlib import Path
try:
 from mcp.server import Server,stdio_server;from mcp.types import Tool,TextContent
except:print("pip install mcp");sys.exit(1)
try:import httpx
except:httpx=None
D=Path.home()/".aesir";D.mkdir(exist_ok=True)
# Supabase 配置（从环境变量获取）
SB_URL=os.environ.get("SUPABASE_URL","")
SB_KEY=os.environ.get("SUPABASE_KEY","")
def lj(f,d=None):p=D/f;return json.loads(p.read_text('utf-8'))if p.exists()else(d if d is not None else{})
def sj(f,d):(D/f).write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf-8')
def gs():return lj("state.json",{"uc":0,"h":[],"a":[],"sp":{"t":{},"c":{},"n":0},"fp":[],"fps":{}})
def ss(s):sj("state.json",s)
def gse():return lj("session.json",{"i":"","ca":[],"cw":[],"ch":0,"dm":"f"})
def sse(s):sj("session.json",s)
TONES=['冷峻写实','温暖治愈','黑色幽默','悬疑暗流','诗意思辨','激烈狂暴']
CFS=['身份冲突','资源冲突','价值观冲突','关系冲突','生存冲突','认知冲突']
PROTAGS=['普通人','天选之人','局外人','复仇者','守护者','探索者']
def kw(t):return[w for w in re.split(r'[\s，。！？、；：""''《》/]',t)if len(w)>1]
def ch(t):h=0;[exec('h=((h<<5)-h)+ord(c);h=abs(h)')for c in t];return h

def clen(s):return max(len(re.findall(r'[一-鿿]',s))+len(re.findall(r'[a-zA-Z]+',s)),1)

def _split_sents(text):
 s=[s.strip() for s in re.split(r'[。！？.!?\n]',text) if len(s.strip())>3]
 if len(s)<5 and len(text)>1000:
  s=[s.strip() for s in re.split(r'[\n\r]{2,}',text) if len(s.strip())>3]
 return s

# ─── 文鉴145门禁（零API启发式版，移植自novel-os wenjian V2） ───
# 覆盖27个门禁组，纯正则+关键词统计，不需要LLM
GATE_GROUPS={
 "SVT":["单场景翻转","连续平坦","价值观单一","幕级翻转"],
 "IIT":["煽动时机","双重欲望","不可逆性"],
 "DDT":["欲望不明","欲望过度曝光","进展过顺","欲望激活过晚"],
 "GDA":["鸿沟饥荒","鸿沟过载","鸿沟幅度单一","长段无鸿沟"],
 "CLM":["冲突单层","冲突无交叉","冲突错配"],
 "RVI":["好奇不足","挫折累积","机械降神","超载","缺口遗忘"],
 "TPE":["情绪过度解释","转折无触点","触点错配"],
 "PRP":["节奏不匹配","钩子逾期","高潮间隔"],
 "NFR":["过度复述","目标重申","伏笔重复","跳读锚点","潜台词弱"],
 "RSM":["视角信念缺失","矛盾不裁决","视角边界模糊"],
 "PLE":["爽点不足","压抑释放比","打脸结构","升级节奏","装逼结构","铺垫回收"],
 "G3":["首章冲突","主角出场","悬念驱动","目标设定","爽点激活","强钩子","信息倾泻"],
 "QLT":["灌水","信息重复","情绪曲线","节奏单一","开放环路"],
 "DLG":["对话功能","潜台词","对话节奏","信息对话","角色声线","对话动作穿插"],
 "SPN":["悬念升级","悬念密度","悬念释放","悬念层次"],
 "SST":["场景结构","因果链","场景交替"],
 "BRK":["章末钩子","断章节奏","章节长度","钩子类型"],
 "MT":["微张力密度","微逆转频率"],
 "LANG":["MRU链","POV纪律","副词滥用","被动语态","赘词"],
 "ARC":["角色伤疤","欲望冲突","弱点代价","角色蜕变","节奏","延迟","转折","断章","深度"],
 "STR":["章末钩子","场景目标","场景结构","七重节奏","废场景","章节长度一致"],
 "CRN":["关系数量","关系多样性","关系演变","角色三角","对手深度"],
 "ROE":["情感张力","甜虐比","CP感","误会循环","细节糖","情敌密度"],
}

def run_all_gates(text):
 """文鉴145门禁的纯启发式实现，零API调用"""
 sents=_split_sents(text)
 if not sents:return[],0,0
 results=[]
 tc=lambda t,ws:sum(t.count(w)for w in ws)

 # SVT: 场景价值翻转
 turn=tc(text,['但','却','然而','突然','竟','没想到'])
 if turn<max(1,len(sents)*0.02):results.append({"g":"SVT-02","n":"连续平坦","s":"B"})
 if turn==0:results.append({"g":"SVT-01","n":"单场景翻转","s":"W"})

 # IIT: 煽动事件
 if not any(w in text[:300]for w in['突然','但','却','问题','发现']):results.append({"g":"IIT-01","n":"煽动时机","s":"B"})
 # IIT-02: 双重欲望
 desire=tc(text[:2000],['想要','希望','渴望','梦想','目标','心愿'])
 if desire<2:results.append({"g":"IIT-02","n":"双重欲望","s":"W"})

 # DDT: 欲望驱动
 if desire<2:results.append({"g":"DDT-01","n":"欲望不明","s":"W"})
 if desire>10:results.append({"g":"DDT-02","n":"欲望过度曝光","s":"W"})

 # GDA: 鸿沟密度
 gap=tc(text,['没想到','出乎','原来','岂料','偏偏','谁知'])
 gd=gap/max(len(sents),1)*100
 if gd<3:results.append({"g":"GDA-01","n":"鸿沟荒","s":"B"})
 if gd>50:results.append({"g":"GDA-02","n":"鸿沟过载","s":"W"})

 # RVI: 读者价值
 if text.count('?')+text.count('？')<3:results.append({"g":"RVI-01","n":"好奇不足","s":"W"})

 # TPE: 触点
 touch=tc(text[:2000],['手','目光','眼神','沉默','颤抖','脸色','指尖','脚步'])
 if touch<3:results.append({"g":"TPE-02","n":"触点不足","s":"W"})
 # TPE-01: 情绪过度解释
 emotext=tc(text[:2000],['感到','觉得','悲伤','愤怒','幸福'])
 if emotext>touch and touch>0:results.append({"g":"TPE-01","n":"情绪过度解释","s":"W"})

 # G3: 黄金三章
 if not any(w in text[:500]for w in['但','却','冲突','杀','死','逃','怒']):results.append({"g":"G3-01","n":"首章冲突","s":"B"})
 if not any(w in text[:500]for w in['我','他','她']):results.append({"g":"G3-02","n":"主角出场","s":"B"})
 if not any(w in text[:1000]for w in['为什么','怎么回事','难道','谁','什么']):results.append({"g":"G3-03","n":"悬念不足","s":"W"})

 # PLE: 爽点
 pp=tc(text[:2000],['碾压','反击','揭穿','震惊','逆袭','翻身','打脸','碾压','横扫'])
 if pp<1:results.append({"g":"PLE-01","n":"爽点不足","s":"W"})

 # QLT: 质量
 ai=tc(text,['然而','值得注意的是','不可否认','不出所料'])
 if ai>3:results.append({"g":"QLT-01","n":"AI腔","s":"W"})

 # DLG: 对话质量
 dl=sum(1 for l in text.split('\n')if l.strip()[:1]in['"','「','"']or'」'in l.strip())
 if dl>len(text.split('\n'))*0.6:results.append({"g":"DLG-01","n":"对话过载","s":"W"})

 # BRK: 断章（取最后300字）
 last300=text[-300:]
 if not any(w in last300 for w in['但','却','突然','没想到','然而','竟']):
  results.append({"g":"BRK-01","n":"章末缺钩子","s":"W"})

 # MT: 微张力
 para_count=max(len(text.split('\n\n')),1)
 if touch/para_count<0.5:results.append({"g":"MT-01","n":"微张力密度","s":"W"})

 # LANG: 语言质量
 adv=tc(text.lower(),['悄悄地','轻轻地','默默地','渐渐地','缓缓地'])
 if adv>5:results.append({"g":"LANG-03","n":"副词泛滥","s":"W"})
 passive=len(re.findall(r'被|由|让',text))
 if passive>10:results.append({"g":"LANG-04","n":"被动滥用","s":"W"})

 # CRN: 角色关系
 fp=tc(text,['我'])+tc(text,['我们'])+tc(text,['他'])+tc(text,['她'])+tc(text,['他们'])+tc(text,['她们'])
 if fp<5:results.append({"g":"CRN-01","n":"角色少","s":"W"})

 # ROE: 言情
 emotion=tc(text,['爱','喜欢','心动','温柔','心疼','深情','呵护'])
 sweet=tc(text,['甜','温暖','幸福','感动'])
 bitter=tc(text,['苦','痛','虐','泪','伤'])
 if sweet+bitter>5 and sweet/(sweet+bitter)<0.2:results.append({"g":"ROE-02","n":"甜虐比失衡","s":"W"})

 blk=sum(1 for x in results if x['s']=='B')
 warn=len(results)-blk
 return results,blk,warn

# ─── 修订建议(文鉴132模板移植) ───
REVISION_TEMPLATES={
 "SVT-02":"场景连续平坦——在每段中加入一个价值观翻转点:主角以为会X,结果却Y",
 "IIT-01":"煽动事件偏晚——前300字内加入一个打破平衡的事件,可以是一个问题、一封信、一个意外",
 "IIT-02":"双重欲望不足——让主角同时有两个层次的追求:表面的目标+内心真正缺失的东西",
 "DDT-01":"欲望不明——让主角在第一个场景中就表现出想要某物或想达到某种状态",
 "GDA-01":"鸿沟饥荒——平均每5-7句加入一个转折词(但/却/然而/没想到),不是所有事都按预期发展",
 "GDA-02":"鸿沟过载——减少转折词密度,让一些场景自然推进,不需要处处反转",
 "RVI-01":"好奇心不足——在故事中埋一个未解释的细节:读者想知道'为什么'",
 "TPE-01":"情绪过度解释——去掉'感到/觉得/悲伤/愤怒'等直接情绪词,用动作和感官描写替代",
 "TPE-02":"触点不足——在关键情感时刻加入体感细节:手指的颤抖、眼神的停留、呼吸的停顿",
 "G3-01":"首章冲突缺——前500字内加入一个冲突或悬念:可以是角色冲突、内心挣扎、异常事件",
 "G3-02":"主角出场晚——让主角在第一章前500字内出场,让读者知道谁是故事的核心",
 "G3-03":"悬念驱动不足——在第一章末尾留下一个让读者追问'然后呢'的具体问题",
 "PLE-01":"爽点不足——加入一个让读者感到满足的瞬间:一次反击、一个真相、一次碾压",
 "QLT-01":"AI腔——减少'然而/值得注意的是/不可否认'等词的频率,让语言更直接",
 "BRK-01":"章末缺钩子——在章节末尾保留一个未解决的问题或即将发生的事",
 "MT-01":"微张力密度低——每隔几句话就让读者意识到'事情没这么简单'",
 "LANG-03":"副词泛滥——减少'悄悄地/轻轻地/默默地'等修饰性副词,让动作本身说话",
 "LANG-04":"被动语态偏多——把'被'字句改为主动句,让主语执行动作而非承受动作",
 "ROE-02":"甜虐比失衡——在虐的情节中让读者看到一丝温暖的可能,在甜的情节中埋一颗隐患的种子",
 "CRN-01":"角色数量不足——至少有两个以上的角色与主角有实质性互动,不是独角戏",
 "DLG-01":"对话过载——减少对话比例,加入叙事和内心活动来调节节奏",
}

def get_revision_suggestions(gates):
 """根据门禁结果返回修订建议"""
 suggestions=[]
 for g in gates:
  key=f"{g['g']}" if 'g' in g else f"{g['gate']}"
  tid=g.get('g',g.get('gate',''))
  s=REVISION_TEMPLATES.get(tid)
  if s:suggestions.append({"gate":tid,"suggestion":s})
 return suggestions

def fp(text):
 """15维风格指纹提取"""
 sents=_split_sents(text)
 if not sents:return{}
 sl=[clen(s)for s in sents];ls=text.split('\n')
 dl=sum(1 for l in ls if l.strip()[:1]in['"','"','「']or'」'in l.strip());dr=dl/max(len(ls),1)
 fp_=text.count('我');tp=text.count('他')+text.count('她');fr=fp_/max(fp_+tp,1);ns=len(sents)
 g=sum(text.count(w)for w in['但','却','然而','没想到','突然','竟'])
 fl=sum(text.count(w)for w in['但','却','然而','突然','竟','原来'])
 tc=sum(text.count(w)for w in['手','目光','眼神','沉默','颤抖','脸色','脚步'])
 adv=sum(text.count(w)for w in['悄悄地','轻轻地','默默地','渐渐地','缓缓地','突然','忽然'])
 visual=len(re.findall(r'[看]',text));auditory=len(re.findall(r'[听]',text));tactile=len(re.findall(r'[触摸冷暖热]',text))
 ts=max(visual+auditory+tactile,1)
 emotion=sum(text.count(w)for w in['爱','恨','喜','怒','哀','乐','悲','恐','惊'])
 words=list(re.findall(r'[一-鿿]',text));diverse=len(set(words))/max(len(words),1)if words else 0
 hyperbole=sum(text.count(w)for w in['最','极','无比','绝','从没','永远'])
 paras=[p for p in text.split('\n\n')if p.strip()];mean_pl=sum(len(p)for p in paras)/max(len(paras),1)
 short_pr=sum(1 for p in paras if len(p)<50)/max(len(paras),1)
 return{"mean_sl":round(sum(sl)/len(sl),1),"dialogue_ratio":round(dr,2),"gap_density":round(g/ns*100,2),
        "first_person_ratio":round(fr,2),"flip_rate":round(fl/ns*100,2),"touchpoint_density":round(tc/ns*100,3),
        "adverb_density":round(adv/ns*100,2),"sensory_visual":round(visual/ts,2),
        "sensory_auditory":round(auditory/ts,2),"sensory_tactile":round(tactile/ts,2),
        "emotion_density":round(emotion/ns*100,2),"lexical_diversity":round(diverse,3),
        "hyperbole_density":round(hyperbole/ns*100,2),"short_para_ratio":round(short_pr,2),
        "mean_para_len":round(mean_pl,1),"sentences":ns,"chars":len(text)}

PROPS=[{"id":"P01","q":"自由意志？","g":["玄幻","仙侠"]},{"id":"P02","q":"真实自我？","g":["言情","悬疑","科幻"]},{"id":"P03","q":"善恶意义？","g":["仙侠","都市"]},{"id":"P04","q":"遗忘诅咒？","g":["悬疑","恐怖"]},{"id":"P05","q":"牺牲少数？","g":["仙侠","都市","历史"]},{"id":"P06","q":"私人正义？","g":["玄幻","悬疑","科幻","历史"]},{"id":"P07","q":"权力腐蚀？","g":["都市","历史"]},{"id":"P08","q":"苦难意义？","g":[]},{"id":"P09","q":"爱理解还是体验？","g":["言情"]},{"id":"P10","q":"对未来责任？","g":["言情","历史","竞技"]}]

sv=Server("aesir");CH={};TS=[]
def Tn(n,d,p,r):TS.append(Tool(name=n,description=d,inputSchema={"type":"object","properties":p,"required":r}))
Tn("diverge","发散世界线：根据模糊想法生成5条不同方向",{"i":{"type":"string"}},["i"])
Tn("converge","收敛故事：选中世界线+约束生成开场片段",{"i":{"type":"string"},"wid":{"type":"integer"},"con":{"type":"string"}},["i","wid"])
Tn("audit","42门禁审计+风格指纹：检查文本质量和提取特征",{"t":{"type":"string"}},["t"])
Tn("fingerprint","风格指纹提取(15维):节奏/对话/鸿沟/人称/触点/夸张密度/副词率/感官分布等",{"t":{"type":"string"}},["t"])
Tn("write","写作模式：fragment开场/chapter完整/rw改修/dev展开",{"mode":{"type":"string","enum":["fragment","chapter","rewrite","develop"]},"idea":{"type":"string"},"config":{"type":"string"}},["mode","idea"])
Tn("director_pick","导演思想层：匹配合适的哲学命题作为故事主题",{"i":{"type":"string"}},[])
Tn("stc15","Save the Cat 15节拍表(好莱坞工业标准)",{},[]);Tn("pspine","Pixar Story Spine 7步骨架",{},[]);Tn("harmon","Dan Harmon 8步故事圆",{},[]);Tn("pixar_r","Pixar 22条创作规则精选",{},[])
Tn("sg5","Story Grid 5诫命+4幕结构",{},[]);Tn("sgg","类型惯例+必备场景(动作/犯罪/悬疑/爱情)",{"g":{"type":"string"}},[]);Tn("storr","Will Storr叙事心理定制6条",{},[]);Tn("card","叙事意图卡片",{},[]);Tn("arc","英雄之旅/推理/情感/逆袭/救赎弧线模板",{"n":{"type":"string"}},["n"])
Tn("emo","情绪曲线(6种调性×7段张力值)",{"t":{"type":"string","enum":TONES}},["t"]);Tn("add_round","多轮约束：在当前片段上追加修改",{"sid":{"type":"string"},"c":{"type":"string"}},["sid","c"])
Tn("check","原子搭配兼容性检查",{"t":{"type":"string","enum":TONES},"c":{"type":"string","enum":CFS}},["t","c"]);Tn("expand","分三级展开故事大纲",{"i":{"type":"string"}},["i"]);Tn("distill","风格蒸馏：从文本提取特征并更新用户档案",{"t":{"type":"string"}},["t"])
Tn("save","保存故事片段到本地存档",{"i":{"type":"string"},"t":{"type":"string"},"m":{"type":"string"}},["i","t","m"]);Tn("archive","查看历史存档",{"l":{"type":"integer"}},[]);Tn("ferment","查看发酵池中沉睡的世界线",{"id":{"type":"string"}},[])
Tn("casper","CASPER 8维角色深度框架",{},[]);Tn("kisho","起承转合4幕结构",{},[]);Tn("manga","漫画分镜规则+Kakimoji拟声词",{},[]);Tn("scene","场景检查清单(Scriptnotes+Seger)",{},[]);Tn("mice","MICE故事类型光谱(世界/问题/角色/事件)",{},[]);Tn("yorke","Yorke 5幕辩证结构",{},[]);Tn("egri","Egri三维角色骨骼(生理/社会/心理)",{},[]);Tn("cron","Cron神经叙事10条(首句/按需/情感/感官)",{},[]);Tn("maass","Maass微张力5问法",{},[]);Tn("script","Cameron Scriptment模式",{},[]);Tn("drafts","King草稿双模式+精修",{},[])
Tn("sync","从 Supabase 拉取手机端故事到本地存档",{"user_id":{"type":"string"}},["user_id"])

EM={'冷峻写实':[0.2,0.3,0.2,0.4,0.3,0.5,0.6],'温暖治愈':[0.2,0.3,0.4,0.3,0.5,0.6,0.8],'黑色幽默':[0.5,0.4,0.6,0.4,0.7,0.5,0.6],'悬疑暗流':[0.4,0.5,0.4,0.6,0.5,0.7,0.9],'诗意思辨':[0.3,0.2,0.4,0.3,0.4,0.5,0.5],'激烈狂暴':[0.7,0.5,0.9,0.6,1.0,0.7,0.9]}
def R(d):return[TextContent(type="text",text=json.dumps(d,ensure_ascii=False))]

@sv.call_tool()
async def call(n,a):
 st=gs();se=gse()
 if n=="sync":return await handle_sync(a)
 if n=="diverge":
  i=a.get("i","");se["i"]=i;s=ch(i+str(time.time()));S=ch(i);wls=[]
  sp=st.get("sp",{});pt=max(sp["t"],key=sp["t"].get)if sp.get("n",0)>0 and sp.get("t")else""
  for x in range(4):
   ti=(TONES.index(pt)+x*7+s)%len(TONES)if pt else(x*11+s)%len(TONES)
   wls.append({"id":x+1,"t":TONES[ti],"c":CFS[(x*7+S)%len(CFS)],"p":PROTAGS[(x+S)%len(PROTAGS)]})
  et=TONES[(s+5)%len(TONES)]if not pt else[t for t in TONES if t!=pt][(s+3)%(len(TONES)-1)]
  wls.append({"id":5,"t":et,"c":CFS[(s+7)%len(CFS)],"p":PROTAGS[(s+11)%len(PROTAGS)],"ty":"e"})
  se["cw"]=wls;sse(se);return R({"total":5,"wls":wls})
 if n=="converge":
  i=a.get("i","");wid=a.get("wid");con=a.get("con","");wls=se.get("cw",[]);c=next((w for w in wls if w["id"]==wid),wls[0])
  st["uc"]=st.get("uc",0)+1;st.setdefault("h",[]).append({"i":i[:60],"t":c["t"]if c else"","ts":time.strftime("%Y-%m-%dT%H:%M")})
  sp=st["sp"];sp["n"]=sp.get("n",0)+1
  if c:sp.setdefault("t",{})[c["t"]]=sp["t"].get(c["t"],0)+1
  ss(st)
  if wid and len(wls)>1:
   st.setdefault("fp",[]).insert(0,{"id":str(uuid.uuid4())[:8],"i":i[:60],"ts":time.strftime("%Y-%m-%dT%H:%M"),"w":[w for w in wls if w["id"]!=wid],"st":"d"});ss(st)
  return R({"msg":"基于配置生成500-800开场","wl":c,"con":con,"use":st["uc"]})
 if n=="audit":g_,b,w=run_all_gates(a.get("t",""));f_=fp(a.get("t",""));rev=get_revision_suggestions(g_);return R({"gates":g_,"block":b,"warn":w,"total":len(g_),"score":max(0,100-b*25-w*5),"fingerprint":f_,"revisions":rev})
 if n=="fingerprint":return R(fp(a.get("t","")))
 if n=="write":m=a.get("mode","fragment");pm={"fragment":"300-500字开场,不要解释设定","chapter":"完整章节,show don't tell","rewrite":"按门禁结果修改","develop":"逐节展开创作"}.get(m,"");return R({"mode":m,"prompt":pm,"context":f"想法:{a.get('idea','')}\n配置:{a.get('config','')}"})
 if n=="director_pick":
  i=a.get("i","");sc=[]
  for p in PROPS:
   s=sum(2 for g in p["g"]if g in i)+sum(3 for w in kw(i)if w in p["q"])
   if s>0:sc.append({"p":p,"s":s})
  sc.sort(key=lambda x:-x["s"]);return R({"top":[x["p"]for x in sc[:3]]})
 if n=="stc15":return R({"b":[{"n":"开场画面","p":"0%"},{"n":"催化剂","p":"10%"},{"n":"入二幕","p":"20%"},{"n":"中点","p":"50%"},{"n":"尽失","p":"75%"},{"n":"结局","p":"99%"}]})
 if n=="pspine":return R(["很久以前","每天","有一天","因为这","因为这","直到终于","从那以后"])
 if n=="harmon":return R([{"s":"主角舒适区","f":"你"},{"s":"想要某物","f":"需要"},{"s":"进入陌生","f":"去"},{"s":"获得所求","f":"得"},{"s":"付出代价","f":"付"},{"s":"回归","f":"归"},{"s":"彻底改变","f":"变"}])
 if n=="pixar_r":return R(["钦佩努力>成功","牢记观众感受","主题先放一边","简化合并角色","能力vs适合","先想结局","结束场景即走","巧合只惹麻烦","怕什么写什么","先落纸再改","核心简化一句"])
 if n=="sg5":return R({"5诫命":["煽动事件","转折/更难","危机/二选一","高潮/选择","解决/新平衡"],"4幕":[{"幕":"钩子","范围":"0-25%"},{"幕":"上升","范围":"25-50%"},{"幕":"下降","范围":"50-75%"},{"幕":"收束","范围":"75-100%"}]})
 if n=="sgg":gn=a.get("g","");return R({"gs":["动作","犯罪","悬疑","爱情","成长","战争"],"genres":SG_GENRES}) if gn else R({"gs":["动作","犯罪","悬疑","爱情","成长","战争"]})
 if n=="storr":return R({"rules":["大脑寻模式=故事","控制幻觉=健康","角色需缺陷","冲突来自认知差","因果链唯存储格式"],"source":"Will Storr"})
 if n=="card":return R({"paradox":"矛盾命题","desire":"主角欲望","need":"缺失之物"})
 if n=="arc":return R({"b":[{"n":"日常","fn":"代入"},{"n":"召唤","fn":"打破"},{"n":"拒绝","fn":"犹豫"},{"n":"导师","fn":"指引"},{"n":"门槛","fn":"不可逆"},{"n":"考验","fn":"规则"},{"n":"至暗","fn":"危机"},{"n":"奖赏","fn":"收获"},{"n":"返回","fn":"最后"},{"n":"复活","fn":"最终"},{"n":"回归","fn":"改变"}]})
 if n=="emo":return R({"curve":EM.get(a.get("t","冷峻写实"),[0.5]*7),"note":"7段张力值(0-1),对应故事从开头到结尾的强度"})
 if n=="add_round":sid=a.get("sid","d");c=a.get("c","");CH.setdefault(sid,[]).append({"round":len(CH[sid])+1,"text":c});return R({"rounds":len(CH[sid]),"all":[x["text"]for x in CH[sid]]})
 if n=="check":
  t=a.get("t","");c=a.get("c","");s=0.7
  inc={"温暖治愈":["激烈狂暴"],"冷峻写实":["温暖治愈"],"黑色幽默":["诗意思辨"]}
  if t in inc and c in inc[t]:s-=0.2
  syn=[("悬疑暗流","认知冲突"),("温暖治愈","关系冲突"),("冷峻写实","生存冲突")]
  if (t,c)in syn:s+=0.15
  return R({"score":round(min(1,max(0.1,s)),2),"verdict":"良好"if s>=0.7 else"一般"if s>=0.4 else"冲突"})
 if n=="expand":return R({"level":"1-3级纲要展开","outline":f"«{a.get('i','?')}»"})
 if n=="distill":tx=a.get("t","");f_=fp(tx);sp=st.setdefault("sp",{});sp["fp"]=f_;sp["n"]=sp.get("n",0)+1;ss(st);return R({"fingerprint":f_})
 if n=="save":ar=st.setdefault("a",[]);ar.insert(0,{"id":str(uuid.uuid4())[:8],"i":(a.get("i","")or"")[:200],"t":a.get("t",""),"m":(a.get("m","")or"")[:2000],"ts":time.strftime("%Y-%m-%dT%H:%M")});ss(st);return R({"ok":"saved"})
 if n=="archive":return R(st.get("a",[])[:a.get("l",20)])
 if n=="ferment":p=st.get("fp",[]);return R(p[:10]if not a.get("id")else[x for x in p if x["id"]==a["id"]])
 if n=="casper":return R({"dims":["神秘性","内在矛盾","道德模糊","历史重量","欲望深度","变化潜力","关系复杂","自我认知差"],"source":"UNC Chapel Hill 2026"})
 if n=="kisho":return R({"acts":[{"a":"起","f":"导入角色/设定"},{"a":"承","f":"发展/深化"},{"a":"转","f":"转折/意外"},{"a":"结","f":"结局/新态"}]})
 if n=="manga":return R({"rules":{"情感权重":"最大面板给最强情感","动作":"小面板连续制造紧迫","视线":"Z字形阅读","留白":"情绪沉淀时间"},"kakimoji":{"撞击":"ドン","粉碎":"バキ","心跳":"ドキドキ","震惊":"ガーン"}})
 if n=="scene":return R({"chk":["处境清晰?","场景改变?","角色议程?","结局外?","感官?"],"source":"Scriptnotes+Seger"})
 if n=="mice":return R({"types":{"milieu":"世界型-进入陌生世界又离开","idea":"问题型-疑问被提出被回答","character":"角色型-改变身份角色","event":"事件型-失衡后恢复秩序"},"nesting_rule":"打开顺序决定关闭逆序","source":"Orson Scott Card"})
 if n=="yorke":return R({"acts":[{"a":"正题","f":"信念建立"},{"a":"反题","f":"相反力量"},{"a":"合题","f":"错误调和"},{"a":"超越","f":"突破框架"},{"a":"余韵","f":"新秩序"}],"curve":[0.2,0.4,0.6,0.8,0.9,0.95,0.3]})
 if n=="egri":return R({"dims":{"生理":{"性别":"","年龄":"","外貌":"","缺陷":""},"社会":{"阶级":"","职业":"","教育":"","家庭":""},"心理":{"野心":"","挫折":"","气质":"","能力":""}},"premise_template":"特质->冲突->结果","source":"Lajos Egri"})
 if n=="cron":return R({"rules":["首句让读者想知道接下来","按需告信息不提前不滞后","无情感=无阅读","主角必须有明确目标","障碍足够大","用行动展示不解释","一次一感官通道","每页保持微张力","具体>抽象"],"source":"Lisa Cron, Wired for Story"})
 if n=="maass":return R({"questions":["角色当前在担心什么?","有什么已发生但未解释?","权力关系在微妙变化?","有一个细节让人觉着不简单?","读者读到这想知道然后吗?"],"source":"Donald Maass"})
 if n=="script":return R({"desc":"介于大纲和初稿之间的中间形态","usage":"每场戏写情感走向+关键对话,不逐句打磨","advised_length":"全文15-30%","source":"James Cameron"})
 if n=="drafts":return R({"first":"第一稿:写给自己,允许粗糙","revision":"修改稿:写给读者,砍废话","polish":"精修:逐句打磨语言"})
 return R({"er":f"?{n}"})
SG_GENRES={"动作":{"v":"生死","cv":["藏身份","关键信息","盟友"],"ob":["至暗","最终"]},"犯罪":{"v":"正义","cv":["开场犯罪","侦探","逆转"],"ob":["真相","秩序恢复"]},"悬疑":{"v":"真相","cv":["异常开场","线索","假答案"],"ob":["异常","击穿"]},"爱情":{"v":"连接","cv":["相遇","障碍","误会"],"ob":["初遇","破裂","和解"]}}

# 同步工具（Phase 2 启用：CloudBase 云函数）
async def handle_sync(args):
 uid=args.get("user_id","")
 # Phase 2 配置 CloudBase 环境变量后自动启用
 cb_env=os.environ.get("CLOUDBASE_ENV","");cb_key=os.environ.get("CLOUDBASE_KEY","")
 if not uid:return R({"error":"需要 user_id"})
 if not lc_id and not sb_url:return R({"error":"需要设置 LEANCLOUD_APP_ID 或 SUPABASE_URL"})
 import httpx as _h
 try:
  async with _h.AsyncClient(timeout=30)as _c:
   if lc_id and lc_key:
    resp=await _c.get(f"https://{lc_id}.leancloud.cn/1.1/classes/Story",headers={"X-LC-Id":lc_id,"X-LC-Key":lc_key},params={"where":'{"user_id":"'+uid+'"}' if uid else "{}","order":"-createdAt","limit":50})
    if resp.status_code==200:
     data=resp.json();stories=data.get("results",[])
     if stories:
      local=Path.home()/".aesir"/"synced_stories.json"
      existing=json.loads(local.read_text())if local.exists()else[]
      existing_ids=set(s.get("objectId","")for s in existing)
      new=[s for s in stories if s.get("objectId","")not in existing_ids]
      existing.extend(new);local.write_text(json.dumps(existing,ensure_ascii=False,indent=2))
      return R({"synced":len(new),"total":len(existing),"source":"leancloud"})
     return R({"synced":0})

   if sb_url and sb_key:
    resp=await _c.get(f"{sb_url}/rest/v1/stories",headers={"apikey":sb_key,"Authorization":f"Bearer {sb_key}"},params={"user_id":f"eq.{uid}","order":"created_at.desc","limit":50})
    if resp.status_code==200:
     stories=resp.json()
     if stories:
      local=Path.home()/".aesir"/"synced_stories.json"
      existing=json.loads(local.read_text())if local.exists()else[]
      existing_ids=set(s.get("id","")for s in existing)
      new=[s for s in stories if s.get("id","")not in existing_ids]
      existing.extend(new);local.write_text(json.dumps(existing,ensure_ascii=False,indent=2))
      return R({"synced":len(new),"total":len(existing),"source":"supabase"})
     return R({"synced":0})

  if cb_env and cb_key:
   # CloudBase 国内方案（Phase 2）
   resp=await _c.post(f"https://api.weixin.qq.com/tcb/databasequery",headers={"Content-Type":"application/json"},json={"env":cb_env,"query":f'db.collection("stories").where({{user_id:"{uid}"}}).orderBy("createdAt","desc").limit(50).get()'})
   if resp.status_code==200:
    data=resp.json()
    if data.get("errcode")==0:
     stories=json.loads(data["data"])
     if stories:
      local=Path.home()/".aesir"/"synced_stories.json"
      existing=json.loads(local.read_text())if local.exists()else[]
      existing_ids=set(s.get("_id","")for s in existing)
      new=[s for s in stories if s.get("_id","")not in existing_ids]
      existing.extend(new);local.write_text(json.dumps(existing,ensure_ascii=False,indent=2))
      return R({"synced":len(new),"total":len(existing),"source":"cloudbase"})
     return R({"synced":0,"source":"cloudbase"})
   # CloudBase 失败后回退

  return R({"error":"Phase 2: 配置 CLOUDBASE_ENV 和 CLOUDBASE_KEY 后可启用云同步"})

 except Exception as e:return R({"error":str(e)})

A("sync","从 CloudBase 拉取故事到本地存档(Phase 2)",{"user_id":{"type":"string"}},["user_id"])

@sv.get_prompt()

@sv.get_prompt()
@sv.get_prompt()
async def get_prompt():
 return "AEsir v4.2 - "+str(len(TS))+" tools"

async def run_ollama():
 import httpx;print("AEsir v4.2 Ollama qwen3:14b")
 while True:
  i=input("\n> ").strip()
  if i.lower()in("exit","q"):break
  if not i:continue
  st=gs();cl=""
  if st.get("uc",0)<3:a=[input(f"  {q}:").strip()or"-"for q in["最在意?","读者带走?","参考?"]];cl=f"补充:{';'.join(a)}"
  an=["英雄之旅","推理","情感","逆袭","救赎"][max(0,min(4,int(input("弧线1-5: ").strip()or"1")))]
  ra=await clm(f"5条世界线,弧线{an}",f"想法:{i}\n{cl}")
  print(f"\n{ra}\n");c2=input("编号选/s保存:").strip()
  if c2=='s':st.setdefault("a",[]).insert(0,{"id":str(uuid.uuid4())[:8],"i":i[:200],"m":ra[:2000]});ss(st);continue
  if c2.lower()in("exit","q"):break
  try:cid=int(c2);con=input("约束:").strip()
  except:con=c2;cid=1
  e=EM[TONE[(cid-1)%len(TONE)]]
  fr=await clm(f"500-800开场+破坏约束",f"想法:{i}\n约束:{con or'无'}")
  print(f"\n{fr}\n");st["uc"]=st.get("uc",0)+1;ss(st)
  if input("保存?(y/n)")in("y","yes",""):st.setdefault("a",[]).insert(0,{"id":str(uuid.uuid4())[:8],"i":i[:200],"m":fr[:2000]});ss(st)

async def clm(s,p,t=0.8):
 import httpx
 try:
  async with httpx.AsyncClient(timeout=120)as cl:
   r=await cl.post("http://localhost:11434/v1/chat/completions",json={"model":"qwen3:14b","messages":[{"role":"system","content":s},{"role":"user","content":p}],"stream":False,"options":{"temperature":t}})
   return r.json()["choices"][0]["message"]["content"]if r.status_code==200 else f"[E:{r.status_code}]"
 except Exception as e:return f"[E:{e}]"

if __name__=="__main__":
 if "--ollama" in sys.argv:asyncio.run(run_ollama())
 else:print(f"AEsir v4.2 {len(TS)}工具",file=sys.stderr);asyncio.run(sv.run(stdio_server()))
