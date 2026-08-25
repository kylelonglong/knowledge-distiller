# 媒体摄入工具链装配指引（Media Ingestion Toolchain）

本指引是「媒体摄入协议」（distillation-method.md 第 17 节）的执行层装配手册：给出每一步对应的工具、安装命令、用法示例与失败兜底。**协议负责"抽什么"，本手册负责"怎么抽"**。

## 0. 工具总览

| 协议步骤 | 工具 | 安装 | 说明 |
|---|---|---|---|
| 视频下载 / 平台解析 | `yt-dlp` | `pip install yt-dlp` | B站 / YouTube / 多数平台；需登录的平台加 `--cookies` |
| 抽帧 / 音频抽取 | `ffmpeg` | 官网或 `winget install ffmpeg` / `brew install ffmpeg` | 场景切分后逐镜头抽帧、转 wav |
| 场景切分 | `scenedetect`（PySceneDetect） | `pip install scenedetect` | 检测镜头切换，替代均匀抽帧 |
| ASR 转录 | `faster-whisper` / `openai-whisper` | `pip install faster-whisper` | 词级时间戳；中文用 `large-v3` / `medium`，快测用 `tiny` |
| 字幕校正 | `ffmpeg` 提字幕轨 / 平台字幕 | — | SRT 与 ASR 对齐（按时间戳） |
| 画面 OCR | `PaddleOCR`（推荐中文）或 `tesseract` | `pip install paddleocr` / `tesseract-ocr` | 提取 PPT/白板/代码内文字 |
| 关键帧三级去重 | `scripts/dedup_frames.py` | `pip install pillow` | dHash + 直方图 + OCR 文本差异 |
| gold 判定 | `scripts/run_gold.py` | 标准库 | 验证预筛 + 报告 |

## 1. 典型流水线（视频 → 图文块）

```bash
# ① 平台视频解析（B站/YouTube 等；抖音/视频号需登录 cookie）
yt-dlp -f "bv*+ba/b" -o "video.%(ext)s" <平台链接>
# 失败兜底：签名/风控抓不到 → 提示用户客户端下载后本地导入，source_media.note 标 platform_video

# ② 场景切分（代替均匀抽帧）
scenedetect -i video.mp4 detect-content --threshold 27 list-scenes -o scenes.csv

# ③ 按场景抽关键帧（每镜头 1–3 帧）+ 音频抽取
ffmpeg -ss <镜头起点> -i video.mp4 -frames:v 1 frames/frame_<n>.jpg
ffmpeg -i video.mp4 -ac 1 -ar 16000 audio.wav

# ④ ASR 转录（词级时间戳）
faster-whisper audio.wav --model medium --language zh --output_format srt --output_dir trans/

# ⑤ 画面 OCR（每关键帧）
paddleocr --image_dir frames/ --lang ch --use_angle_cls true   # 或用 tesseract {path} stdout -l chi_sim

# ⑥ 关键帧三级去重
python scripts/dedup_frames.py --frames-dir frames/ --out keep_list.txt \
    --hash-threshold 6 --hist-threshold 0.05 \
    --ocr-cmd "tesseract {path} stdout -l chi_sim"

# ⑦ 按时间戳对齐 → 图文块（人工/AI 按 keep_list + srt + ocr 组装，或写脚本聚合）
```

## 2. 网址 → 内嵌视频探测（第17节三级探测的执行）

| 级别 | 做法 |
|---|---|
| ① 直链 | URL 后缀是 `.mp4/.webm/.m3u8` → `ffmpeg -i <url> -c copy local.mp4` 或 yt-dlp |
| ② 页面结构 | 抓 HTML 找 `<video src>` / `og:video` / `twitter:player`；`m3u8` 流用 ffmpeg 拉取 |
| ③ 平台分享页 | 域名识别（bilibili/douyin/youtube/weixin 视频号）→ yt-dlp 按平台规则解析 |

## 2.5 多视频形态展开（合集 / 播放列表 / 主页 / 多链接）

```bash
# ① 预扫列表（不下载，秒级）：列 id 与标题，用于判定形态与裁剪范围
yt-dlp --flat-playlist --print "%(id)s | %(title)s" <合集/频道/主页URL>

# ② 按范围下载：最近 20 条（合集/主页）
yt-dlp --playlist-end 20 -f "bv*+ba/b" -o "videos/%(playlist_index)03d_%(id)s.%(ext)s" <URL>
#    全部：去掉 --playlist-end；指定时间段：加 --dateafter 20260101 --datebefore 20260601
#    只下载合集内的特定章节：yt-dlp --playlist-items 3-8 <URL>

# ③ 多链接输入：N 个 URL 写入 urls.txt，逐行处理（各自先判定形态再展开）

# ④ 去重合并：按 %(id)s 建集合，跳过已处理视频；source_media 记 parent_uri（来源页）+ note: collection
```

**数量管控规则**：预扫清单 >20 条时先向用户确认裁剪范围（全部 / 最近 N 条 / 时间段 / 指定合集 / 关键词过滤），再批量下载摄入——避免一次性拉取几百条撑爆处理与上下文。

## 3. 画面语义描述（可选增强，清单9）

对保留的关键帧调用多模态模型生成一句话画面描述，并入图文块的文本流（如 `[画面] 白板上写着 E=mc²，讲师在推导相对论`）。描述与 OCR 互补：OCR 拿"写了什么"，描述拿"在讲什么"。

## 4. 说话人分离 / 自动章节（可选增强，清单10）

- **说话人分离**：`pyannote.audio`（pip install pyannote.audio）→ ASR 文本按说话人分段标记 `[说话人A/B]`，访谈/播客类蒸馏时按人归组。
- **自动章节分段**：场景切分 + 转录文本聚类（或 LLM 按语义切章）→ 生成章节标题与时间轴，长视频先章节化再蒸馏，`structure` 桶可直接复用章节树。

## 4.5 OCR 竖排处理（竖版页面 / 古籍 / 竖排图文）

OCR 引擎默认按「横排从左到右」假设输出，**竖排中文**（文字从上到下、列从右到左，如古籍 / 竖版标题 / 对联）会被读成乱序或逐字散列。用 `scripts/ocr_layout.py` 做「检测 → 按列重组 → 右起排序」。

**① 各引擎 OCR 输出 → 统一 JSON**（每块带边框 + 文本，四点框自动兼容）：

```bash
# PaddleOCR（Python API 拿 result 转 JSON，或直接存 json）
paddleocr --image_dir frames/ --lang ch --use_angle_cls true
#   → 每条记录转 {"box":[x1,y1,x2,y2] 或 四点,"text":...,"conf":...}
# rapidocr：engine.predict(img) → boxes/texts/scores → 同结构
# tesseract：tesseract img stdout -l chi_sim tsv → 按 left/top/width/height 组 box，滤低置信
```

**② 重组**（把 OCR JSON 喂给重排器）：

```bash
python scripts/ocr_layout.py --input ocr.json --mode auto        # 自动检测竖排 → 右起重组（默认）
python scripts/ocr_layout.py --input ocr.json --mode vertical --column-order ltr --mark-columns
#   --mode auto|vertical|horizontal；--column-order rtl(右起,默认)|ltr(左起)；--mark-columns 输出 [列N] 便于核对
#   检测规则：窄块（宽 ≤ 高×0.7）占比 ≥50% 判竖排；用户明示竖排时直接 --mode vertical
```

**③ 旋转兜底**（OCR 单字识别率低时：竖排转横排再 OCR）：

```bash
ffmpeg -i page.jpg -vf "transpose=1" page_rot90.jpg        # 顺时针 90°（transpose=2 逆时针）
# 或 Pillow：python -c "from PIL import Image; Image.open('p.jpg').rotate(-90, expand=True).save('r.jpg')"
```

旋转后重新 OCR（此时文字已横排，引擎识别率更高），再把结果坐标**反变换回原图**后仍走 `ocr_layout.py` 重组；或旋转后直接按横排阅读顺序核对。仍不理想 → 保留原帧作视觉证据，OCR 文本标 low 进人工审阅。

**④ 标注**：竖排来源在 `source_media.note` 标 `vertical_text`，与 `platform_video` / `asr_only` 同体系，便于溯源与再蒸馏。

## 5. 失败兜底规则

| 场景 | 处理 |
|---|---|
| 平台需登录 / 签名 / 风控 | 提示用户客户端下载 → 走本地视频输入；source_media.note 标 `platform_video` |
| ASR 语言识别差 | 显式指定 `--language zh`；无字幕时以 ASR 为准并标 low confidence |
| OCR 误识别 | 保留原始帧作视觉证据（图文块图片不删），OCR 文本标 low 并进人工审阅 |
| 视频无有效音频（纯画面教学） | 跳过 ASR，仅关键帧 + OCR + 画面语义描述三通道 |
| 网址抓取失败（短暂网络/限流） | 重试 ≤3 次 + 备用通道（§5.5） |
| 网址抓取失败（沙箱通道序列化故障） | **非工厂责任**——立刻停手，不要逐 URL 重试；提示用户重启会话 |

## 5.5 网址渠道失败分级 · 备用通道命令清单

> 配合 distillation-method §17.1 使用。本节给"动手层"的命令模板。

### ① 批次前通道健全性探测（30s 预算）

```bash
# Bash + curl（与 WebFetch 是独立通道，WebFetch 限流时常仍能成功）
curl -sI -o /dev/null -w "%{http_code} %{time_total}s\n" --max-time 10 https://example.com/
# 也可用 WebFetch 单次空跑 https://example.com/ 探测
# 期望：200/301/302 之一；429/5xx → A 类（限流/抖动，可重试）；连接拒/超时 → A 类
# 关键：若两次探测都"参数 undefined" → C 类（沙箱通道坏了），立刻停手告知用户
```

### ② A 类失败的重试与备用通道（按序尝试）

```bash
# 方案 1：原样重试（带退避与 UA）
for i in 1 2 3; do
  curl -L --max-time 30 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
       --retry 1 --retry-delay $((2**i)) -o raw/page.html "<URL>" \
    && break || sleep $((2**i))
done

# 方案 2：让 yt-dlp 接手（部分平台反爬会绕过）
yt-dlp --no-check-certificates -U --user-agent "Mozilla/5.0 ..." \
       --retries 3 --fragment-retries 3 -o raw/yt.%(ext)s "<URL>"

# 方案 3：互联网档案馆快照（公开页最稳的兜底）
curl -L --max-time 30 -o raw/wayback.html "https://web.archive.org/web/0/<URL>"
#   也可在浏览器手动查看：web.archive.org/web/<URL>

# 方案 4：readability 提取（抓回的 HTML 转干净正文）
trafilatura -i raw/page.html -o raw/page.txt
#   或 readability-lxml：python -c "from readability import read; ..."
```

### ③ B/D 类失败（反爬/登录/JS-only）—— 不重试

- 不调任何重试；
- 提示用户在浏览器导出（HTML / 另存为 / Markdown）；
- 或导出 PDF/截图后走本地文件输入（OCR/竖排路径）；
- 若用户能登录该站 → 让其手动复制正文粘贴进对话。

### ④ C 类失败（沙箱序列化故障）—— 立刻停手 + Bug Report

- **不要重试**——C 类对所有后续调用同样表现，重试只浪费用户时间；
- 文字模板：**「沙箱侧工具调用通道故障（参数 url/command 整层丢失），非本工厂可修复。请尝试：① 重启会话 ② 检查沙箱代理/MCP 配置 ③ 换工具集。如反复出现请向宿主/Bug Report。」**
- 同时把 `source_media.note` 标 `channel_fault`，便于事后筛选失败样本与统计故障频次。

### ⑤ 失败来源标注（在 SKILL.md 第 1 步的 source_media 桶）

```json
{
  "id": "m-3",
  "type": "url",
  "uri": "https://example.com/foo",
  "note": "via_curl"   // 或 "via_wayback" / "platform_video" / "vertical_text" / "channel_fault" / "wechat_mp_blocked"
}
```

——便于再蒸馏与故障排查时按 `note` 字段过滤失败/备用来源样本。

## 5.6 微信公众号文章专门处置（B 类子型 · §17.1.1 配套命令清单）

> 配合 distillation-method §17.1.1 使用。公众号文章即使通道 100% 健康也几乎拿不到正文（JS 加密 + Referer + 限流 + 部分文章关注全文隐藏），下面是**用户自助导出 → 再喂工厂**的命令清单。

### ① 浏览器开发者工具抓包（最稳 · 拿原始 JSON）

```bash
# 用户侧步骤（让用户在浏览器里做）：
# 1. 登录 https://mp.weixin.qq.com 并打开文章页
# 2. F12 → Network 面板 → 筛选关键词：profile_ext / getmsg / appmsg
# 3. 点击该 XHR 请求 → Response 一栏复制完整 JSON 对象
# 4. 重点字段：JSON 内的 content（HTML 片段）/ title / author / publish_time
```

工厂侧拿到 JSON 后：

```bash
# 提取 content 字段单独成文件
python -c "import json,sys; d=json.load(open('mp.json','r',encoding='utf-8')); \
  open('mp_raw.html','w',encoding='utf-8').write(d.get('content') or d['data']['content'])"
# readability/trafilatura 提干净正文
trafilatura -i mp_raw.html -o mp_clean.txt
# 喂给第 1 步文本输入即可（source_media.type=local_clip, note=wechat_mp_blocked）
```

### ② 微信客户端分享导出（推荐 · 不依赖抓包）

```bash
# 用户侧步骤：
# 1. 手机微信打开文章 → 右上角 ··· → 分享
# 2. 选「印象笔记」（或「微信收藏」）
# 3. 印象笔记端导出为 .enex 或 .md；微信收藏端复制全文
# 4. 把 .md 文件或全文粘贴到对话或上传为本地附件
```

工厂侧：直接走第 1 步**本地文件输入**（MD/TXT）或**文本输入**粘贴格式，与常规来源抽取一致。

### ③ 直接粘贴正文（兜底）

```bash
# 用户选中全文 → 复制 → 在对话粘贴
# 工厂按文本输入处理；source_media.type=local_clip, note=wechat_mp_blocked
```

### ④ 来源标注 schema 示例

```json
{
  "id": "m-wx-1",
  "type": "local_clip",
  "uri": "https://mp.weixin.qq.com/s/xxxxxx",
  "note": "wechat_mp_blocked",   // 标记原始失败原因
  "captured_via": "browser_devtools_json",   // 或 "wechat_share" / "manual_paste"
  "collected_at": "2026-08-25T15:30+08:00"
}
```

### ⑤ 边界与提示

- **版权边界**：仅处理用户**已通过微信客户端打开过**的内容；不替用户绕过关注可见保护；
- **多篇批量**：每一篇都需用户单独抓/粘贴，工厂不自动循环抓包（避免触犯微信风控）；
- **与 C 类故障区分**：若用户反馈"连这条命令的输入参数都收不到"——那是 §5.5 ④ 的 C 类沙箱通道故障，与公众号无关，不要把 C 类 Bug Report 误推给 §5.6。

## 6. 产出落点

- 转录 / OCR / 图文块 → 第 2 步抽取的输入文本 + `source_media` 桶（type/uri/collected_at/video.timestamp/frame_id）
- 原始帧与转录缓存 → `references/memory/knowledge-grains/media-chunks/`（多次收集时版本化保留）
- 注意版权：仅处理用户有权使用的内容，蒸馏产物不保留整段音视频副本。
