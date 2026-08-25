#!/usr/bin/env python3
"""
ocr_layout.py — 竖排文字感知的 OCR 结果重排器

背景：OCR 引擎（PaddleOCR / rapidocr / tesseract）默认按「横排从左到右」假设输出
文本顺序。竖排中文（古籍 / 竖版标题 / 对联 / 日式排版：文字从上到下、列从右到左）
会被读成乱序或逐字散列。

本脚本对 OCR 输出的「文本块 + 边框坐标」做几何分析并重组：
  1) 竖排检测（auto）：窄块（宽 ≤ 高 × 0.7）占比 ≥ 阈值 → 判为竖排页面
  2) 按列聚类：x 中心相近的块聚为一列（列宽容差自适应，可 --col-tol 覆盖）
  3) 列内排序：按 y 从上到下
  4) 列序输出：默认从右到左（中文传统竖排 rtl），可 --column-order ltr 左起

输入（JSON，stdin 或 --input）：
  [
    {"box": [x1, y1, x2, y2], "text": "春", "conf": 0.98},
    {"box": [[x,y],[x,y],[x,y],[x,y]], "text": "眠"},   # 四点框亦可
    ["box", "text", conf]                                 # 行式亦可（PaddleOCR 风格）
  ]
  或 {"result": [...], ...}（兼容包一层 result/data 的对象）。

用法：
  python scripts/ocr_layout.py --input ocr.json
  cat ocr.json | python scripts/ocr_layout.py
  python scripts/ocr_layout.py --input ocr.json --mode vertical --column-order rtl --mark-columns

横排输入时（auto 判定为横排）也做一次「按 y 分行、行内 x 排序」的阅读顺序整理，
保证顺序稳定；--mode horizontal 则原样逐块输出。

退出码：0 正常；2 输入错误。
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys

# 竖排判定：窄块（宽 ≤ 高 × NARROW_RATIO）占比 ≥ VERTICAL_THRESHOLD → 竖排
NARROW_RATIO = 0.7
VERTICAL_THRESHOLD = 0.5
# 列聚类容差默认系数（中位块宽 × 系数）
COL_TOL_FACTOR = 0.6
# 分行容差默认系数（中位块高 × 系数）
ROW_TOL_FACTOR = 0.6


def box_xy(box):
    """归一化边框为 (x1, y1, x2, y2)。"""
    if len(box) == 4 and all(isinstance(v, (int, float)) for v in box):
        return float(box[0]), float(box[1]), float(box[2]), float(box[3])
    if len(box) == 4 and all(isinstance(p, (list, tuple)) and len(p) >= 2 for p in box):
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        return float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))
    return None


def normalize(rows):
    """把各种 OCR 输出格式统一为 [{"box":(x1,y1,x2,y2),"text":str,"conf":float}]。"""
    boxes = []
    for r in rows:
        if isinstance(r, dict):
            box = r.get("box") or r.get("points") or r.get("bbox")
            text = r.get("text") or r.get("txt") or r.get("transcription") or ""
            conf = r.get("conf", r.get("confidence", 0.0)) or 0.0
        elif isinstance(r, (list, tuple)) and len(r) >= 2:
            box, text = r[0], r[1]
            conf = r[2] if len(r) > 2 and isinstance(r[2], (int, float)) else 0.0
        else:
            continue
        if not text or not box:
            continue
        xy = box_xy(box)
        if xy is None:
            continue
        boxes.append({"box": xy, "text": str(text).strip(), "conf": float(conf or 0.0)})
    return [b for b in boxes if b["text"]]


def detect_vertical(boxes):
    if not boxes:
        return False
    narrow = 0
    for b in boxes:
        x1, y1, x2, y2 = b["box"]
        w, h = x2 - x1, y2 - y1
        if h > 0 and w <= h * NARROW_RATIO:
            narrow += 1
    return narrow / len(boxes) >= VERTICAL_THRESHOLD


def cluster_columns(boxes, col_tol=None):
    """按 x 中心把块聚类成列；列内按 y 升序。返回列列表。"""
    if not boxes:
        return []
    widths = [b["box"][2] - b["box"][0] for b in boxes]
    tol = col_tol if col_tol is not None else max(statistics.median(widths) * COL_TOL_FACTOR, 2.0)
    items = sorted(boxes, key=lambda b: ((b["box"][0] + b["box"][2]) / 2, (b["box"][1] + b["box"][3]) / 2))
    columns = []
    for it in items:
        cx = (it["box"][0] + it["box"][2]) / 2
        placed = False
        for col in columns:
            col_cx = sum((b["box"][0] + b["box"][2]) / 2 for b in col) / len(col)
            if abs(col_cx - cx) <= tol:
                col.append(it)
                placed = True
                break
        if not placed:
            columns.append([it])
    for col in columns:
        col.sort(key=lambda b: (b["box"][1] + b["box"][3]) / 2)
    return columns


def reassemble_vertical(boxes, column_order="rtl", col_tol=None, mark_columns=False):
    columns = cluster_columns(boxes, col_tol)
    key = lambda col: sum((b["box"][0] + b["box"][2]) / 2 for b in col) / len(col)
    columns = sorted(columns, key=key, reverse=(column_order == "rtl"))
    lines = []
    for i, col in enumerate(columns, 1):
        text = "".join(b["text"] for b in col)
        lines.append(f"[列{i}] {text}" if mark_columns else text)
    return "\n".join(lines)


def reassemble_horizontal(boxes, row_tol=None):
    """横排阅读顺序：按 y 中心分行，行内按 x 升序。"""
    if not boxes:
        return ""
    heights = [b["box"][3] - b["box"][1] for b in boxes]
    tol = row_tol if row_tol is not None else max(statistics.median(heights) * ROW_TOL_FACTOR, 2.0)
    items = sorted(boxes, key=lambda b: ((b["box"][1] + b["box"][3]) / 2, (b["box"][0] + b["box"][2]) / 2))
    rows = []
    for it in items:
        cy = (it["box"][1] + it["box"][3]) / 2
        placed = False
        for row in rows:
            row_cy = sum((b["box"][1] + b["box"][3]) / 2 for b in row) / len(row)
            if abs(row_cy - cy) <= tol:
                row.append(it)
                placed = True
                break
        if not placed:
            rows.append([it])
    lines = []
    for row in rows:
        row.sort(key=lambda b: (b["box"][0] + b["box"][2]) / 2)
        lines.append("".join(b["text"] for b in row))
    return "\n".join(lines)


def load_rows(raw):
    data = json.loads(raw)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("result", "data", "results", "items"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def main():
    ap = argparse.ArgumentParser(description="竖排文字 OCR 结果重排器")
    ap.add_argument("--input", help="OCR JSON 文件（缺省读 stdin）")
    ap.add_argument("--mode", choices=["auto", "vertical", "horizontal"], default="auto",
                    help="auto=按几何检测竖排(默认); vertical=强制竖排重组; horizontal=按横排阅读顺序")
    ap.add_argument("--column-order", choices=["rtl", "ltr"], default="rtl",
                    help="竖排列序：rtl=右起(中文传统, 默认); ltr=左起")
    ap.add_argument("--col-tol", type=float, default=None, help="列聚类 x 容差（像素），默认自适应中位块宽×0.6")
    ap.add_argument("--mark-columns", action="store_true", help="输出带 [列N] 标记，便于人工核对")
    args = ap.parse_args()

    raw = sys.stdin.read() if not args.input else open(args.input, encoding="utf-8").read()
    try:
        rows = load_rows(raw)
    except json.JSONDecodeError as e:
        print(f"[ocr_layout] JSON 解析失败: {e}", file=sys.stderr)
        sys.exit(2)

    boxes = normalize(rows)
    if not boxes:
        print("[ocr_layout] 未提取到文本块（空输入）", file=sys.stderr)
        sys.exit(0)

    vertical = {"auto": detect_vertical(boxes), "vertical": True, "horizontal": False}[args.mode]
    if vertical:
        print(reassemble_vertical(boxes, args.column_order, args.col_tol, args.mark_columns))
    else:
        print(reassemble_horizontal(boxes))


if __name__ == "__main__":
    main()
