---
name: knowledge-distiller
description: 将原始知识源（文档、FAQ、SOP、转录稿、聊天记录、问答、视频、网页链接、图片/扫描件，含竖版页面与竖排古籍）蒸馏为结构化的、可直接发布的 WorkBuddy 技能定义。当用户想把任何领域知识变成可复用技能时使用，例如"把这份资料蒸馏成 skill"、"根据这份文档/视频/网页生成技能"、"把我的知识库做成技能"、"帮我把 SOP 变成智能体技能"、"把这份竖排古籍/竖版文档做成技能"。
agent_created: true
slug: knowledge-distiller
displayName: 知识蒸馏工厂（开源版）
version: 3.6.1
summary: 把任意领域知识源（文档/FAQ/SOP/转录/视频/网页/图片/竖排古籍/知识库）蒸馏为可复用、可进化的 WorkBuddy 技能；子技能自带进化底座，工厂可自检升级。
license: MIT
---

# 知识蒸馏工厂（Knowledge Distiller）

## 概述
把零散、冗长的知识压缩成结构化、可复用的技能定义。它像一个"技能工厂"：给定一份知识源，产出一份完整、可发布的 SKILL.md（含名称、描述、系统提示、步骤与 few-shot 示例）。蒸馏是压缩与概括，不是逐字抄写。

## 何时使用
- 用户提供文档、FAQ、SOP、转录稿或问答，并要"做成技能"、"蒸馏成技能"、"生成技能"、"做成智能体技能"。
- 用户提供视频（本地文件或链接）、网页链接，想从音视频/网页内容中沉淀知识。
- 用户有值得沉淀为可复用工作流的领域专长。
- 用户想从知识库批量生产技能。
- 用户希望技能具备自动升级能力（随资料完善而进化）。
- 用户想**升级一个已存在的子 skill**（追加资料 / 用户纠错 / 知识库更新 / 时效到期），而非从零蒸馏——走「再进化模式」（见下）。

## 核心原则
蒸馏而非转录。去除冗余、消解冲突、提炼少数可泛化的核心原则、捕获边界 case，并始终保留示例。只输出技能定义本身——不要寒暄或废话。

## 工作流程

### 第 1 步 — 接收与解析
识别知识类型（FAQ / SOP / 叙述 / 结构化数据 / **视频** / **网址**）、目标范围，以及"禁止清单"（技能绝不能做什么）。判断输入是**单源**还是**多源/知识库**：
- 单源：直接进入第 2 步。
- 多源/知识库：先按下方"多源与知识库模式"做摄入与对齐，再继续。
- **视频输入**（本地文件 / 链接）：按「媒体摄入协议」（见 references/distillation-method.md 第 17 节）做多模态提取——①音频轨 ASR 转录（词级时间戳）；②视频轨**场景切分**抽关键帧（画面变化才抽，不做均匀抽帧）；③字幕轨（如有）校正 ASR；④画面 OCR 提取 PPT/白板/代码内文字（**竖版/竖排文字**自动检测并按列重组，见下方「图片与竖排输入」）；⑤元数据（标题/简介/时长/作者）。最后**时间轴对齐成图文块**——每块 = 一段转录文字 + 该时段关键帧 + 帧内 OCR，图文互证。关键帧做**三级去重**：pHash 视觉相似 + 直方图差异 + OCR 文本差异（画面相同但字幕/文字变了 → 判新帧）。可选增强：关键帧画面语义描述（多模态模型一句话概括画面）、说话人分离（访谈/播客按人归组）、自动章节分段（长视频先切章再蒸馏）——细节见第 17 节。
- **网址输入**：正文提取（readability 去广告/导航）、保留表格/列表/代码块/图片 alt、抓取元数据（URL/标题/作者/**发布时间**——发布时间喂给 freshness 桶）。**渠道失败按四级分类处理**——A 类短暂网络/限流（重试 ≤3 次 + 备用通道 yt-dlp/curl/wayback）；B 类反爬/登录/签名（不重试，走用户导出/授权）；**C 类沙箱通道序列化故障（工厂无能力修，提示用户重启会话，别空转）**；D 类 JS-only/captcha（走用户导出/授权）。**批量前先做一次轻量通道探测**，命中 C 类故障立刻停手不要逐 URL 重试。细节见 references/distillation-method.md §17.1。
  - **公众号文章专门处置（`mp.weixin.qq.com`，B 类子型）**：JS 加密（`__mp_anti_*`）+ Referer 校验 + 第三方 IP 限流 + 部分文章关注后全文隐藏叠加——通道 100% 健康也几乎拿不到正文。**工厂层不能自动修**，请按 §17.1.1 三路径自助导出后喂回：①浏览器登录 `mp.weixin.qq.com` 后 F12 Network 抓 `profile_ext`/`getmsg` 请求 response JSON（粘进对话，走 `local_clip`）；②微信客户端分享到印象笔记或微信收藏后导出为 Markdown；③选中全文复制粘贴。如反复"通道全挂"则是 C 类叠加，与公众号本身无关。
  - **网址内嵌视频探测**：访问网址后先探测页面内是否含视频——①URL 直接指向视频文件（.mp4/.webm/.m3u8 等）→ 直接解析；②页面含 `<video>` 标签 / `og:video` 元数据 → 提取视频源地址；③视频平台分享页（B站/抖音/YouTube 等）→ 解析平台链接。探测到视频即下载后走上方「视频输入」的五轨提取流程（ASR/关键帧/OCR/字幕/元数据 → 图文块），与正文提取合并为同一来源的多通道输入。平台视频需登录/反爬无法直接抓取时，提示用户下载后本地导入。
  - **多视频形态展开**：一个链接可能是合集/播放列表/博主主页，或一次给多个链接——先判定形态（单视频 S1 / 多视频页 S2 / 合集 S3 / 主页 S4 / 多链接 S5）再展开为视频清单（预扫不下载、按视频 id 去重）；清单超阈值（默认 >20 条）时与用户确认裁剪范围（全部 / 最近 N 条 / 时间段 / 指定合集 / 关键词过滤），合并后逐条摄入（细节见第 17 节「媒体来源展开」）。
- **多次收集**：同一来源（视频/网址/文档）再次摄入时**版本化存储**（记录 `collected_at` 时间戳），做文本 diff 只处理变化部分，走「跨次合并四步」增量更新——不重跑全量。
- **图片 / 扫描件 / 竖版页面**（截图 / 竖版 PDF / 古籍 / 竖版海报 / 长图）：OCR 提取文字后统一做**阅读顺序整理**——横版按"y 分行、行内 x 排序"，**竖排文字**（从上到下、列从右到左）用 `scripts/ocr_layout.py` 按列重组（窄块检测 → x 中心聚类成列 → 列内 y 排序 → 默认右起 rtl；OCR 单字识别差时先把图旋转 90° 再 OCR，坐标反变换后仍走重组；超长截图先切分再逐块 OCR）。竖排来源在 `source_media.note` 标 `vertical_text`；原文语义依赖版式顺序（如对联、古籍页码）时保留原始排版标注供人工核对。
若来源含糊或太单薄无法泛化，只问一个聚焦的澄清问题，然后继续。

#### 体量 / 动态性评估（决定路由方式）
在第 1 步末尾，对来源做一次「体量 × 动态性」评估，据此选择两种封装路由之一：
- **路由 A — 全量嵌入（Stable, Compact）**：来源体量小（单篇/单册、可总结进 ≤2 页提示）、且长期稳定不变 → 按第 2–6 步，把知识压缩进 SKILL.md。
- **路由 B — 骨架 + 检索路由（RAG）**：来源过大（多册书、海量文档、整库）或频繁变动（每周/每月更新）→ **不把知识正文塞进 SKILL.md**，而是产出：
  1. 一个**骨架技能**：只含稳定不变的部分——能力定位、判断流程、输出模板、调用约定；
  2. 一条**检索路由**：写明「凡涉及来源细节/事实，先去 `<知识库名/id>` 检索再作答」，并把知识库名/id 记入 references/；
  3. 一份**索引约定**：告诉调用方如何检索（关键词、检索范围、是否需授权）。
评估维度：①体量（条数/页数/字数是否超出单次提示舒适区）；②动态性（是否常变、是否已有在线知识库可检索）。两者任一命中即选路由 B。
注意：路由 B 的核心是「骨架稳定、细节外挂」，避免 SKILL.md 膨胀与知识过期——但这要求来源可被检索（本地导出索引，或已连接在线知识库）。若来源既大又不可检索，先提示用户导出/连接检索后端，再走路由 B。

### 第 2 步 — 抽取（标准表示 · v3.1）
一律抽取为统一的固定 JSON Schema（见下方「标准抽取 Schema」），**不要**用自由表格或散落要点——统一结构便于后续度量覆盖率、排序人工审阅与跨源对齐。

**横向五层**之外，本步引入**纵向「道法术器」层级树（dftq）**与**结构／导图／流通**三类新桶，构成完整抽取矩阵：
- 道法术器是**层级嵌套树**（非并列四列）：很多条「道」→ 每条道下很多「法」→ 每条法下很多「术」→ 每条术下很多「器」→ 每个器下很多「细节」。共 5 层：`dao`(道·原理宗旨价值观本质规律底线) / `fa`(法·方法论框架规则决策) / `shu`(术·具体步骤技巧话术窍门) / `qi`(器·工具系统模板术语指标) / `detail`(细节·参数·字段·边界·模板内容) / `cross`(跨层关系·流程衔接)。
- 层级归属落在独立 `dftq` 桶（见下方 Schema）：每个节点带 `id / parent_id / dim / title / summary / detail / confidence / source_ref`，`parent_id` 指向上一层节点，从而表达「道⊃法⊃术⊃器⊃细节」的归属链。每条横向抽取项可附 `dftq_ref` 挂接到对应树节点。
- 每条抽取项带 `path`（章节锚点，如 `/第三章/3.2节/定价规则`），把细化知识锚定到原文位置；第 5 步 gold 验证可精确溯源，覆盖率也能按章节统计。
- 每项仍附 `confidence`（high/medium/low）与 `source_ref`（多源必填），贯穿压缩、审阅、验证与冲突裁决全程。

核心逻辑仍是「抽取=全量中间表示，压缩=选择性落地」：Schema 抽得细而全，作为第 3 步覆盖率度量的基线；最终技能多数内容会被压成散文，但度量基线不能丢。

```json
{
  "entities":   [{"term":"","definition":"","aliases":[],"category":"","related":[],"dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"high|medium|low","source_ref":""}],
  "relations":  [{"from":"","rel_type":"cause_effect|if_then|before_after|beats|exception_of|conflicts_with|refines|part_of|other","rel":"","to":"","dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"","source_ref":""}],
  "rules":      [{"id":"r1","statement":"","applies_when":"","severity":"must|should|may","exceptions":"","dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"","source_ref":""}],
  "decisions":  [{"condition":"","action":"","priority":"","fallback":"","dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"","source_ref":""}],
  "metrics":    [{"name":"","value":"","unit":"","comparator":">=|<=|=|in","applies_to":"","dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"","source_ref":""}],
  "qa":         [{"question":"","answer":"","dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"","source_ref":""}],
  "examples":   [{"type":"good|bad|neutral","scenario":"","input":"","expected_output":"","dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"","source_ref":""}],
  "steps":      [{"order":1,"name":"","input":"","output":"","tool":"","dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"","source_ref":""}],
  "persona":    {"tone":"","voice":"","do_not":[""],"values":[""],"dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"","source_ref":""},
  "edge_cases": [{"case":"","handling":"","dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"","source_ref":""}],
  "ambiguity":  [{"issue":"","resolution":"pending|assumed|needs_human","note":"","dim":"dao|fa|shu|qi|detail|cross","path":""}],
  "structure":  [{"level":1,"title":"","parent":"","aliases":[],"dim":"dao|fa|shu|qi|detail|cross","path":"","source_ref":""}],
  "dftq":       [
    {"id":"d1","dim":"dao","title":"客户第一","summary":"一切以客户利益为先","detail":"","parent_id":null,"confidence":"high","source_ref":"ch2"},
    {"id":"f1","dim":"fa","title":"首次响应时效","summary":"所有咨询须限时响应","detail":"","parent_id":"d1","confidence":"high","source_ref":"ch3"},
    {"id":"s1","dim":"shu","title":"镜像措辞开场","summary":"用用户原话回应对方情绪","detail":"","parent_id":"f1","confidence":"medium","source_ref":"sop-7"},
    {"id":"q1","dim":"qi","title":"CRM 话术库","summary":"调用标准话术模板","detail":"","parent_id":"s1","confidence":"high","source_ref":"tool-doc"},
    {"id":"x1","dim":"detail","title":"话术模板字段","summary":"","detail":"称呼/痛点/替代方案/收口四字段","parent_id":"q1","confidence":"high","source_ref":"tpl-1"}
  ],
  "flows":      {"forward":[{"from_dim":"dao","to_dim":"fa","trigger":"","note":""}],"reverse":[{"from_dim":"detail","to_dim":"qi","trigger":"","note":""}]},
  "logic":      [{"id":"l1","type":"chain|branch|sequence|tradeoff","trigger":"","premise":"","steps":[""],"condition":"","branches":[{"if":"","then":""}],"conclusion":"","fallback":"","priority":1,"dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"high|medium|low","source_ref":""}],
  "mindmap":    [{"node":"","parent":"","children":[],"dim":"dao|fa|shu|qi|detail|cross","source_ref":""}],
  "domain_ext": [{"ext_type":"compliance|error_code|api_param|symptom_cause|other","name":"","value":"","applies_when":"","constraint":"","dftq_ref":"","dim":"dao|fa|shu|qi|detail|cross","path":"","confidence":"high|medium|low","source_ref":""}],
  "triggers":   [{"id":"t1","intent":"","patterns":[""],"negative":[""],"route_to":"","priority":1,"dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"high|medium|low","source_ref":""}],
  "conditions": [{"id":"c1","type":"pre|post|env","statement":"","applies_to":"","dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"high|medium|low","source_ref":""}],
  "state_machine": [{"state":"","event":"","action":"","next_state":"","guard":"","dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"high|medium|low","source_ref":""}],
  "acceptance": [{"id":"a1","target":"","assert":"","pass_condition":"","trap_case":"","gold_ref":"","dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"high|medium|low","source_ref":""}],
  "io_contract": [{"id":"io1","target":"","type":"input|output|failure","name":"","schema":"","required":[""],"default":"","example":"","dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"high|medium|low","source_ref":""}],
  "decision_tree": [{"id":"dt1","node":"","parent":"","condition":"","action":"","fallback":"","depth":1,"dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"high|medium|low","source_ref":""}],
  "diagnosis": [{"id":"dg1","symptom":"","causes":[{"cause":"","weight":"high|medium|low","verify":"","exclude_order":1}],"danger_signals":[""],"dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"high|medium|low","source_ref":""}],
  "freshness": [{"id":"fr1","target":"","checked_at":"","valid_until":"","update_freq":"","superseded_by":"","reason":"","dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"high|medium|low","source_ref":""}],
  "deps": [{"id":"dp1","from":"","to":"","type":"prereq|depends_on|conflicts_with|supersedes","note":"","dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"high|medium|low","source_ref":""}],
  "permissions": [{"id":"p1","scope":"","who":"","auth":"","data_class":"public|internal|confidential|pii","guardrail":"","dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"high|medium|low","source_ref":""}]
}
```
- **① 事实与术语层**：`entities` 术语定义 + 同义词(aliases) + 分类(category) + 关联实体(related)；`relations` 实体间关系（支撑 RAG 检索召回与知识图谱）。
- **② 规则与决策层**：`rules` 硬性约束 + 严重度(severity: must/should/may) + 例外(exceptions)；`decisions` 条件→动作 + 优先级(priority) + 兜底(fallback)；`metrics` 量化阈值（值/单位/比较符），最易翻车，单独桶便于断言校验。
- **③ 内容素材层**：`qa` 问答对（检索语料 / few-shot 素材）；`examples` 来源自带范例(good/bad/neutral) → 直接转 few-shot；`steps` 流程步骤 + 输入(input)/输出(output)/工具(tool)。
- **④ 风格与边界层**：`persona` 语气/发声/禁止清单(do_not)/价值观 → 系统提示与风格段；`edge_cases` 特殊 case 与其处理（与 ambiguity 的"未知"明确区分）。
- **⑤ 待定/盲区层**：`ambiguity` 真正未知 / 冲突未解 → pending / assumed / needs_human。
- **⑥ 结构／导图／流通层（新增）**：
  - `structure` 抽**目录 → 章节 → 重点小标题**的层级树（`level/title/parent/aliases`），`aliases` 即「现代名称/别称」；每条带 `dim` 与 `path`，把细化的知识锚在原文结构里。注意 `structure` 是**原文物理结构**，与下方 `dftq` 的**逻辑层级（道法术器）**是两个维度，可并存。
  - `dftq`：**道法术器层级树**主轴——节点 `{id, parent_id, dim, title, summary, detail, confidence, source_ref}`。`parent_id` 指向上一层，形成「道⊃法⊃术⊃器⊃细节」归属链；一条道下挂多条法、一条法下挂多条术、一条术下挂多条器、一条器下挂多条细节，**每层子项数不设硬上限**。横向桶（rules/steps/…）可附 `dftq_ref` 指向树节点，建立「内容 → 层级」关联。
  - `flows` 记录来源里知识的**流通方式**——正向推导链（道→法→术→器→细节：为什么→用什么方法→什么技法→什么工具→什么参数）与运行时逆向链（细节→器→术→法→道：什么参数→什么工具→什么技法→合于什么方法→合于什么原则）；每条含触发条件 `trigger` 与衔接说明 `note`。
  - `logic`（v3.6 新增）记录知识**内在逻辑如何运转**——把推理/决策/编排的运转机制蒸馏成可执行链：`chain` 因果/推导链（`premise` 前提 → `steps` 推理步骤 → `conclusion` 结论，回答"为什么/怎么推出来的"）；`branch` 条件分支（`condition` 判定 + `branches` if-then 列表 + `fallback` 兜底，回答"什么条件下走哪条路"）；`sequence` 步骤时序（`steps` 有序编排，含先后/并行/回退语义，回答"先做什么后做什么"）；`tradeoff` 权衡取舍（`premise` 权衡点 + `steps` 对比 + `conclusion` 取舍结论，回答"为什么选它不选它"）。每条带 `trigger` 触发条件与 `priority` 优先级。**凡资料含可复用的推理/判断/编排逻辑，都必须抽 `logic`，而不是只抽孤立要点**——这是"把知识蒸馏出逻辑运转"的主载体。
  - `mindmap` 由 `structure`（骨架）+ `dftq`（层级）+ `relations/entities`（关联）**派生**的导图节点（`node/parent/children/dim`）；标注"派生"而非重复抽取，**仅长文/多章资料生成**——短文（单篇、无章节结构）跳过，只给每条打 `path`。
- `source_ref` 源自哪个段落/文档/来源（多源时必填，便于溯源与第 5 步核查）。
- 下游映射：`persona→系统提示`、`metrics→规则硬数字断言`、`examples→few-shot`、`relations→路由B检索`、`edge_cases→边界段`、`ambiguity→残留盲区`、`structure→章节目录`、`dftq→道法术器层级（子技能主结构）`、`mindmap→导图`、`flows→子技能逆向工作流`、`logic→子技能「逻辑运转段」（推理/决策/执行编排）`、`triggers→子技能「何时使用」与路由判断`、`conditions/state_machine→子技能前置检查与状态分支`、`acceptance→第5步 gold 集与反例素材`、`io_contract→输入输出格式与失败处理`、`decision_tree→多分支流程`、`diagnosis→排障顺序与危险预警`、`freshness/deps→路由B决策与依赖/过时提示`、`permissions→权限校验与 do_not 清单`、`domain_ext→领域规则/参数表/条款清单`、`source_media→媒体溯源与增量更新锚点（图文块/章节/帧定位）`、`dim→各层级落点`。

#### 领域扩展桶（domain_ext）
通用 Schema 之上，`domain_ext` 承载**领域特有字段**——通用五层桶装不下、但对特定领域至关重要的一类知识。每条记录 `{ext_type, name, value, applies_when, constraint, dftq_ref, dim, path, confidence, source_ref}`：
- `ext_type` 预定义四类，可扩展 `other`：
  - `compliance` **合规条款**——须/禁/罚则/豁免（如数据保留期、准入资格、红线行为）；
  - `error_code` **错误码**——码/含义/触发条件/处理动作（如 `E1001: 额度不足，提示充值`）；
  - `api_param` **接口参数**——参数名/类型/必填/约束/默认值；
  - `symptom_cause` **症状→病因**——现象/原因/排除法/危险信号（排障、医疗、诊断类）。
- `dftq_ref` 指向对应层级树节点（如 `api_param` 挂 `qi` 接口文档、`symptom_cause` 挂 `shu` 排障步骤），`dim` 标纵向落点，`constraint` 记校验规则（正则/枚举/范围）。
- 是否启用、启用哪些 `ext_type`：第 1 步识别领域后决定；**不用领域字段的资料不填此桶**。四类预设有对应领域适配说明，见 references/distillation-method.md 第 12 节。

#### 可选扩展桶（触达 · 契约 · 条件 · 推理 · 生命周期 · 治理 · 验收）
领域桶之外，还有七组**按资料类型启用**的可选桶（与 domain_ext 一样「不用不填」）：
- **`triggers`（触达 · 触发与意图）**——让技能知道"什么时候该出手、什么时候绝不该出手"：`intent` 意图名 + `patterns` 触发说法/关键词（用户怎么说该用）+ `negative` 否定触发（怎么说绝不用）+ `route_to` 路由目标（多技能竞争时指向谁）+ `priority` 优先级。下游 → 子技能「何时使用」段与路由判断。**几乎所有技能都建议抽**。
- **`conditions` + `state_machine`（适用条件 · 前置/后置/环境/状态机）**——`conditions.type` 三态：`pre` 前置条件（执行前必须满足）/ `post` 后置条件（执行后保证）/ `env` 环境适用（平台/版本/区域/受众矩阵），`applies_to` 指向步骤 order 或规则 id；`state_machine` 抽状态迁移表：`state` 当前态 / `event` 事件 / `action` 动作 / `next_state` 下一态 / `guard` 守卫条件。下游 → 子技能步骤的前置检查与状态分支逻辑。**流程/工单/审批/审核类资料建议抽**。
- **`acceptance`（验收 · 断言与反例）**——`target` 验收对象（规则 id / 步骤 order / dftq 节点）+ `assert` 验收断言（怎么算答对）+ `pass_condition` 通过条件 + `trap_case` 陷阱题/反例 + `gold_ref` 关联 gold 条目。下游 → **第 5 步 gold 集直接由 `assert` 生成**（抽取阶段就把验收标准定了，验证阶段复用，形成闭环）。**输出质量需要可验证的资料建议抽**。
- **`io_contract`（契约 · 输入输出）**——`target` 契约对象（步骤/技能/dftq 节点）+ `type`（`input` 入参 / `output` 出参 / `failure` 失败模式）+ `name` 参数名 + `schema` 类型结构 + `required` 必填列表 + `default` 默认值 + `example` 示例值。下游 → 子技能输入输出格式约定、`scripts/` 校验规则、失败处理分支。**API/接口文档、表单/脚本类资料建议抽**。
- **`decision_tree`（推理 · 决策树）**——把扁平 `decisions` 树化：`node` 节点名 + `parent` 父节点 + `condition` 分支条件 + `action` 动作 + `fallback` 兜底 + `depth` 层级。下游 → 子技能的多分支流程（嵌套判断而非平铺 if-else）。**审核/风控/审批类多层判断资料建议抽**。
- **`diagnosis`（推理 · 诊断树）**——`symptom` 现象 + `causes[]` 候选原因数组（`cause`/`weight` 权重/`verify` 验证手段/`exclude_order` 排除顺序）+ `danger_signals` 危险信号（**先查危险，再查常见**）。下游 → 子技能排障步骤的排除顺序与红线预警。**排障/医疗/维修/诊断类资料建议抽**。
- **`freshness`（生命周期 · 时效）**——`target` 知识对象 + `checked_at` 上次核验 + `valid_until` 有效期 + `update_freq` 更新频率 + `superseded_by` 被谁替代 + `reason` 变更原因。下游 → 路由B决策（高频变→外挂）、known-gaps、过时提示。**政策/价格/版本类常变资料建议抽**。
- **`deps`（生命周期 · 依赖）**——`from`→`to` + `type`（`prereq` 前置依赖 / `depends_on` 依赖 / `conflicts_with` 冲突 / `supersedes` 替代）+ `note`。下游 → 子技能的学习路径/调用顺序/冲突提示。**培训课程、方法论类（先学 A 再 B）资料建议抽**。
- **`permissions`（治理 · 权限边界）**——`scope` 适用范围（操作/数据/功能）+ `who` 谁能用 + `auth` 所需授权 + `data_class` 数据分级（public/internal/confidential/pii）+ `guardrail` 红线行为（绝对禁止）。与 `domain_ext.compliance` 互补：compliance 记**外部合规条款**，permissions 记**内部使用边界**。下游 → 子技能权限校验段 + do_not 清单。**合规/金融/医疗/企业内部技能建议抽**。
- 启用建议与各桶字段细节见 references/distillation-method.md 第 15–16 节。

#### 五层覆盖度诊断（道法术器 · 含细节）
第 2 步末尾，对 `dftq` 层级树做一次**五层诊断**：
- 逐层统计：道层有多少条道、每条道下平均多少法、每条法下平均多少术、每条术下平均多少器、每条器下平均多少细节；以及各层平均置信，形成道·法·术·器·细节 五张「有／缺／薄／断」图。
- **断链识别**：某条道下完全没有法、某条法下完全没有术、某条术下完全没有器、某条器下完全没有细节——属「断链」，记入残留盲区并提示该链不完整。
- **缺层不补造**：整层为零（如纯操作手册只有"术+器+细节"），属诊断结论而非失败——在输出报告标「本资料缺道层/缺法层」并记入残留盲区；**绝不凭空编造一个道/法**。仅当用户明确要求"补齐某层"时，才标 `needs_human` 请人工补，不自行生成。
- **薄层/薄链**：某层条数极少或平均置信低，标"薄"并在报告提示该层/链可能不足以支撑技能，建议补充来源或降权使用。
- 诊断结果回灌第 3 步：压缩时按层级均衡取舍，避免技能只堆积某一层（如全是"术"而无"道"锚定原则），也要避免「有道无术」「有术无器」的空链。

#### 逻辑自检（六维诊断 · 逻辑自洽维 · v3.6 新增）
在五层诊断（层级覆盖）之后、补料决策点之前，对抽取结果做一次**逻辑自洽检查**——层级完整 ≠ 逻辑自洽，检查知识"内在逻辑能否运转"：
- **矛盾检测**：扫描 `rules`/`decisions` 的 statement/condition 两两互斥（如 r1 must X 与 r2 must 非 X）；`relations` 中 `conflicts_with` 未裁决的对；`deps` 中 `conflicts_with` 类型——命中即记「矛盾对」，未裁决的入残留盲区并标 `needs_human`（走冲突裁决）。
- **循环依赖检测**：以 `deps`（prereq/depends_on）与 `steps`（order/input→output）、`logic.sequence` 构建引用图，检出环（A 依赖 B 且 B 依赖 A）→ 记「循环依赖」，回第 2 步重抽或标 `needs_human`。
- **前提缺失检测**：`rules.applies_when` / `decisions.condition` / `conditions` / `logic.trigger` 引用的概念，在 `entities`/`dftq` 中未定义 → 记「前提缺失」进 known-gaps（含"被引用但未定义"清单）。
- **分支不全检测**：`decision_tree` / `state_machine` / `logic.branch` 缺 `fallback` 或缺明显分支（有"是"无"否"）→ 记「分支不全」，补 fallback 或标 `needs_human`。
- **层间内容跳跃**：`logic` 链的 `conclusion` 与 `premise` 之间缺推理步骤、`dftq` 父子节点内容语义断层（父谈 A 子谈 B）→ 记「层间跳跃」，薄链提示。
- 自检输出「**逻辑诊断清单**」（矛盾对 / 循环依赖 / 前提缺失 / 分支不全 / 层间跳跃 五类 + 数量 + 涉及节点），并入残留盲区/known-gaps；结果随「补料/继续决策点」一起呈现给用户（可并入该决策的提示模板，作为第六维诊断结果）。

#### 补料 / 继续决策点（五层诊断后）
诊断结束、压缩之前，蒸馏器**主动向用户呈现三选一决策**，让用户决定「五层缺/薄/断链」如何处理。**绝不替用户默选**——每条路径的影响范围不同，需用户确认后进入下一步。决策提示模板（在对话里直接呈现，措辞可灵活但要点齐）：

> 「本次抽取诊断发现：道层 X 条（薄）、法层 X 条（断链：d1 下无 fa）、术层 X 条（断链：f2 下无 shu）、器层 X 条、细节层 X 条。请选择下一步处理方式：
> ① 暂不补充 → 把当前 `dftq` 层级树与「缺/薄/断链清单」**固化为记忆档案**暂存于 `references/raw-extract-<source>.json`，标记 `status: staged`，待后续资料到位后再续抽与合并；
> ② AI 补充 → 启用 AI 自动填补路径（A1 由 AI 在已抽内容上做合理外推并标 `assumed`，需用户校验；A2 AI 仅补骨架与占位，由用户自行填入具体细节；A3 仅补最薄/最断链层，全部标 `assumed` 并强制进入人工审阅）；
> ③ 不补充 → 跳过补料，直接进入第 3 步压缩与第 4 步封装——按当前 `dftq` 实际结构出技能，缺失层按「五层诊断」标记，不强凑闭环。」

**三种路径的具体逻辑：**

**路径 ① — 暂不补充 / 形成记忆保留**
- 把第 2 步抽取的全部原始中间表示（含 `dftq` 完整层级树、五层诊断结果、缺/薄/断链清单）保存为 `references/raw-extract-<source>.json`，并写入 `references/extract-log.md` 一行索引：`source / timestamp / status: staged / 缺口清单`。
- 工作流停在诊断后、第 3 步压缩前，**不向下推进**，等待用户后续追加资料。
- 用户追加新资料时，走「续抽与合并」路径：①重新跑第 1–2 步（仅对新源），得到新 `dftq`；②按下方「跨次合并四步」做**跨次合并**；③重新跑五层诊断——补足则可继续走 ②/③ 或继续 ①。
- **跨次合并四步**（详细规则与判定阈值见 references/distillation-method.md 第 13 节）：
  1. **归一化**：新老节点 `title` 去空白/标点/繁简归一化，便于精确比对；
  2. **精确合并**：`title` 归一后相同 → 合并为一个节点，`summary`/`detail` 取更详尽者，`confidence` 取高者，`source_ref` 追加新来源；
  3. **同义合并**：title 不同但 `summary` 语义等价（相似度 ≥0.6）→ 自动合并，保留规范名，旧名记入 `aliases`；0.6–0.85 中置信项也合并（宽松策略），低置信点记入「待验证清单」由第 5 步验证兜底——合并错了事后拆分降级，不阻塞流程（见 verify-protocol §4 与 distillation-method §13.1 合并降级）；
  4. **补挂与裁决**：新节点按 `parent_id`+`dim` 补挂到已存树（作为新子项）；同层同名内容冲突时走「权威等级 × 置信加权」裁决并记四元组，**裁决结果须人工确认**（见多源冲突裁决）。
  - 合并结果必须输出一份「合并清单」（合并了谁/新增了谁/挂到了哪/待验证项），低置信合并点进「待验证清单」（非人工阻塞），冲突裁决项才进人工审阅优先级。
- 适用：用户手头资料不齐、想先沉淀手头内容、未来再补；或希望把多次抽取累积成一份更完整的技能。

**路径 ② — AI 补充**
- 仅在用户明确选择此路径时启动；**默认拒绝凭空补造**（与「缺层不补造」原则一致，此路径是用户显式授权的例外）。
- 三个子选项对应不同 AI 介入深度：
  - **A1 AI 合理外推 + 用户校验**：AI 在已有抽取项基础上做最小外推（如根据相邻法推一条同类法、根据已知的术推一条配对的术），全部标 `assumed` 并附 `basis: "外推自 <邻近抽取项 id>"`；产物进入第 5 步 gold 验证与人工审阅优先级第一序列。
  - **A2 AI 仅补骨架 + 用户填细节**：AI 把缺的层/链搭出空骨架（节点 + `title` + `summary: "<待用户填写>"` + `detail: "<待用户填写>"`），用户/调用方在后续使用中**自行完善**——技能发布时这些字段直接作为「可填位」开放。
  - **A3 仅补最缺/最断链**：AI 只对诊断中标 `断链` 与 `薄` 的节点做最小补足（如只补 `d1` 下空的法骨架），仍全部标 `assumed` 并强制进入人工审阅。
- 补充结果**必须重新走一遍五层诊断**：若仍断链，回到决策点再选；直到用户继续推进。
- **用户校验流程**（A1/A2/A3 的补足项在进压缩前都须过这一关）：
  1. 以清单形式呈现所有补足项（节点 id / title / 标 `assumed` 的 summary·detail / basis 依据）；
  2. 用户对每项三选一：**确认**（保留，`confidence` 升为 medium 并去 `assumed` 标记）/ **修改**（按用户修正内容覆盖）/ **删除**（该项剔除）；
  3. 校验完成后更新 `version-state.json` 与 `known-gaps.md`，再进入压缩；未校验的 `assumed` 项不得出现在最终 SKILL.md 正文（可保留在 references/ 待后续校验）。

**路径 ③ — 不补充 / 继续完善技能**
- 直接以当前 `dftq` 实际结构进入第 3 步压缩与第 4 步封装。**不补造、不强凑闭环**——缺层/断链/薄链按原样写入技能元数据或 `references/known-gaps.md`，并在第 6 步输出报告的「残留盲区」显式列出。
- 适用于：用户接受当前覆盖度、想先发版验证价值、后续迭代时再补；或该层确实不适用本资料（如纯工具手册本来就不需要"道"层）。
- 此路径下，第 5 步 gold 验证会针对「已知缺失」做容忍性评判（缺失的不计入失败），避免因覆盖不足导致验证不过。

**决策默认值**：用户 30 秒内未表态，**默认走路径 ①（暂不补充 / 形成记忆保留）**——这是最保守、最不损害「缺层不补造」原则的兜底。如需改变默认行为，用户可在对话里指明 `默认路径：②` 或 `默认路径：③`。

#### 记忆板块（第 2 步 ↔ 第 3 步之间 · v3.0 新增）
子 skill 自动进化的底座：把每次抽取的**知识颗粒**（标准中间表示）+ 使用期的**反馈信号**沉淀为记忆，后续资料到位时据此**增量升级**，而不是每次从零重建。
- **与决策点路径①的区别**：路径①是"当前资料不齐，用户选择暂存，等后续再续抽"——**被动等待**；记忆板块是**持续累积的进化底座**——第 2 步的抽取结果（无论是否走路径①）都落一份进记忆库，供未来任何时刻自动升级使用。
- **记忆库结构**（子 skill 出厂预装 `references/memory/`）：
  - `knowledge-grains/`：每次摄入的原始中间表示（`raw-extract-<source>-<timestamp>.json`），按来源+时间版本化存放；
  - `feedback/`：使用期反馈池——`corrections.md` 用户纠错、`failed-cases.md` gold 失败案例、`gap-notes.md` 使用中发现的缺口；
  - `version-state.json`：当前版本的 dftq 树快照、版本号、覆盖率/置信度基线；
  - `evolution-log.md`：进化日志——每次升级记录「触发信号 → 变更内容 → 验证结果 → 新版本号」。
- **四类进化触发器**：①新资料摄入（增量合并）；②用户反馈纠错；③gold 验证失败（使用期通过率下降）；④freshness 到期（时效类知识过期）。
- **升级环**：触发 → 沉淀记忆 → 增量 diff → 跨次合并 → 重诊断 → 重压缩 → **回归验证（旧 gold + 新 gold 都过）** → 版本++ → 可回滚。
- 完整协议见 references/evolution-protocol.md；第 1 步媒体摄入（视频/网址）的多次收集结果同样汇入知识颗粒库。

### 第 3 步 — 蒸馏与压缩
- 合并重复；消解矛盾并说明所作假设。
- **构建道法术器层级树**：以第 2 步 `dftq` 为主轴，把知识组织成「很多条道 → 每条道下很多法 → 每条法下很多术 → 每条术下很多器 → 每个器下很多细节」的 5 层嵌套树。**每层子项数不设硬上限**——一条道下可挂十几条法，一条法下可挂若干术，以此类推；规模由层级深度（固定 5 层：道/法/术/器/细节）而非条数上限控制。每条节点提炼到「能超越示例泛化」为止，再按权重（道 > 法 > 术 > 器 > 细节）收敛，确保五层均衡、不靠单一层撑满，也不留「有道无术」「有术无器」的空链。
- 识别边界/边缘 case 及其处理方式。
- 生成 2–4 个高质量 few-shot 示例，捕捉专家的"思考方式"而非仅最终答案。
- **覆盖率（Coverage）度量**：压缩后以第 2 步的标准表示为基线，估算「来源要点 → 技能」的覆盖比例。统计：①抽取项总数与已进入技能的比例；②`ambiguity` 中仍 `pending` 的数量；③`confidence=low` 项中有多少被保留、多少被降级为「需检索/需人工」。把估算写进输出报告（见第 6 步）。覆盖率低于阈值（默认 <70%）时，回流补抽取或升级为路由 B（RAG）。

### 第 4 步 — 封装为技能
按 references/skill-schema.md 的规范产出完整 SKILL.md：
- 前置信息：name（hyphen-case 小写，≤40 字符）、description（第三人称，写明何时用）、agent 生成时加 agent_created: true。
- 正文用祈使句：概述、何时使用、工作流步骤、few-shot 示例。
- **工作流默认按「逆向逻辑、正向运用」组织**：以第 2 步 `flows.reverse`（逆向运用链 细节→器→术→法→道）为骨架，子技能步骤按 **细节 → 定器 → 择术 → 循法 → 证道** 排序——先落到具体细节/参数（细节），再识别场景/输入/工具（器），再选技法（术），再套规则与流程（法），最后对原则与边界校验（道）。每一步**向上校验**：细节须落于器、用器必配术、术须合于法、法须合于道，确保执行从最细的"细节"出发，却始终朝"道"收敛。来源缺某层时，按「五层覆盖度诊断」标注缺失，不强凑闭环。
- **few-shot 与逆向工作流映射**：2–4 个示例**按逆向链组织**，与 `flows.reverse`（细节→器→术→法→道）一一对应——每个示例 = 输入（场景+细节）→ 推理过程（标注 `[器]` 选工具模板、`[术]` 用技法、`[法]` 套规则、`[道]` 守原则/边界校验）→ 输出（收敛于道）。这样示例既是 few-shot 又是逆向链的活演示：读者顺着示例就把工作流跑了一遍。
- **预装进化机制**：子技能发布时同步建立 `references/memory/` 记忆库（见上方「记忆板块」），出厂即带自动升级能力——以后资料完善、用户纠错、验证失败都会触发版本升级而非重做。
方法细节、六类蒸馏配方（问答/SOP/推理链/人设/few-shot/多源融合）、标准抽取 Schema、质量度量（覆盖率/置信度）与 RAG 路由分流见 references/distillation-method.md。

### 第 5 步 — 真验证与迭代闭环
不要只在脑中「跑」测试——把草稿技能当成真实技能来验证：
- 构造 gold 集：从来源自动抽取 3–5 个真实问答／场景作为金标准基准；若第 2 步抽了 `acceptance` 桶，gold 直接由 `acceptance.assert` 生成（断言即判定点，不必另造）；也可采用用户指定的测试集。
- 实跑验证：在子 Agent／沙箱中实际加载草稿 SKILL.md，逐条喂入 gold 查询，记录真实输出。
- 比对判定：逐条标注 答对／部分答对／答错／答非所问，并归类失败原因（缺规则、规则含糊、冲突未解、格式不符）。
- 回流修正：把失败 case 回传到第 3 步（压缩）重提炼规则；必要时回到第 2 步补抽取。
- 迭代达标：重复上述步骤，直到 gold 通过率达到门槛（默认 ≥80%）或触及迭代上限（默认 3 轮）。绝不默默猜测或编造来源不支持的知识。
- 末轮保留：覆盖率估算、残留盲区清单，以及按 `confidence` 降序排列的「待人工审阅优先级」——low / ambiguous 项排在前，便于人工把关最高风险内容。

### 第 6 步 — 输出
将最终 `SKILL.md`（已通过验证）置于单个代码块返回，并附一段验证报告，固定包含五项指标：
- **覆盖率（Coverage）**：来源要点进入技能的比例、`pending` ambiguity 数量；
- **置信度分布（Confidence）**：各抽取项 high/medium/low 计数，low 项列出并标注处理方式（保留/降级检索/需人工）；
- **gold 通过率**：实跑验证的通过比例；
- **残留盲区**：未覆盖/未解决项；
- **版本与进化状态**：当前版本号、出厂版本（v1.0.0）、是否已预装记忆库（`references/memory/`）、已登记待触发的进化信号。
**产物落盘决策**（压缩与封装时同步决定每部分进哪个目录，规则见 references/skill-schema.md）：
- `SKILL.md`：执行时**每步都要读**的内容——判断流程、核心规则、工作流步骤、few-shot；
- `references/`：**按需加载**的详细内容——术语表、参数表、模板正文、长规则集、领域明细、验证报告、合并记录、盲区清单、抽取档案、`memory/` 记忆库（进化底座）；
- `scripts/`：**确定性代码**——解析器、校验器、格式化脚本、gold 运行器；
- `assets/`：**非代码素材**——输出模板、样例文件、话术模板。
单条内容超过 2 屏、或只在特定分支用到 → 进 `references/`；每步必读的核心判断 → 留在 `SKILL.md`。
当用户要求发布时，用 SkillManage（Craft 模式）写入 `~/.workbuddy/skills/<name>/`（用户级）或 `.workbuddy/skills/<name>/`（项目级）。

### 再进化模式（升级已存在的子 skill · v3.2 新增）

第 1–6 步是「从零蒸馏」：输入原始资料，产出 v1.0.0 子 skill。当目标是**升级一个已经存在的子 skill** 时，走本模式——**把现有子 skill 本身（SKILL.md + 它的 `references/memory/`）当作来源**，叠加新的进化信号，跑**增量升级环**，而不是从零重抽。

**与从零蒸馏的关键区别**：加载现有 memory、只对变化部分重写、不重跑全量压缩；版本号从现有 `version-state.json` 续推（minor=结构变 / patch=仅更新内容），而非从 v1.0.0 起。

**输入（三要素）**：
- 现有子 skill：`SKILL.md` + `references/memory/`（`version-state.json` 快照 + `knowledge-grains/` 历史颗粒 + gold 集快照 + `evolution-log.md`）；
- 新信号（四选一或组合）：①新资料（文档/视频/网址/问答）②用户纠错（`corrections.md`）③知识库更新（KB Diff，见 evolution-protocol §11）④freshness 到期（重抽该源）；
- 可选：用户指定的变更范围 / 仅跑回归验证。

**流程**（复用升级环，详见 evolution-protocol §12）：
1. 载入：读 `version-state.json`（现有 dftq 快照 + 版本号 + 覆盖率/置信度基线 + gold 快照）；读 `knowledge-grains/` 历史颗粒（回归与回滚素材）。
2. 信号入记：新资料 → 第 1–2 步抽取为 `raw-extract-<source>-<ts>.json` 入 `knowledge-grains/`；纠错 → `feedback/corrections.md`；KB 更新 → 走 §11；freshness → 标 `freshness.valid_until` 过期。
3. 跑升级环（evolution-protocol §3 七步）：增量 diff → 跨次合并 → 重诊断 → 重压缩（**仅重写变化部分**，未变节点/示例不动）→ 回归验证（旧 gold + 新 gold 全过）→ 版本++ → 更新 `version-state.json` + `evolution-log.md`，保留旧版可回滚。
4. 输出：新版本 `SKILL.md` + 更新后的 `references/memory/`。

**不要求写回工厂**：本模式的目标子 skill 可以位于任意位置——用户级 `~/.workbuddy/skills/`、项目级 `.workbuddy/skills/`、或任意目录——只要它携带 `references/memory/`，就能被本工厂再进化。这与「把发现工厂自身的改进缺口写回本技能」是**正交**的两件事：子 skill 独立进化不依赖、也不要求写回工厂（项目约定"工厂技能改写回惯例：用户决定制，默认不动"）。

### 工厂自身进化（v3.0 新增）
蒸馏工厂本身也要像它产出的子 skill 一样自动升级：
- **学习信号**：每次蒸馏的运行记录（抽取/诊断/决策点选择/验证报告/落盘清单）+ 用户对产出的反馈（纠错/不满意）+ 子 skill 使用期的 failed-cases 回流。
- **沉淀**：每次完成蒸馏后把学习信号追加到 `references/factory-log.md`（来源类型、踩坑、用户反馈、可改进点）。
- **升级触发**：积累到阈值（默认每 10 次蒸馏）或用户主动要求时，蒸馏器自检自身 SKILL.md / 方法文档 / 模式库，把重复出现的失败模式固化为规则，工厂版本++（CHANGELOG 记录）。
- **元进化闭环**：工厂产出的子 skill 带进化机制出生（记忆库 + 升级环），子 skill 的反馈又回流改进工厂——形成「工厂 → 子 skill → 反馈 → 工厂」的双层进化闭环。

## 多源与知识库模式
用于把多个来源（多本电子书、文档集、在线知识库）一次性蒸馏成**一个**技能。

### 摄入（来源如何进入）
- **本地文件**（DOCX / PDF / EPUB / MD / TXT；老版 .doc 也行）：先解析为文本。DOCX/PDF/DOC 用 markitdown，PDF 也可用 pdf 技能；EPUB/MD 直接读。无需授权。
- **视频 / 网址**：视频按「媒体摄入协议」（第 17 节）提取图文块后作为来源文本传入；网址做正文提取 + 元数据抓取；多次收集走版本化增量更新（见第 1 步）。
- **在线知识库**（ima / 乐享 等）：本技能**不直接读取**知识库。先连接对应连接器并授权，再经其检索/获取工具拉取相关片段，把检索到的文本作为来源传入。连接与授权是前提——须明确提示。
- **本地知识库**（本地文档库 / 目录 / Obsidian vault / 本地索引）：**无需授权**——递归扫描支持的格式批量解析（走批量蒸馏编排，第 19 节），逐份抽取入 `knowledge-grains/` 后统一跨次合并；体量大或常变可建本地检索（全文/向量索引）走路由 B。来源标识 `local-kb/<相对路径>`。
- **知识库更新再进化**：在线与本地知识库蒸馏出的技能，知识库更新后走 **KB Diff**（见 references/evolution-protocol.md 第 11 节）——检索范围快照 + 指纹对比，只对新增/删除/修改的差异片段做增量升级，并重估骨架稳定规则。

### 跨源对齐（让它是融合而非拼接的额外一步）
对每个来源独立跑第 2 步抽取，然后对齐：
- **去重**：合并相同的规则/事实，保留一种规范表述。
- **消歧**：消解跨来源的同词异义；必要时附来源标签。
- **冲突裁决（权威 × 置信 感知）**：来源不一致时，按以下次序处置，绝不默默取平均或丢弃：
  - **权威等级表**：先按来源权威分级（如 官方规范 > 公司 SOP > 行业手册 > 社区经验 > 单篇博客），同级再用更新度（最近修订时间）破平。
  - **置信加权**：带入第 2 步的 `confidence`；高权威且高置信者优先，规则旁注明「置信：来源X(high) / 来源Y(medium)」。
  - **分歧显式标注**：选中的规则与落败的备选都写进技能（如「采用 A；备选 B，理由…」），确保可回溯、可纠错。
  - **「需人工确认」标记**：当权威同级、置信冲突、或涉及合规/安全红线时，在 `ambiguity` 中标记 `resolution: "needs_human"`，并在输出报告「残留盲区」列明，绝不自行定夺。
  - 每条冲突记录「冲突点 / 采用 / 舍弃 / 理由」四元组，汇入产物的溯源说明。
- **溯源**：记录每条核心原则来自哪个来源，便于第 5 步自检时标注支撑薄弱的断言。
- **媒体来源协同**：视频/网址来源的**图文块**与文档来源同样参与对齐——去重按图文块粒度（文字相同且关键帧相同 → 合并，保留双 source_ref）；消歧对画面 OCR 文字同样适用；冲突裁决的权威等级对平台内容（官方教程 > 博主讲解 > 评论区经验）照常生效。媒体来源的 `video_timestamp`/`frame_id` 锚点随合并保留。

### 融合封装
产出**一份** SKILL.md，其规则跨所有来源泛化。按统一能力命名（如 contract-review），而非按单本书。仅把来源特有内容当作边界 case 保留。

### 批量编排（多份资料流水线）
一次摄入多份资料（多文档/多视频/多网址混合）时：逐份走第 1–2 步抽取 → 全部落入 `knowledge-grains/` → 统一「跨次合并」成一份 dftq 树 → 一次压缩封装；已有技能时新批次只对增量部分跑合并与回归验证。细节见 references/distillation-method.md 第 19 节。

## 示例

输入（一段售前 FAQ 节选）：

> Q: 你们支持私有化部署吗？ A: 支持，标准版不支持，企业版支持，需联系销售评估。
> Q: 免费版有什么限制？ A: 最多 3 个成员、5GB 存储、无 API。
> Q: 能否导出数据？ A: 可以，管理员在设置-数据导出中操作，导出为 CSV。

输出（蒸馏出的技能定义）：

```markdown
---
name: product-presales-qa
description: 回答关于套餐档位、限制、部署与数据导出的售前问题。当用户询问套餐对比、版本限制、私有化部署或数据导出操作时使用。
agent_created: true
---

# 产品售前问答

## 概述
用一致、准确的套餐信息回答常见售前问题。

## 何时使用
- 免费版/付费版/企业版限制相关问题。
- 私有化/本地部署是否可用。
- 如何导出数据。

## 核心规则
- 免费版：≤3 成员、5GB、无 API。
- 私有化部署：仅企业版；转销售。
- 数据导出：管理员 → 设置 → 数据导出 → CSV。

## 回复风格
先给答案，再给条件。绝不承诺套餐表之外的功能。
```

本示例展示模式：扁平问答变成泛化规则 + 回复风格，而非抄录文本。

### v3.0 能力示例（媒体 + 进化，示意）

输入（一段教学视频 + 用户随后追加的补充）：

> 视频（12 分钟）：讲师用白板讲解「复利公式推导」，画面含公式与图表。
> 用户追加：文字补充「复利计算器在财务模块的入口与参数」。

处理（示意）：
- 第 1 步：视频五轨提取 → 转录 + 关键帧（白板公式 OCR）+ 画面描述（"讲师推导 FV=PV×(1+r)^n"）→ 图文块；与追加文字同源多通道。
- 第 2 步：图文块文字抽规则（公式/适用条件），OCR 与画面描述挂 dftq 的 `qi`（计算器工具）与 `detail`（参数表）；`source_media` 记 `video.timestamp: 00:03:20` 等锚点。
- 记忆板块：两次摄入的颗粒都入 `knowledge-grains/`；第二次摄入触发「新资料」进化信号。
- 升级环：增量 diff → 跨次合并（公式节点合并，参数表补挂）→ 回归验证（旧 gold：公式推导；新 gold：计算器参数）→ 版本 v1.0.0 → v1.1.0。

本示例展示：媒体来源的图文块如何进矩阵，以及子 skill 如何随资料完善自动升级。

### 多源示例

输入：两个来源融合成一个技能 ——
- 来源 A（书《客服话术》）：热情问候、镜像用户措辞、绝不说"不"而不给替代方案。
- 来源 B（公司 SOP）：1 小时内回复、账单问题升级到财务、每个案例录入 CRM。

输出（一个融合技能，而非两个拼块）：
- name: support-reply
- description: 融合"温情话术手册"与"公司 SOP（SLA、升级、记录）"用于客服回复。
- 核心规则：语气（热情/镜像/总给替代）+ SLA（1h）+ 升级（账单→财务）+ 记录（CRM）。
- 何时使用：起草或审阅任何客服回复。

本示例展示融合：话术手册的语气与 SOP 的硬性规则，变成一个连贯技能——已去重、已泛化，而非拼接。
