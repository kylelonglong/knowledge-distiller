#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dedup_frames.py — 关键帧三级去重（媒体摄入协议 · 第17节）

判定规则（与协议一致）：
  1. dHash 感知哈希（视觉相似度）——Hamming 距离 < 阈值 → 视觉相近
  2. 灰度直方图差异（颜色分布突变）
  3. OCR 文本差异（可选，需外部 OCR 命令）——画面相同但文字变了 → 判新帧

判定结论：视觉相近 + 文本相同 → 去重；视觉相近但文本不同 → 保留。

依赖：Pillow（pip install pillow）。OCR 为可选通道，未装配时自动跳过第 3 级。

用法：
  python dedup_frames.py --frames-dir ./frames --out keep_list.txt \
      --hash-threshold 6 --hist-threshold 0.05 \
      --ocr-cmd "tesseract {path} stdout -l chi_sim"
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def dhash(img, size=8):
    """感知哈希：缩小 → 灰度 → 相邻像素比较 → 位串。"""
    gray = img.convert("L").resize((size + 1, size), img.LANCZOS)
    bits = []
    for y in range(size):
        for x in range(size):
            bits.append(1 if gray.getpixel((x, y)) > gray.getpixel((x + 1, y)) else 0)
    return bits


def hamming(a, b):
    return sum(1 for x, y in zip(a, b) if x != y)


def hist_diff(img_a, img_b, buckets=32):
    """归一化灰度直方图差异（0=完全相同，1=完全不同）。"""
    ha = img_a.convert("L").resize((64, 64)).histogram()
    hb = img_b.convert("L").resize((64, 64)).histogram()
    ha = [v / 4096 for v in ha]
    hb = [v / 4096 for v in hb]
    return sum(abs(a - b) for a, b in zip(ha, hb)) / 2


def ocr_text(path: str, cmd: str) -> str:
    """调用外部 OCR 命令（如 tesseract），返回归一化文本。失败返回空串。"""
    try:
        out = subprocess.run(
            cmd.format(path=path), shell=True, capture_output=True, text=True, timeout=60
        )
        return "".join(out.stdout.split()) if out.returncode == 0 else ""
    except Exception:
        return ""


def load_image(path):
    try:
        from PIL import Image
        return Image.open(path)
    except ImportError:
        print("[ERROR] 需要 Pillow：pip install pillow")
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description="关键帧三级去重")
    ap.add_argument("--frames-dir", required=True, help="帧图片目录（frame_*.jpg）")
    ap.add_argument("--out", default="keep_list.txt", help="输出保留帧清单")
    ap.add_argument("--hash-threshold", type=int, default=6, help="dHash Hamming 阈值（越小越严）")
    ap.add_argument("--hist-threshold", type=float, default=0.05, help="直方图差异阈值")
    ap.add_argument("--ocr-cmd", default="", help="OCR 命令模板，含 {path}；留空跳过第3级")
    args = ap.parse_args()

    frames = sorted(
        [p for p in Path(args.frames_dir).iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}],
        key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)) if re.search(r"(\d+)", p.stem) else 0,
    )
    if not frames:
        print("[ERROR] 帧目录为空")
        sys.exit(1)

    keep, dropped, prev_hash, prev_ocr = [], [], None, ""
    for i, path in enumerate(frames):
        img = load_image(str(path))
        h = dhash(img)
        if prev_hash is None:
            keep.append(path.name)
        else:
            visual_similar = hamming(prev_hash, h) <= args.hash_threshold
            hist_similar = hist_diff(prev_img, img) <= args.hist_threshold
            if args.ocr_cmd:
                cur_ocr = ocr_text(str(path), args.ocr_cmd)
                text_same = (cur_ocr == prev_ocr)
            else:
                cur_ocr, text_same = "", True  # 未装配 OCR 时按文本相同处理
            if visual_similar and hist_similar and text_same:
                dropped.append(path.name)
            else:
                keep.append(path.name)
            prev_ocr = cur_ocr
        prev_hash, prev_img = h, img

    Path(args.out).write_text("\n".join(keep), encoding="utf-8")
    print(f"[OK] 输入 {len(frames)} 帧 → 保留 {len(keep)}，去重 {len(dropped)}")
    if dropped:
        print(f"[INFO] 已去重: {', '.join(dropped[:10])}{' …' if len(dropped) > 10 else ''}")
    print(f"[INFO] 保留清单: {args.out}")


if __name__ == "__main__":
    main()
