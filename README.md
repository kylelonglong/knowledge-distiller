# 知识蒸馏工厂（Knowledge Distiller）· 开源版 v3.3

把任意领域知识源——文档、FAQ、SOP、转录稿、问答、**视频、网页链接、知识库**——蒸馏成结构化、可直接发布的 WorkBuddy 技能（Skill）。本仓库是**完整开源版**（MIT）：算法、抽取矩阵、进化协议全部开放，可自由使用、修改、再分发。

> 你的知识 → 一个可复用的技能；你的技能 → 能随资料持续进化的智能体。

---

## 它是什么

一个"技能工厂"（元技能）：给定一份知识源，产出完整的 SKILL.md（名称、描述、步骤、few-shot 示例）及配套 references。

- **蒸馏而非转录**：去除冗余、消解冲突、提炼可泛化的核心原则、捕获边界 case，始终保留示例。
- **道法术器层级树**：知识按 道 ⊃ 法 ⊃ 术 ⊃ 器 ⊃ 细节 五层组织，子技能按「细节 → 器 → 术 → 法 → 道」逆向链工作（定器 → 择术 → 循法 → 证道，每步向上校验）。
- **媒体摄入**：视频五轨提取（ASR + 场景关键帧 + 字幕 + OCR + 元数据）→ 时间轴对齐成图文块；网址内嵌视频探测；多视频/合集/主页批量展开。
- **双层进化**：
  - **子技能进化**：每个产物自带 `references/memory/` 进化底座，喂新资料 / 纠错 / gold 失败 / 时效到期即可增量升级（升级环七步，版本续推）。
  - **工厂自身进化**：工厂每 10 次蒸馏或用户要求时自检升级；你也可以直接 fork 本算法改进后发布派生版本。

## 快速上手

1. **安装**：把本目录放入 `~/.workbuddy/skills/knowledge-distiller/`（用户级，所有项目可用），或 `.workbuddy/skills/knowledge-distiller/`（项目级）；也可在 WorkBuddy 中从 zip 导入。
2. **喂素材**：直接说"把这份资料蒸馏成 skill"，附上文档 / FAQ / 视频链接 / 网页链接。
3. **走 6 步工作流**：接收解析 → 抽取（标准表示）→ 压缩 → 封装 → 验证（gold 实跑）→ 输出。
4. **产出**：子技能落到 `out/<skill-name>/`，用 SkillManage 写入目标目录即发布。

详细用法见 `SKILL.md`；机制细节见 `references/`。

## 子技能进化（人人都能）

拿到任何一个子技能（无论是不是本工厂产出），只要它带 `references/memory/`：

```
输入：现有子技能 + 新信号（新资料 / 纠错 / 知识库更新 / 时效到期）
处理：加载现有 memory → 增量升级环（沉淀 → diff → 合并 → 重诊断 → 重压缩 → 回归验证 → 版本++）
输出：新版本子技能（版本从 version-state.json 续推）
```

说一句"把这个技能再进化一下，这是新增资料"即可。详见 `references/evolution-protocol.md` §12。

## 工厂自身进化

- **自检升级**：工厂使用中每完成 10 次蒸馏（或你要求时）触发一次自检，把发现的缺口/可优化点写入 factory-log，确认后升版本。
- **社区派生**：MIT 许可下，你可以 fork、修改抽取算法/压缩规则/进化协议，发布你自己的版本（建议同步更新 CHANGELOG 与版本号）。

## 目录结构

```
knowledge-distiller/
├── SKILL.md                     # 工厂主文件（6 步工作流 + 再进化 + 工厂进化）
├── CHANGELOG.md                 # 版本演进（v1.0 → v3.3）
├── LICENSE                      # MIT
├── references/
│   ├── distillation-method.md   # 蒸馏方法全集（配方/层级树/媒体摄入/冲突裁决…）
│   ├── skill-schema.md          # 产出规范 + 抽取 Schema v3.0 + 质量清单
│   ├── evolution-protocol.md    # 记忆与自动进化协议（§12 再进化 / §13 触发器边界）
│   ├── verify-protocol.md       # gold 验证实操手册
│   └── example-full-run.md      # 端到端教学范例
└── scripts/
    ├── run_gold.py              # gold 预筛 + 验证报告
    ├── dedup_frames.py          # 关键帧三级去重
    └── media-ingest-guide.md    # ffmpeg/whisper/OCR/yt-dlp 工具链装配指引
```

## 贡献

欢迎提改进：新的领域抽取预设、更好的压缩规则、进化协议增强、工具链脚本等。改动建议遵循：

- 改 Schema 须同步 `SKILL.md` 与 `skill-schema.md` 的版本标签 + `CHANGELOG.md`。
- 保持"蒸馏而非转录、保留 few-shot"的核心原则。

## License

MIT — 详见 [LICENSE](LICENSE)。
