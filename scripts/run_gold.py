#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_gold.py — gold 验证运行器（确定性部分）

第 5 步「真验证与迭代闭环」的可运行脚手架：
  1. 读 gold.json（验证集，含 checkpoints 判定点）
  2. 读 results.json（实跑记录：每条 gold 的真实输出）
  3. 按 checkpoints 做格式化预筛判定（关键字/断言），生成 verify-report.md
  4. 升级回归验证：传 --regress 旧报告，对比通过率是否回退

注意：gold 判定涉及语义，本脚本只做「预筛」；最终判定由验证 Agent 人工/LLM 复核。
用法：
  python run_gold.py gold.json results.json verify-report.md
  python run_gold.py gold.json results.json verify-report.md --regress old-report.md
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def load_json(path: Path):
    if not path.exists():
        print(f"[ERROR] 找不到文件: {path}")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_contains(output: str, checkpoint: str) -> bool:
    """判定点命中：期望文本出现在输出中（大小写不敏感、去空白）。"""
    if not checkpoint:
        return True
    norm_out = "".join(output.split()).lower()
    norm_cp = "".join(checkpoint.split()).lower()
    return norm_cp in norm_out


def check_excludes(output: str, negative: str) -> bool:
    """否定判定点：期望文本绝不出现在输出中。"""
    if not negative:
        return True
    norm_out = "".join(output.split()).lower()
    norm_neg = "".join(negative.split()).lower()
    return norm_neg not in norm_out


def judge(gold: dict, output: str) -> dict:
    """四态判定：答对 / 部分答对 / 答错 / 答非所问。"""
    checkpoints = gold.get("checkpoints", [])
    negatives = gold.get("negative", [])  # gold 可选字段：绝不可出现的文本
    hits = sum(1 for cp in checkpoints if check_contains(output, cp))
    miss = [cp for cp in checkpoints if not check_contains(output, cp)]
    neg_hit = [ng for ng in negatives if not check_excludes(output, ng)]

    if neg_hit:
        verdict, reason = "答错", f"触犯否定断言: {neg_hit}"
    elif hits == len(checkpoints) and checkpoints:
        verdict, reason = "答对", ""
    elif hits > 0:
        verdict, reason = "部分答对", f"缺判定点: {miss}"
    elif not output.strip():
        verdict, reason = "答非所问", "空输出"
    else:
        verdict, reason = "答错", f"未命中任何判定点: {checkpoints}"
    return {"verdict": verdict, "reason": reason, "hit": hits, "total": len(checkpoints)}


def main():
    ap = argparse.ArgumentParser(description="gold 验证预筛与报告生成")
    ap.add_argument("gold", type=Path, help="gold.json 路径")
    ap.add_argument("results", type=Path, help="results.json 路径（[{id, output}]）")
    ap.add_argument("report", type=Path, help="输出 verify-report.md 路径")
    ap.add_argument("--regress", type=Path, default=None, help="旧报告路径（回归对比）")
    ap.add_argument("--weights", type=str, default="1.0:0.5", help="通过率权重 答对:部分答对，默认 1.0:0.5")
    args = ap.parse_args()

    golds = {g["id"]: g for g in load_json(args.gold)}
    results = load_json(args.results)
    full, partial = [float(x) for x in args.weights.split(":")]

    lines = ["# 验证报告（Verify Report）", ""]
    lines.append(f"> 生成时间：{datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"> 预筛脚本：scripts/run_gold.py（判定由验证 Agent 人工/LLM 复核）")
    lines.append("")

    rows, passed_score = [], 0.0
    for item in results:
        gid = item.get("id")
        gold = golds.get(gid)
        if not gold:
            print(f"[WARN] results 中有 gold 未定义的 id: {gid}")
            continue
        j = judge(gold, item.get("output", ""))
        score = full if j["verdict"] == "答对" else (partial if j["verdict"] == "部分答对" else 0.0)
        passed_score += score
        rows.append((gid, gold.get("path", ""), j["verdict"], j["reason"], score))
        lines.append(f"- `{gid}` {j['verdict']}（{score:.1f}）｜来源锚点 {gold.get('path','')}｜{j['reason'] or '通过'}")

    rate = passed_score / len(rows) if rows else 0.0
    lines.append("")
    lines.append(f"## 汇总")
    lines.append(f"- gold 总数：{len(rows)}")
    lines.append(f"- 通过率（答对×{full} + 部分×{partial}）：**{rate:.0%}**（门槛 ≥80%）")
    lines.append(f"- 失败明细：{'，'.join(f'{r[0]}({r[2]})' for r in rows if r[2] != '答对') or '无'}")

    if args.regress:
        old = args.regress.read_text(encoding="utf-8")
        # 从旧报告取通过率行做对比提示（预筛口径，供人工参考）
        lines.append("")
        lines.append(f"## 回归对比（升级验证）")
        lines.append(f"- 旧报告：{args.regress}；本次通过率 {rate:.0%}。")
        lines.append(f"- 判定：通过率 <90% 或低于旧基线 → 建议回滚上一版本（见 evolution-protocol.md 第 4 节）。")

    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] 报告已生成: {args.report}（通过率 {rate:.0%}）")


if __name__ == "__main__":
    main()
