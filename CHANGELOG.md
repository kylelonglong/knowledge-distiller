# Changelog

## v3.3（2026-08-24）— 开源版（MIT · 移除封装双轨 · 进化能力全量开放）
- **开源化**：本版本为**完整开源版**（MIT License），替代此前"公开壳子 + 私有后端/托管服务"的封装分发形态。任何人可自由使用、修改、再分发。
- **产物全量开放**：移除产物脱敏/剥离逻辑——子技能默认携带 `references/memory/` 进化底座与全部可选用桶，**子技能进化（§12 再进化模式）开箱即用**。
- **工厂自身进化开放**：任何持有本工厂的人均可按「工厂自身进化」节自检升级，也可自行修改算法并派生新版本（开源协议允许）。
- **交付形态**：单目录技能包（10 文件）→ 官方 `package_skill.py` 打包为 zip，可直接导入 WorkBuddy / 上架 SkillHub。
- 工厂版本 v3.2 → v3.3；Schema 仍为 v3.0（本次未改抽取矩阵）。

## v3.2（2026-08-24）— 再进化模式一等入口 + 独立子 skill 触发器监控边界
- **再进化模式（升级已存在的子 skill）一等入口**：SKILL.md 新增「再进化模式」段 + evolution-protocol 新增 §12——把现有子 skill（SKILL.md + 它的 `references/memory/`）当来源、叠加新信号（新资料 / 纠错 / KB 更新 / freshness 到期）跑**增量升级环**（加载现有 memory，不重跑全量压缩）；明确"不要求写回工厂"——任何携带 `references/memory/` 的子 skill（用户级 / 项目级 / 任意目录）都可作为再进化目标；与"从零蒸馏"的关键区别写入文档。补「何时使用」触发识别一条。
- **独立子 skill 触发器监控边界**（缺口 2）：evolution-protocol 新增 §13——四类触发器中 ①② 天然用户驱动（手动即触发）；③④（gold 失败 / freshness 到期）对**未挂监控的独立子 skill** 退化为手动触发（用户说"重新进化 / 验证"），保持"写回工厂 vs 独立进化"边界清晰；真·自动需 optional automation（默认不开启）。
- 工厂版本 v3.1 → v3.2；Schema 仍为 v3.0（本次未改抽取矩阵）。

## v3.1（2026-08-24）— 21 项优化落地（一致性 + scripts 实体化 + 机制细化）
- **一致性修复**：example-full-run 标题 v2.2→v3.0；distillation-method 第8节 Schema 版本与全字段补全；SKILL.md / skill-schema.md 下游映射补 `source_media`；SKILL.md 第6步落盘补 `memory/`、输出报告新增第5项「版本与进化状态」。
- **scripts/ 实体化**：新增 `scripts/run_gold.py`（gold 判定预筛 + 验证报告生成，标准库，支持回归对比）、`scripts/dedup_frames.py`（关键帧三级去重：dHash + 直方图 + OCR 接口位）、`scripts/media-ingest-guide.md`（ffmpeg / faster-whisper / PaddleOCR / scenedetect / yt-dlp 工具链装配指引 + 平台视频解析 + 失败兜底）。
- **领域预设扩展**：domain_ext 预设从 4 类扩至 8 类（新增财税 tax_item / 电商 logistics_status / 医疗 contraindication / 教育 learning_path）。
- **媒体摄入增强**：第17节新增画面语义描述、说话人分离、自动章节分段三通道；SKILL.md 第1步同步。
- **机制细化**：跨次合并相似度实现口径（n-gram Jaccard 粗筛 + LLM 判定 + 无 LLM 降级）；路径②A1/A2/A3 用户校验流程（确认/修改/删除三选一）；多源跨源对齐补媒体图文块协同；批量蒸馏编排（新第19节）。
- **进化协议细化**：新增第8节默认参数表（阈值集中）、第9节反馈写入时机与线上回测、第10节路由 B 技能进化；factory-log 结构化模板；gold 集快照进 version-state。
- **SKILL.md 示例区**：新增 v3.0 能力示例（教学视频 + 增量资料的媒体摄入与自动进化演示）。
- **媒体来源展开（多视频形态）**：第17节新增来源形态判定与展开机制——S1 单视频 / S2 多视频页 / S3 合集·播放列表 / S4 主页·空间 / S5 多链接输入，`--flat-playlist` 预扫展开 + 数量管控（>20 条裁剪：全部/最近 N 条/时间段/合集/关键词）+ 按视频 id 去重；SKILL.md 第1步、media-ingest-guide（yt-dlp 展开命令）、source_media 说明（collection/parent_uri）同步。
- **知识库再进化 + 本地知识库蒸馏**：evolution-protocol 新增第11节 **KB Diff**（检索范围快照 kb_snapshot + 指纹对比 + 新增/删除/修改三分 + 骨架规则 freshness 重估 + 探针检索质量对比）；distillation-method 新增第20节「知识库来源与蒸馏」——在线（连接器授权）与**本地知识库**（目录/Obsidian/本地索引，无需授权，走批量编排与本地检索路由 B）；SKILL.md 多源模式摄入拆在线/本地 + 更新再进化提示；source_ref 补 `kb:<库名>` / `local-kb:<路径>` 标识。
- 校验全绿（Skill is valid!），zip 已刷新。

## v3.0（2026-08-24）— 媒体摄入 + 记忆板块 + 双层自动进化
- **媒体摄入协议**（第1步扩展）：视频/网址输入——视频走多模态五轨提取（音频 ASR / 场景切分关键帧 / 字幕校正 / 画面 OCR / 元数据）+ 关键帧三级去重（pHash + 直方图 + OCR 文本差异）+ 时间轴对齐成图文块；网址正文提取 + 元数据抓取 + **内嵌视频探测**（直链 / 页面 video·og:video / 平台分享页，探测命中走视频五轨流程，与正文合并为多通道输入）；同一来源**多次收集**版本化增量更新（collected_at 为版本键）。
- **记忆板块**（第2步↔第3步之间）：子 skill 出厂预装 `references/memory/`（knowledge-grains / feedback / version-state.json / evolution-log.md），为自动进化提供底座。
- **双层自动进化**：子 skill 四类触发器（新资料 / 纠错 / gold 失败 / freshness 到期）→ 升级环（沉淀 → diff → 合并 → 重诊断 → 重压缩 → 回归验证 → 版本++），增量优先 · 回归保护 · 可回滚；蒸馏工厂自身每 10 次蒸馏或用户要求时自检升级（factory-log）。
- **新增** `references/evolution-protocol.md`：进化协议详述（触发器 / 升级环七步 / 回归验证 / 版本管理与回滚 / 双层进化）。
- **新增** `source_media` 桶（Schema v3.0）：媒体来源元数据（type / uri / collected_at / video.timestamp / frame_id）。
- distillation-method.md 新增第 17 节「媒体摄入协议」、第 18 节「记忆与双层进化」。
- SKILL.md / skill-schema.md Schema 升 v3.0；质量门补媒体摄入与记忆库自检；skill-schema.md 新增「记忆与进化底座」节。
- example-full-run.md 与 verify-protocol.md 同步（范例加 source_media 与进化升级演练；验证协议加第 8 节升级回归验证）。

## v2.5（2026-08-24）— 补充扩展桶（契约/推理树/生命周期/治理）
- **新增** `io_contract` 桶（输入/输出契约）：step_ref / input_schema / output_schema / failure_mode；深化 steps，面向 API/接口/脚本类资料。
- **新增** `decision_tree` 桶（决策树化）：node_id / question / branch / default / weight；把扁平 decisions 升为嵌套分支，面向诊断/客服分流。
- **新增** `diagnosis` 桶（诊断树）：symptom / candidates[`cause`,`prior`,`verify`] / exclude_order / red_flag；诊断类专用。
- **新增** `freshness` 桶（时效）：checked_at / valid_until / superseded_by；政策/价格/版本类等常变知识。
- **新增** `deps` 桶（依赖）：prereq / blocks / rel；培训/课程类学习顺序。
- **新增** `permissions` 桶（治理边界）：who / auth / data_class / guardrail；合规/金融/医疗/企业内部安全红线。
- SKILL.md / skill-schema.md 的 Schema 升 v2.5（标准抽取矩阵扩充至 11 横向桶 + dftq + 7 组可选扩展桶全覆盖）。
- distillation-method.md 新增第 16 节「补充扩展桶」。
- example-full-run.md 与 verify-protocol.md 同步（第2步示例补 io_contract/decision_tree/diagnosis/freshness/deps/permissions 片段；验证协议补扩展桶验证要点）。

## v2.4（2026-08-24）— 可选抽取维度（触达/条件/验收）
- **新增** `triggers` 桶（触达·触发与意图）：intent / patterns / negative（否定触发）/ route_to / priority；下游 → 子技能「何时使用」与路由。几乎所有技能建议抽。
- **新增** `conditions` + `state_machine` 桶（适用条件·状态机）：pre/post/env 三态条件 + 状态迁移表（state/event/action/next_state/guard）；面向流程/工单/审批/审核类资料。
- **新增** `acceptance` 桶（验收·断言与反例）：target/assert/pass_condition/trap_case/gold_ref；**第 5 步 gold 由 assert 直接生成**，抽取与验证闭环。
- SKILL.md / skill-schema.md 的 Schema 升 v2.4（版本标签统一从 v2.2 修正）；下游映射补 triggers/conditions/state_machine/acceptance/domain_ext。
- 质量门新增「已按资料类型启用可选扩展桶」自检项。
- distillation-method.md 新增第 15 节「可选抽取维度」（字段定义 + 示例 + 启用建议表 + 与既有矩阵关系）。
- example-full-run.md 与 verify-protocol.md 同步（gold 可由 acceptance 生成）。

## v2.3（2026-08-24）— 十项完善落地
- **新增** `domain_ext` 桶（第2步）：合规条款 / 错误码 / 接口参数 / 症状→病因 领域特有字段，每条挂 dftq 节点；配套 4 类领域预设模板（客服/合规/代码/排障）→ distillation-method.md 第 12 节。
- **新增** 跨次续抽与合并规则：路径①的「跨次合并四步」（归一化→精确合并→同义合并→补挂裁决）+ 相似度阈值 → distillation-method.md 第 13 节。
- **新增** few-shot × 逆向工作流映射：示例按 `[器][术][法][道]` 标注组织 → SKILL.md 第4步 + distillation-method.md 第 14 节。
- **新增** `references/verify-protocol.md`：第5步 gold 验证实操手册（gold 构造/实跑加载/判定/回流/豁免）。
- **新增** `references/example-full-run.md`：完整端到端范例（客服资料跑通 6 步 + dftq + 诊断 + 决策点②A1 + domain_ext + 验证报告）。
- **新增** `references/known-gaps.md` 模板与人工审阅交接清单（skill-schema.md「残留盲区与人工审阅交接」节）。
- **新增** 产物落盘决策规则：SKILL.md / references / scripts / assets 划分（skill-schema.md「产物落盘决策」节）。
- **新增** 路由 B 骨架产物模板（skill-schema.md「RAG 路由骨架规范」节）。
- **补齐** 质量门：决策点三路径、记忆档案、known-gaps、domain_ext、审阅交接、落盘 6 条新自检项。
- **新增** 本 CHANGELOG.md。

## v2.2（2026-08-24）— 道法术器层级树 + 决策点
- 道法术器从平铺升级为**层级嵌套树**（道⊃法⊃术⊃器⊃细节），每层子项不设硬上限；独立 `dftq` 桶（id/parent_id/dim/title/summary/detail/confidence/source_ref）。
- 新增 structure（原文物理结构）、flows（正逆向流通）、mindmap（派生导图）三桶。
- 五层覆盖度诊断（有/缺/薄/断链），「缺层不补造」。
- 补料/继续决策点三路径（①暂不补充记忆暂存 ②AI补充用户校验 ③不补充直接封装），默认路径①。

## v2.1 — 道法术器维度 + 结构/导图/流通桶
- 引入道法术器维度（dim）与 structure/flows/mindmap 桶；path 章节锚点。

## v2.0 — 标准表示 v2
- 统一 JSON Schema（11 桶，五层）；覆盖率/置信度度量；优化项 A/B/C/D（迭代验证/标准表示/RAG路由/冲突裁决）。

## v1.0 — 基础六步
- 6 步工作流：接收解析 → 抽取 → 压缩 → 封装 → 验证 → 输出；六类蒸馏配方。
