# 目标技能结构规范

每个蒸馏出的技能必须是另一个 WorkBuddy 实例可加载使用的合法技能。

## 文件布局
```
skill-name/
└── SKILL.md          （必需）
└── references/       （可选，按需加载的详细文档）
└── scripts/          （可选，确定性代码）
└── assets/           （可选，输出模板）
```

## SKILL.md 前置信息（必需）
- `name`：hyphen-case，仅小写字母/数字/连字符，≤40 字符，必须与目录名完全一致。
- `description`：第三人称，具体说明做什么、何时用。包含具体触发场景（文件类型、任务、用户说法）。
- `agent_created: true` —— 当技能由智能体产出时加（agent 创建的技能须有此项，以便 SkillManage 后续修改/删除）。

## SKILL.md 正文（必需，祈使句）
1. 概述 —— 1–2 句：能做什么。
2. 何时使用 —— 具体触发场景。
3. 核心原则/规则 —— 泛化，非转录。
4. 工作流步骤 —— 有序、可操作。
5. few-shot 示例 —— 2–4 个 输入 → 输出 对。

## 质量门槛（输出前自检）
- [ ] `name` 符合命名规则且等于目录名。
- [ ] `description` 写明何时用（第三人称）。
- [ ] 无逐字抄写；原则已泛化。
- [ ] 已处理边界/边缘 case。
- [ ] ≥2 个 few-shot 示例。
- [ ] 无超出来源的幻觉知识。
- [ ] 正文用祈使句。
- [ ] 已用 gold 测试集实跑验证（迭代闭环），通过率达门槛或已记录残留盲区。
- [ ] 抽取统一为标准化 JSON Schema v3.0（entities/relations/rules/decisions/metrics/qa/examples/steps/persona/edge_cases/ambiguity + structure/dftq/flows/mindmap + domain_ext + triggers/io_contract/conditions/state_machine/decision_tree/diagnosis/freshness/deps/permissions/acceptance + source_media），每项带 dim（道法术器/detail/cross）与 path（章节锚点）、confidence 与 source_ref；层级归属落在 dftq 桶（parent_id 表达 道⊃法⊃术⊃器⊃细节）。
- [ ] 已给出覆盖率（Coverage）估算与置信度（Confidence）分布，low/ambiguous 项已排入人工审阅优先级。
- [ ] 已完成「五层覆盖度诊断」：道/法/术/器/细节 的有/缺/薄/断链已判明，缺层已入残留盲区，未凭空补造；薄层与断链已提示。
- [ ] 子技能工作流已按「逆向逻辑、正向运用」（细节→定器→择术→循法→证道，细节→器→术→法→道）组织，每步向上校验，缺失层已标注。
- [ ] 来源过大/常变时，已采用路由 B（骨架技能 + 检索路由），而非把知识正文塞进 SKILL.md。
- [ ] 多源冲突已按「权威等级 × 置信加权」裁决，同级/合规冲突已标 `needs_human` 并列入残留盲区。
- [ ] 已向用户呈现「补料/继续决策点」（①暂不补充 / ②AI补充 / ③不补充）并记录所选路径；未表态时默认路径①。
- [ ] 路径①：抽取中间表示 + 缺/薄/断链清单已固化 `references/raw-extract-<source>.json`（status: staged）并写入 extract-log.md；路径②：AI 补足项全部标 `assumed` 且已重跑五层诊断；路径③：缺层/断链已写入 `references/known-gaps.md`。
- [ ] 已按 `domain_ext` 桶抽取领域特有字段（compliance / error_code / api_param / symptom_cause，按第 1 步识别的领域启用）；不适用则整桶留空并注明。
- [ ] 已按资料类型启用可选扩展桶：`triggers`（几乎所有技能）、`io_contract`（API/表单类）、`conditions`/`state_machine`（流程/工单/审批类）、`decision_tree`/`diagnosis`（多层判断/排障类）、`freshness`/`deps`（常变/课程类）、`permissions`（合规/金融/企业内部）、`acceptance`（输出需可验证类）；不适用则整桶留空并注明；抽了 `acceptance` 时第 5 步 gold 由 `assert` 生成。
- [ ] 已提供人工审阅交接清单：按 confidence 降序的待审项 + 冲突四元组 + `needs_human` 项。
- [ ] 已按产物落盘决策把内容分入 SKILL.md / references/ / scripts/ / assets/。
- [ ] 视频/网址来源已按「媒体摄入协议」提取（多模态五轨 / 图文块 / 三级去重 / 多次收集版本化），`source_ref` 含 video_timestamp / frame_id / url / collected_at。
- [ ] 子 skill 已预装记忆库 `references/memory/`（knowledge-grains/ + feedback/ + version-state.json + evolution-log.md），具备自动升级能力。

## 标准抽取 Schema v3.0（中间表示）
所有抽取统一输出此 JSON，按五层（事实与术语／规则与决策／内容素材／风格与边界／待定盲区）加结构/层级树/导图/流通层组织。它是「全量中间表示」：抽得细而全，作为第 3 步覆盖率度量基线；下游压缩才做「选择性落地」。每条抽取项都带 `dim`（道法术器/detail/cross 纵向维度）与 `path`（章节锚点）；**道法术器的层级归属**落在独立 `dftq` 桶（parent_id 表达 道⊃法⊃术⊃器⊃细节），与横向五层正交，构成完整抽取矩阵。
```json
{
  "entities":   [{"term":"","definition":"","aliases":[],"category":"","related":[],"dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"high|medium|low","source_ref":""}],
  "relations":  [{"from":"","rel":"","to":"","dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"","source_ref":""}],
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
    {"id":"d1","dim":"dao","title":"","summary":"","detail":"","parent_id":null,"confidence":"high|medium|low","source_ref":""},
    {"id":"f1","dim":"fa","title":"","summary":"","detail":"","parent_id":"d1","confidence":"","source_ref":""},
    {"id":"s1","dim":"shu","title":"","summary":"","detail":"","parent_id":"f1","confidence":"","source_ref":""},
    {"id":"q1","dim":"qi","title":"","summary":"","detail":"","parent_id":"s1","confidence":"","source_ref":""},
    {"id":"x1","dim":"detail","title":"","summary":"","detail":"","parent_id":"q1","confidence":"","source_ref":""}
  ],
  "flows":      {"forward":[{"from_dim":"dao","to_dim":"fa","trigger":"","note":""}],"reverse":[{"from_dim":"detail","to_dim":"qi","trigger":"","note":""}]},
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
  "permissions": [{"id":"p1","scope":"","who":"","auth":"","data_class":"public|internal|confidential|pii","guardrail":"","dim":"dao|fa|shu|qi|detail|cross","path":"","dftq_ref":"","confidence":"high|medium|low","source_ref":""}],
  "source_media": [{"id":"m1","type":"video|url|doc","uri":"","title":"","author":"","published_at":"","collected_at":"","video":{"timestamp":"","frame_id":""},"url":{"domain":""},"note":""}]
}
```
- `dim`：纵向层级 `dao`(道·原理宗旨价值观本质规律底线) / `fa`(法·方法论框架规则决策) / `shu`(术·具体步骤技巧话术窍门) / `qi`(器·工具系统模板术语指标) / `detail`(细节·参数·字段·边界·模板内容) / `cross`(跨层关系·流程衔接)。每条抽取项必打其一；`dim` 是「这条内容落在哪一层」的快速标记。
- `dftq`：**道法术器层级树主轴**。`id` 唯一；`parent_id` 指向上一层节点（道无父=null），形成「道⊃法⊃术⊃器⊃细节」归属链——一条道下挂多条法、一条法下挂多条术、一条术下挂多条器、一条器下挂很多细节，**每层子项数不设硬上限**。`summary` 节点摘要，`detail` 节点细节内容（参数/字段/模板正文）。这是子技能的主结构来源。
- `dftq_ref`：横向桶（rules/steps/…）可附此字段指向某 `dftq` 节点 id，建立「内容 → 层级」关联。
- `path`：章节锚点（如 `/第三章/3.2节/定价规则`），把细化知识锚定到原文位置，便于第 5 步精确溯源与按章节算覆盖率。
- `confidence`：来源支撑强度 high/medium/low；low 须进入 ambiguity 或 edge_cases，或显式降级为「需检索/需人工」。
- `source_ref`：段落/文档/来源标识（多源必填）；媒体来源支持 `video_timestamp`（如 `00:12:34`）、`frame_id`、`url`、`collected_at`，与 path 锚点并存，便于 gold 验证回溯到视频具体位置。知识库来源：在线用 `kb:<库名>`、本地用 `local-kb/<相对路径>`；骨架稳定规则可附 `kb_ref` 标注来源，供 KB Diff 时逐条重估。
- `severity`：规则强制级别 must（硬性）/ should（推荐）/ may（可选）。
- `metrics`：`comparator` 为比较符（>=/<=/=/in），量化阈值单独成桶，便于第 5 步 gold 断言校验。
- `structure`：`level/title/parent/aliases` 抽目录→章节→重点小标题层级树（**原文物理结构**），`aliases` 即现代名称/别称。与 `dftq`（**逻辑层级**）是两个维度，可并存。
- `flows`：`forward` 正向推导链（道→法→术→器→细节）、`reverse` 运行时逆向链（细节→器→术→法→道），每条含 `trigger` 与 `note`。
- `mindmap`：由 `structure`+`dftq`+`relations/entities` 派生的导图节点（`node/parent/children/dim`），仅长文/多章生成，短文跳过。
- `domain_ext`：**领域特有字段**桶（与六层并列的第七桶）。`ext_type` 预定义 `compliance`（合规条款）/ `error_code`（错误码）/ `api_param`（接口参数）/ `symptom_cause`（症状→病因）/ `other`（可扩展，如 `escalation` 升级规则）；`name`+`value` 记内容，`applies_when` 记适用情形，`constraint` 记校验/罚则/处理动作，`dftq_ref` 挂回层级树节点，`dim` 标纵向落点。按第 1 步识别的领域启用对应类型，不适用则整桶留空。领域适配表见 distillation-method.md 第 12 节。
- `triggers`：**触达/触发与意图**（可选桶）。`intent` 意图名、`patterns` 触发说法/关键词、`negative` 否定触发（怎么说绝不用）、`route_to` 路由目标（多技能竞争指向谁）、`priority` 优先级。下游 → 子技能「何时使用」与路由判断。几乎所有技能建议抽。
- `conditions`：**适用条件**（可选桶）。`type` 三态：`pre` 前置（执行前必须满足）/ `post` 后置（执行后保证）/ `env` 环境适用（平台/版本/区域/受众矩阵）；`applies_to` 指向步骤 order 或规则 id。
- `state_machine`：**状态迁移表**（可选桶，流程/工单/审批/审核类）。`state` 当前态 / `event` 事件 / `action` 动作 / `next_state` 下一态 / `guard` 守卫条件。下游 → 子技能状态分支逻辑。
- `acceptance`：**验收断言与反例**（可选桶，输出质量需可验证类）。`target` 验收对象（规则 id/步骤 order/dftq 节点）、`assert` 验收断言（怎么算答对）、`pass_condition` 通过条件、`trap_case` 陷阱题/反例、`gold_ref` 关联 gold 条目。下游 → 第 5 步 gold 集由 `assert` 直接生成（断言即判定点）。
- `io_contract`：**输入输出契约**（可选桶，API/表单/脚本类）。`target` 契约对象、`type` 三态 `input`（入参）/`output`（出参）/`failure`（失败模式）、`name` 参数名、`schema` 类型结构、`required` 必填列表、`default` 默认值、`example` 示例值。下游 → 输入输出格式约定 + `scripts/` 校验 + 失败处理分支。
- `decision_tree`：**决策树**（可选桶，多层判断/审核/风控类）。`node` 节点名、`parent` 父节点、`condition` 分支条件、`action` 动作、`fallback` 兜底、`depth` 层级——把扁平 `decisions` 树化为嵌套分支。
- `diagnosis`：**诊断树**（可选桶，排障/医疗/维修类）。`symptom` 现象、`causes[]` 候选原因数组（`cause`/`weight` 权重/`verify` 验证手段/`exclude_order` 排除顺序）、`danger_signals` 危险信号（先查危险再查常见）。
- `freshness`：**时效**（可选桶，政策/价格/版本类常变资料）。`target` 知识对象、`checked_at` 上次核验、`valid_until` 有效期、`update_freq` 更新频率、`superseded_by` 被谁替代、`reason` 变更原因。下游 → 路由B决策与过时提示。
- `deps`：**依赖**（可选桶，培训/课程/方法论类）。`from`→`to`、`type` 四态 `prereq`（前置依赖）/`depends_on`（依赖）/`conflicts_with`（冲突）/`supersedes`（替代）、`note`。下游 → 学习路径/调用顺序/冲突提示。
- `permissions`：**权限边界**（可选桶，合规/金融/医疗/企业内部）。`scope` 适用范围、`who` 谁能用、`auth` 所需授权、`data_class` 数据分级（public/internal/confidential/pii）、`guardrail` 红线行为。与 `domain_ext.compliance` 互补：compliance 记外部合规条款，permissions 记内部使用边界。
- `source_media`：**媒体来源元数据**桶（可选，视频/网址/多次收集时启用）。`type` 三态 `video`/`url`/`doc`，`uri` 来源地址、`collected_at` 收集时间（多次收集的版本键）、`video.timestamp`/`frame_id` 定位到视频具体位置。**网址内嵌视频**：`type=url` 且页面探测到视频时，在 `note` 标 `embedded_video`，并把解析出的视频源地址记入 `video.url`（可选扩展字段）；平台视频抓取失败时标 `platform_video` 并提示用户本地导入。**多视频形态（合集/主页展开）**：`uri` 记来源页（合集/主页 URL），`note` 标 `collection` + 展开数量，每个子视频各建一条 source_media（`video.url` 指实际视频地址、`parent_uri` 指来源页）——按视频 id 去重、各自可溯源。与 `source_ref` 组合使用，是媒体溯源与增量更新的锚点。
- 五层覆盖度诊断：抽完按 `dftq` 层级统计道/法/术/器/细节 有/缺/薄/断链；缺层不补造、薄层与断链提示，结果记入残留盲区。
- 度量口径：`Coverage = 进入技能的抽取项 / 总抽取项`；`Confidence 分布`为 high/medium/low 计数。
- 下游映射：`persona→系统提示`、`metrics→规则断言`、`examples→few-shot`、`relations→路由B检索`、`edge_cases→边界段`、`ambiguity→残留盲区`、`structure→章节目录`、`dftq→道法术器层级（子技能主结构）`、`mindmap→导图`、`flows→子技能逆向工作流`、`triggers→「何时使用」与路由`、`conditions/state_machine→前置检查与状态分支`、`acceptance→gold 集与反例`、`io_contract→格式约定与失败处理`、`decision_tree→多分支流程`、`diagnosis→排障顺序与危险预警`、`freshness/deps→路由B决策与依赖/过时提示`、`permissions→权限校验与 do_not`、`domain_ext→领域规则/参数表/条款`、`source_media→媒体溯源与增量更新锚点`、`dim→各层级落点`。

## RAG 路由骨架规范（路由 B）
当体量过大或动态性高时，产出：
- 一个**骨架技能**（SKILL.md）：仅稳定部分——能力定位、判断流程、输出模板、调用约定；
- 一条**检索路由**：正文含「涉及来源细节/事实，先去 `<知识库名/id>` 检索再作答」；
- 一份**索引约定**（写入 references/ 或正文）：检索后端、关键词、检索范围、是否需授权；
- 骨架正文须注明知识库名称/id，且不承载会随源过期的具体内容。

**路由 B 产物模板**（按此骨架填充）：
```markdown
---
name: <capability>-rag
description: <第三人称写明能力边界与触发场景，并注明"凡涉及来源细节/事实，先去 <知识库名/id> 检索再作答">
agent_created: true
---
# <能力名>（骨架版）

## 概述
<一句话：本技能只承载稳定判断，细节一律外挂检索。>

## 何时使用
- <触发场景 1> / <触发场景 2>

## 工作流步骤
1. 判断是否涉及来源细节/事实 → 涉及则先检索，不涉及直接用稳定规则。
2. 检索：关键词 <默认检索词>，范围 <检索范围>，授权 <是否需要>。
3. 基于检索结果 + 稳定规则作答。

## 检索路由
- 知识库：<name / id>
- 检索字段：<关键词、过滤条件>
- 授权：<需要 / 不需要，如何获取>

## 稳定规则（不随源更新变化的部分）
- <规则 1> / <规则 2>
```
核心是「骨架稳定、细节外挂」：SKILL.md 内不出现会过期的具体内容，所有事实性细节都指向检索。

## 残留盲区与人工审阅交接
产出技能时，把「没解决/需人定夺」的内容用统一格式固化，让人工一眼看到该审什么。

**`references/known-gaps.md` 模板**：
```markdown
# 已知缺口（Known Gaps）
> 生成时间：<ISO 时间>｜路径：<①暂存 / ②AI补充 / ③不补充>

## 缺层 / 断链
| 节点 | 层级 | 状态(缺/薄/断链) | 说明 | 处理建议 |
|---|---|---|---|---|

## 低置信项（confidence=low）
| 抽取项 | 内容 | 处理(保留/降级检索/需人工) | 依据 |
|---|---|---|---|

## needs_human 待定项
| 事项 | 为什么需要人 | 影响 | 建议 |
|---|---|---|---|

## 冲突四元组
| 冲突点 | 采用 | 舍弃 | 理由 |
|---|---|---|---|
```

**人工审阅优先级清单**：按 confidence 降序输出——`low` 与 `ambiguous` 项排最前（最高风险），随后是 `assumed` 补足项、`needs_human` 项、跨次合并的模糊项。每次交付附此清单。

## 记忆与进化底座（子 skill 出厂预装）
每个蒸馏产出的子 skill 发布时预装 `references/memory/`（结构、四类触发器与升级环详见 references/evolution-protocol.md）：
```
skill-name/references/memory/
├── knowledge-grains/     # 增量颗粒（raw-extract-<source>-<timestamp>.json，只增不改）
├── feedback/             # corrections.md / failed-cases.md / gap-notes.md
├── version-state.json    # 当前 dftq 快照 + 版本号 + 覆盖率/置信度基线
└── evolution-log.md      # 进化日志（触发 → 变更 → 验证 → 版本）
```
- 四类触发器：①新资料摄入 ②用户纠错 ③gold 失败（使用期通过率 <80%）④freshness 到期。
- 升级环：沉淀记忆 → 增量 diff → 跨次合并 → 重诊断 → 重压缩 → 回归验证（旧 gold + 新 gold）→ 版本++ 发布，失败即回滚。
- 铁律：增量优先 · 回归保护 · 可回滚。
- 质量门槛已含对应自检项（见上）；蒸馏工厂自身的进化记录于工厂的 `references/factory-log.md`（每 10 次蒸馏或用户要求时自检升级工厂版本）。

## 产物落盘决策
蒸馏出的内容按「读取时机」分目录，避免 SKILL.md 膨胀：
| 内容类型 | 落盘位置 | 理由 |
|---|---|---|
| 判断流程 / 核心规则 / 工作流步骤 / few-shot | `SKILL.md` | 每步必读 |
| 术语表 / 参数表 / 模板正文 / 长规则集 / 领域明细 / 验证报告 / 合并记录 / 盲区清单 / 抽取档案 | `references/` | 按需加载 |
| 解析器 / 校验器 / 格式化脚本 / gold 运行器 | `scripts/` | 确定性代码 |
| 输出模板 / 样例文件 / 话术模板 | `assets/` | 非代码素材 |

判定规则：单条内容超 2 屏、或只在特定分支用到 → `references/`；执行时每步都读的核心判断 → 留在 `SKILL.md`；可自动执行、结果确定的逻辑 → `scripts/`；非代码的模板/样例 → `assets/`。

## 作用域决策
- 用户技能 → `~/.workbuddy/skills/<name>/`（默认；跨项目跟随）。
- 项目技能 → `<repo>/.workbuddy/skills/<name>/`（与仓库协作者共享）。

## 多源约定
- 一个融合能力产出一个蒸馏技能；不要每个来源各产一个。
- `name` 反映统一能力（如 `contract-review`），绝不用单本书/文件名。
- 冲突裁决须「权威等级 × 置信加权」：优先取高权威高置信者，并显式标注备选与理由；权威同级、置信冲突或涉及合规/安全红线时，标记 `needs_human` 并列入残留盲区，绝不自行定夺。所有冲突记录「冲突点 / 采用 / 舍弃 / 理由」四元组。
- 在线知识库来源，把知识库名称/id 记入 `references/` 笔记，便于未来重蒸馏时溯源。
- 逐源原始抽取仅当用户要求时保留在 `references/`；否则融合后丢弃，避免膨胀。
