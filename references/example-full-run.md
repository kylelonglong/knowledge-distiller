# 完整端到端范例（Example Full Run）

演示：一份**客服售后资料**（FAQ + SOP 节选），从接收走到发布，全程展示 dftq 层级树、五层诊断、补料决策点、domain_ext、few-shot×逆向链、gold 验证，并在结尾演示 v3.0 的**记忆板块与自动进化**。本范例是**教学演示**，不是新技能产物；视频/网址来源的媒体摄入演示见 distillation-method.md 第 17 节。

## 输入资料（节选）

> Q1 你们支持退货吗？→ 7 天内无理由退货，需包装完好；定制商品不支持。
> Q2 退款多久到账？→ 审核通过后 1–3 个工作日原路退回。
> Q3 订单显示"配送中"3 天了怎么办？→ 先查物流单号，超 3 天未更新则升级人工核实，必要时补发。
> Q4 商品有问题找谁？→ 拍照/视频发客服，24h 内响应；食品变质立即下架同批次并上报。
> SOP：1 小时内回复；账单问题升级财务；每个案例录入 CRM；绝不承诺无依据的时效。
> 红线：绝不私自超出标准的补偿；绝不删除客户差评记录（合规要求）。

## 第 1 步 — 接收与解析

- 类型：FAQ + SOP 混合（叙述性规则 + 决策树）｜目标：客服售后应答技能｜禁止清单：不承诺无依据时效、不越权补偿。
- 单源；体量小（单篇，可概括进 2 页）且稳定 → **路由 A（全量嵌入）**。
- 领域识别：客服/售后 → 启用 `compliance` + `escalation`（domain_ext 预设表）。

## 第 2 步 — 抽取（标准表示 v3.0，节选）

```json
{
  "rules": [
    {"id":"r1","statement":"7 天内无理由退货","applies_when":"非定制商品且包装完好","severity":"must","exceptions":"定制商品不支持","dim":"fa","path":"/Q1","dftq_ref":"f2","confidence":"high","source_ref":"faq-q1"},
    {"id":"r2","statement":"1 小时内回复","applies_when":"所有咨询","severity":"must","exceptions":"","dim":"fa","path":"/SOP-1","dftq_ref":"f1","confidence":"high","source_ref":"sop"}
  ],
  "decisions": [
    {"condition":"物流超 3 天未更新","action":"升级人工核实，必要时补发","priority":"high","fallback":"先查物流单号","dim":"shu","path":"/Q3","dftq_ref":"s2","confidence":"high","source_ref":"faq-q3"},
    {"condition":"涉及账单","action":"升级财务","priority":"high","fallback":"","dim":"fa","path":"/SOP-2","dftq_ref":"f1","confidence":"high","source_ref":"sop"}
  ],
  "steps": [
    {"order":1,"name":"共情开场","input":"用户原话","output":"镜像措辞回应","tool":"话术模板","dim":"shu","path":"/SOP","dftq_ref":"s1","confidence":"medium","source_ref":"sop"}
  ],
  "edge_cases": [
    {"case":"食品变质","handling":"立即下架同批次并上报，24h 内响应","dim":"fa","path":"/Q4","dftq_ref":"f3","confidence":"high","source_ref":"faq-q4"}
  ],
  "persona": {"tone":"先共情后给答案","voice":"专业且温和","do_not":["承诺无依据时效","越权补偿","删除差评记录"],"values":["客户第一"],"dim":"dao","path":"/红线","dftq_ref":"d1","confidence":"high","source_ref":"sop"},
  "dftq": [
    {"id":"d1","dim":"dao","title":"客户第一","summary":"一切以客户利益为先","detail":"","parent_id":null,"confidence":"high","source_ref":"sop"},
    {"id":"d2","dim":"dao","title":"合规红线","summary":"绝不删差评、绝不越权补偿","detail":"","parent_id":null,"confidence":"high","source_ref":"sop"},
    {"id":"f1","dim":"fa","title":"服务时效法","summary":"1h 回复、账单升级财务、全录入 CRM","detail":"","parent_id":"d1","confidence":"high","source_ref":"sop"},
    {"id":"f2","dim":"fa","title":"退货政策","summary":"7 天无理由，定制除外","detail":"","parent_id":"d2","confidence":"high","source_ref":"faq-q1"},
    {"id":"f3","dim":"fa","title":"异常升级法","summary":"超时/变质升级人工","detail":"","parent_id":"d1","confidence":"high","source_ref":"faq-q3/q4"},
    {"id":"s1","dim":"shu","title":"镜像措辞开场","summary":"用用户原话回应情绪","detail":"","parent_id":"f1","confidence":"medium","source_ref":"sop"},
    {"id":"s2","dim":"shu","title":"物流核查","summary":"先查单号，超 3 天升级","detail":"","parent_id":"f3","confidence":"high","source_ref":"faq-q3"},
    {"id":"q1","dim":"qi","title":"CRM 话术库","summary":"调用标准话术模板","detail":"","parent_id":"s1","confidence":"high","source_ref":"tool-doc"}
  ],
  "domain_ext": [
    {"ext_type":"compliance","name":"差评记录不可删除","value":"所有差评记录原样保留","applies_when":"任何售后处理","constraint":"删改属违规，需上报","dftq_ref":"d2","dim":"dao","path":"/红线","confidence":"high","source_ref":"sop"},
    {"ext_type":"escalation","name":"配送超时升级","value":"超 3 天未更新→人工核实→必要时补发","applies_when":"物流异常","constraint":"升级须留 CRM 记录","dftq_ref":"s2","dim":"shu","path":"/Q3","confidence":"high","source_ref":"faq-q3"}
  ],
  "triggers": [
    {"id":"t1","intent":"退货咨询","patterns":["可以退货吗","怎么退","七天无理由"],"negative":["退款到账了吗","投诉"],"route_to":"退货流程","priority":1,"dim":"cross","path":"/Q1","dftq_ref":"f2","confidence":"high","source_ref":"faq-q1"},
    {"id":"t2","intent":"物流催问","patterns":["配送中","到哪了","什么时候到"],"negative":["退款"],"route_to":"物流核查","priority":1,"dim":"cross","path":"/Q3","dftq_ref":"s2","confidence":"high","source_ref":"faq-q3"}
  ],
  "state_machine": [
    {"state":"已发货","event":"超3天无物流更新","action":"升级人工核实","next_state":"人工处理中","guard":"先查单号确认","dim":"fa","path":"/Q3","dftq_ref":"f3","confidence":"high","source_ref":"faq-q3"}
  ],
  "acceptance": [
    {"id":"a1","target":"r1","assert":"回答须含'7天'且不含'定制商品可退'","pass_condition":"同时满足","trap_case":"客户问定制商品能否退货——必须答不能","gold_ref":"g1","dim":"fa","path":"/Q1","dftq_ref":"f2","confidence":"high","source_ref":"faq-q1"}
  ],
  "io_contract": [
    {"id":"io1","step_ref":"step-1","input_schema":{"user_msg":"string, required"},"output_schema":{"reply":"string"},"failure_mode":{"code":"E4001","msg":"空消息"},"dim":"qi","path":"/SOP","dftq_ref":"s1","confidence":"medium","source_ref":"sop"}
  ],
  "decision_tree": [
    {"id":"dt1","node_id":"n1","question":"是否为退货咨询？","branch":[{"label":"是","next":"退货流程"},{"label":"否","next":"其他"}],"default":"转人工","dim":"fa","path":"/Q1","dftq_ref":"f2","confidence":"high","source_ref":"faq-q1"}
  ],
  "diagnosis": [
    {"id":"dg1","symptom":"退款迟迟未到账","candidates":[{"cause":"银行处理中","prior":"高","verify":"查流水"},{"cause":"退款被拦截","prior":"中","verify":"查退款单状态"}],"exclude_order":["先查流水"],"red_flag":"金额异常请风控","dim":"shu","path":"/Q2","dftq_ref":"f1","confidence":"medium","source_ref":"faq-q2"}
  ],
  "freshness": [
    {"id":"fr1","checked_at":"2026-08-24","valid_until":"2026-12-31","superseded_by":"","dftq_ref":"f2","dim":"fa","path":"/Q1","confidence":"high","source_ref":"faq-q1"}
  ],
  "deps": [
    {"id":"dp1","prereq":["d1"],"blocks":["s2"],"rel":"prereq","note":"先懂客户第一原则再学物流核查","dim":"cross","path":"","dftq_ref":"d1","confidence":"high","source_ref":""}
  ],
  "permissions": [
    {"id":"pm1","who":"授权客服","auth":"工单系统登录","data_class":"PII","guardrail":"绝不输出客户身份证号全文","dim":"dao","path":"/红线","dftq_ref":"d2","confidence":"high","source_ref":"sop"}
  ],
  "source_media": [
    {"id":"m1","type":"doc","uri":"faq-sop合集.pdf","title":"客服FAQ与SOP","collected_at":"2026-08-24T10:00:00+08:00","note":"多次收集示例：同源再摄入时按 collected_at 版本化，diff 增量更新"}
  ],
  "flows": {"forward":[{"from_dim":"dao","to_dim":"fa","trigger":"确立原则后定规则","note":""}],"reverse":[{"from_dim":"detail","to_dim":"qi","trigger":"用户提问","note":""}]},
  "ambiguity": [
    {"issue":"定制商品退货争议","resolution":"needs_human","note":"政策未覆盖，需人工裁定","dim":"fa","path":"/Q1"}
  ]
}
```

## 五层覆盖度诊断

| 层 | 条数 | 状态 |
|---|---|---|
| 道 | 2 | 有 |
| 法 | 3 | 有 |
| 术 | 2 | 有（薄：s1 仅 1 条法下挂 1 术） |
| 器 | 1 | **薄/断链**：s2 下无器（物流核查没有挂工具） |
| 细节 | 0 | **缺**（本资料无参数级内容，属"缺层不补造"） |

- 断链：`s2（物流核查）→ 无 qi`；`q1 下无 detail`。
- 缺层：细节层为 0 → 标记"本资料缺细节层"，不编造。
- 残留盲区待写：断链 s2、缺细节层、定制退货争议（needs_human）。

## 补料 / 继续决策点

> 本次诊断：道 2（有）、法 3（有）、术 2（薄）、器 1（断链：s2 下无 qi）、细节 0（缺）。
> 请选择：① 暂不补充（记忆暂存）｜② AI 补充（用户校验）｜③ 不补充（直接封装）

**用户选择：② A1（AI 合理外推 + 用户校验）。**

AI 外推（全部标 `assumed`）：
```json
{"id":"q2","dim":"qi","title":"物流查询接口","summary":"按单号查物流轨迹","detail":"<待用户校验>","parent_id":"s2","confidence":"assumed","basis":"外推自 s2（物流核查）","source_ref":""}
```
重跑诊断：断链 s2 已补（器 2 条），细节层仍缺（属资料本身缺层，保留标记）。外推项进入第 5 步验证与人工审阅第一序列。

## 第 3 步 — 蒸馏压缩（层级树成品）

```
道 d1 客户第一
└─ 法 f1 服务时效法（1h 回复 / 账单→财务 / 全录 CRM）
   └─ 术 s1 镜像措辞开场（先共情后给答案）
      └─ 器 q1 CRM 话术库
道 d2 合规红线（绝不信口承诺 / 绝不删差评 / 绝不越权补偿）
└─ 法 f2 退货政策（7 天无理由，定制除外；争议→needs_human）
└─ 法 f3 异常升级法（配送超 3 天 / 变质下架上报）
   └─ 术 s2 物流核查（先查单号→超时升级）
      └─ 器 q2 物流查询接口 [assumed]
```
压缩策略：道/法层全保留（原则锚定）；术层合并"共情+给答案"；细节层缺 → 不强凑。few-shot 2 个（典型 + 边界）。

## 第 4 步 — 封装为技能（逆向逻辑 · 正向运用）

**工作流骨架（细节→器→术→法→道）**：
1. [细节] 抓取用户原话与关键信息（单号/商品/诉求）→ 2. [器] 选话术模板 / 调物流接口 → 3. [术] 镜像措辞、核查步骤 → 4. [法] 套时效与升级规则（1h/账单→财务/超 3 天升级）→ 5. [道] 校验：有没有承诺无依据内容？有没有触碰红线？无则输出。

**few-shot × 逆向链（节选）**：
```
输入：客户："我的订单显示配送中 3 天了，到底什么时候到？！"
推理：[细节] 单号未知、情绪激动；[器] 调物流查询接口/话术模板-物流类；[术] 镜像开场"我理解您等得很着急"→ 请客户提供单号核查；[法] 超 3 天未更新→升级人工核实，必要时补发；[道] 客户第一 + 绝不承诺无依据时效 → 校验：给不出确切时间，只给核实动作。
输出：共情 → 要单号 → 承诺 1 小时内反馈核查结果（不承诺具体送达日）。
```

**产出 SKILL.md 要点**（完整产物按 skill-schema 规范，此处略）：name 取统一能力 `after-sales-reply`（非按资料名）；正文含概述/何时使用/核心规则/逆向工作流/few-shot；domain_ext 的 compliance 红线进核心规则与 do_not，escalation 进决策步骤。

## 第 5 步 — gold 验证与迭代闭环

gold 集（3 条，含来源锚点）：
- g1 退货咨询（Q1）｜g2 配送超时追问（Q3）｜g3 食品变质投诉（Q4）

实跑结果（子 Agent 加载草稿 SKILL.md 逐条喂入）：
- g1 答对 ✓
- g2 **部分答对**：给了共情与核查，但漏了「升级人工」分支 → 原因：`缺规则`（升级条件在法 f3 里是术层隐性内容，未显式化）
- g3 答对 ✓

**回流**：回第 3 步，把「物流超 3 天未更新 → 升级人工核实（必要时补发）」从术层上提为显式决策规则（decisions），并加进工作流第 4 步。第 2 轮重跑：g2 答对，通过率 100%。

## 第 6 步 — 输出与验证报告

- **覆盖率（Coverage）**：抽取 15 项 → 进入技能 13 项 ≈ 87%；pending ambiguity 1（定制退货争议）。
- **置信度（Confidence）**：high 11 / medium 2 / low 0 / assumed 1（q2 物流接口，已列人工审阅第一序列）。
- **gold 通过率**：第 2 轮 3/3（100%），迭代 2 轮（≤3 达标）。
- **残留盲区**：细节层缺失（资料本身无参数级内容）；定制退货争议 needs_human；q2 为 AI 外推待用户校验。

本范例展示：一份资料从「扁平问答」经 dftq 层级树 + 诊断 + 决策点 + 领域桶 + 逆向封装 + 实跑回流，产出**有原则锚定、有验证证据、盲区透明**的技能。

## 附：v3.0 记忆与自动进化演示（升级演练）

发布后的子 skill `after-sales-reply` 出厂预装记忆库：

```
references/memory/
├── knowledge-grains/raw-extract-faq-sop-20260824.json   # 本次抽取颗粒（只增不改）
├── feedback/                    # 使用期填充：corrections / failed-cases / gap-notes
├── version-state.json           # dftq 快照 + version 1.0.0 + 覆盖率 87%
└── evolution-log.md             # v1.0.0 出厂记录
```

**升级演练（触发器② 用户纠错）**：
1. 用户反馈："定制商品其实可以换货，写死'不支持'不对" → 写入 `feedback/corrections.md`；
2. 属高风险纠错（政策红线级）→ **即时触发**升级环；
3. 增量 diff：仅 `f2 退货政策` 节点变化 → 跨次合并更新该节点（`exceptions: 定制商品不支持退货，但支持换货`），其余节点不动；
4. 重诊断 → 重压缩 → **回归验证**：旧 gold（g1 断言含'7天'且不含'定制商品可退'）+ 新 gold（换货断言）双跑通过；
5. 版本 1.0.0 → 1.1.0（patch：内容修正），evolution-log 追加一行，旧版可回滚。
