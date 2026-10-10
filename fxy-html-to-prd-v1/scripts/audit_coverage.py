#!/usr/bin/env python3
"""交互入口覆盖率对账：把原型里所有可点击入口的「用户可见文案」抽出来，
逐个检查是否出现在已写好的 PRD 里，输出未覆盖清单。

用途：PRD 交付前自查「功能点有没有遗漏」。原型里每个 onclick 都是一个功能入口，
凡是文案在 PRD 里找不到的，要么是真遗漏，要么只是没引按钮原文 —— 逐条判定即可。

用法:
    python3 audit_coverage.py <原型.html> <PRD.md> [--min-len N] [--show-covered]

输出:
    总数 / 已覆盖 / 未覆盖，随后列出未覆盖清单（文案 + 触发它的处理器函数名）。
    处理器名可用于回原型定位该入口的实现，判断是真遗漏还是仅文案未引。

说明:
    - 自动过滤 JS 模板拼接产生的噪声文案（含 `+`、`;`、`{`、`}` 等拼接痕迹的）。
    - 比对时剥离文案前缀的图标与符号（＋ ✎ 🗑 📱 ← → ↑ ↓ ✔ 🔒 🤖 等）。
    - 判定为「覆盖」的阈值是文案前 6 个字符命中（避免因标点/后缀差异漏判）。
"""
import argparse
import re
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("prototype", help="原型 HTML 路径")
ap.add_argument("prd", help="已写好的 PRD Markdown 路径")
ap.add_argument("--min-len", type=int, default=2, help="文案最短长度（默认 2，过滤单字符噪声）")
ap.add_argument("--show-covered", action="store_true", help="同时列出已覆盖项")
a = ap.parse_args()

try:
    src = Path(a.prototype).read_text(encoding="utf-8", errors="replace")
except OSError as exc:
    sys.exit(f"读不到原型 {a.prototype}: {exc}")
try:
    prd = Path(a.prd).read_text(encoding="utf-8")
except OSError as exc:
    sys.exit(f"读不到 PRD {a.prd}: {exc}")

PREFIX = r"^[＋+✎🗑📱⟳←→↑↓✔🔒🤖📄✨·\-\s]+"

# 两种 onclick 写法：原生属性 onclick="..."  与  JS 字符串内 onclick=\'...\'
pairs = []
for m in re.finditer(r'onclick="([^"]{0,120})"[^>]*>([^<]{1,60})', src):
    pairs.append((m.group(1), m.group(2).strip()))
for m in re.finditer(r"onclick=\\'([^\\']{0,120})\\'[^>]*>([^<]{1,60})", src):
    pairs.append((m.group(1), m.group(2).strip()))

# 去重 + 过滤模板拼接噪声
seen, uniq = set(), []
for h, label in pairs:
    if not label or (h, label) in seen:
        continue
    seen.add((h, label))
    if any(c in label for c in ["+'", "';", '"+', "{", "}", "()"]):
        continue
    if len(label) < a.min_len:
        continue
    uniq.append((h, label))

covered, missing = [], []
for h, label in uniq:
    probe = re.sub(PREFIX, "", label).strip().replace("\\", "")
    if not probe:
        continue
    (covered if probe[:6] in prd else missing).append((label, h))

total = len(covered) + len(missing)
print(f"交互入口（已滤模板噪声）: {total} 个")
if total:
    print(f"  PRD 已覆盖 : {len(covered)}  ({len(covered) / total * 100:.0f}%)")
    print(f"  未覆盖     : {len(missing)}\n")

if missing:
    print("未覆盖清单（逐条判定：真遗漏 / 仅未引按钮原文）")
    print("-" * 68)
    for label, h in missing:
        print(f"  文案「{label[:28]:<28}」 ← {h[:36]}")
    print(
        "\n判定提示：处理器名可用 `dump_prototype_js.py fn <函数名>` 回查实现，"
        "确认该入口的行为是否已在 PRD 中描述。"
    )
if a.show_covered:
    print("\n已覆盖清单：")
    for label, h in covered:
        print(f"  ✓ {label[:28]:<28} ← {h[:36]}")

sys.exit(0)
