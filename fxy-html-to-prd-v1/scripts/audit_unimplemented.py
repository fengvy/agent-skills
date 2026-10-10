#!/usr/bin/env python3
"""反向对账：核验文档里「未实现 / 未接线 / 死代码 / 占位 / 不生效」这类声明。

背景：覆盖率对账（audit_coverage.py）只查一个方向 —— 原型里有、文档没写（漏写）。
反方向同样危险：文档声称「某功能未实现」时，若判断有误，实施方会**主动跳过**一个
真实存在的功能。漏写是消极错误，误判是积极错误。

用法:
    python3 audit_unimplemented.py <原型.html> <PRD.md 或 实现规格.md> [--show-ok] [--claims-only]

## 设计要点：为什么不能只数「引用」

「未实现」在中文里是好几件不同的事，各自要查的证据维度不同：

| 声明写法            | 实际含义        | 该查的维度 |
| ----------------- | ------------- | -------- |
| 恒为空 / 不回写 / 未赋值 | 从不**写入**    | assign   |
| 未接线 / 无入口 / 未调用 | 从不**被调用**  | call     |
| 在 X 处未生效 / 渲染时未使用 | **特定位置**不生效 | 无法自动判定 |
| 未实现 / 不存在        | 从未出现        | total    |

只数「引用」会把「有引用但从不赋值」误判成"已实现" —— 本脚本开发途中
真实踩到过：`roleMenuSel` 被 renderNav 读取 2 次（引用>0），但从未被赋值，
「按角色隐藏菜单未生效」的声明完全正确。故按维度分开计数。

## 判定三态

    ✓ 一致      关注维度的计数为 0 —— 证据支持「未实现」的说法
    ⚠ 不一致    关注维度有计数，且声明是全局性的 —— 需回源码确认
    ？ 须人工判断 声明含位置限定词（"在…处/时"），或标识符过短（名字冲突风险）

**不做自动化结论**：脚本只把计数与上下文摆出来。⚠ 不等于判断错误
（可能是定义了但走不到的分支），？ 更不等于有问题 —— 都须回源码确认。
"""
import argparse
import re
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("prototype", help="原型 HTML 路径")
ap.add_argument("doc", help="PRD 或实现规格 Markdown 路径")
ap.add_argument("--show-ok", action="store_true", help="同时列出判定为一致的声明")
ap.add_argument("--claims-only", action="store_true", help="只列出声明行，不做核验")
a = ap.parse_args()

try:
    src = Path(a.prototype).read_text(encoding="utf-8", errors="replace")
except OSError as exc:
    sys.exit(f"读不到原型 {a.prototype}: {exc}")
try:
    doc_lines = Path(a.doc).read_text(encoding="utf-8").splitlines()
except OSError as exc:
    sys.exit(f"读不到文档 {a.doc}: {exc}")

CLAIM_KW = ["未实现", "未接线", "未生效", "不生效", "不回写", "未绑定", "无事件绑定",
            "占位", "死代码", "演示态", "未设计", "未提供", "未暴露", "未打通", "未落地"]

# 声明 → 关注维度。按"更具体"优先匹配。
DIM_RULES = [
    (r"恒为空|不回写|未赋值|从不写入|始终为空", "assign",
     "声明指向「从不写入」，核验维度 = 赋值次数"),
    (r"未接线|无入口|未调用|未绑定|未挂", "call",
     "声明指向「从无入口」，核验维度 = 调用次数"),
    (r"未生效|不生效|未实现|未落地|未打通", "total",
     "声明指向「未实现」，核验维度 = 任何使用"),
]
# 位置限定词 → 强制降级为"须人工判断"
LOC_RULES = r"在.{0,12}(处|时|中|里|内)|渲染时|该处|此处|仅.{0,6}时|H5.{0,6}渲染"


def pick_dim(text):
    for pat, dim, why in DIM_RULES:
        if re.search(pat, text):
            return dim, why
    return "total", "未识别具体维度，按任何使用核验"


def counts(name):
    """分维度计数：定义 / 赋值 / 调用 / 读取。"""
    wb = r"\b" + re.escape(name) + r"\b"
    total = len(re.findall(wb, src))
    d = (len(re.findall(r"function\s+" + wb + r"\s*\(", src))
         + len(re.findall(r"\b(?:var|let|const)\s+" + wb + r"\s*=", src)))
    # 赋值：NAME = 且前面不是 var/let/const 声明
    assign = len(re.findall(r"(?<![.\w])(?<!var )(?<!let )(?<!const )" + wb + r"\s*=(?!=)", src))
    # 属性赋值：.NAME = 或 ["NAME"] = 之类的写入
    assign += len(re.findall(r"\." + wb + r"\s*=(?!=)", src))
    call = len(re.findall(r"(?<!function\s)" + wb + r"\s*\(", src))
    read = max(0, total - d - assign - call)
    return {"def": d, "assign": assign, "call": call, "read": read, "total": total}


def context(name, n=2):
    wb = r"\b" + re.escape(name) + r"\b"
    out = []
    for m in re.finditer(wb, src):
        seg = src[max(0, m.start() - 50):m.start() + 50].replace("\n", " ")
        if re.search(r"function\s+" + wb, seg) or re.search(r"(?:var|let|const)\s+" + wb, seg):
            continue
        out.append(seg.strip())
        if len(out) >= n:
            break
    return out


def find_claims():
    out = []
    for i, line in enumerate(doc_lines, 1):
        if not any(k in line for k in CLAIM_KW):
            continue
        ids = [x for x in re.findall(r"`([A-Za-z_$][\w$]*)`", line) if len(x) >= 2]
        out.append((i, line.strip(), ids))
    return out


claims = find_claims()

if a.claims_only:
    print(f"共 {len(claims)} 条「未实现类」声明：\n")
    for ln, text, ids in claims:
        tag = "、".join(f"`{x}`" for x in ids) if ids else "（未指名标识符）"
        print(f"  L{ln:<5} {tag}")
    sys.exit(0)

print(f"文档: {a.doc}")
print(f"原型: {a.prototype}  ({len(src)} 字符)")
print(f"\n共 {len(claims)} 条「未实现类」声明\n")

ok, bad, manual = [], [], []

for ln, text, ids in claims:
    if not ids:
        manual.append((ln, text, "未指名标识符", None))
        continue
    dim, why = pick_dim(text)
    loc_limited = bool(re.search(LOC_RULES, text))
    for ident in ids:
        c = counts(ident)
        focus = c[dim]
        if loc_limited:
            manual.append((ln, text, f"声明含位置限定词（{why}）", ident))
        elif len(ident) <= 2:
            manual.append((ln, text, f"标识符仅 {len(ident)} 字符，名字冲突风险高", ident))
        elif focus == 0:
            ok.append((ln, ident, dim, c, why))
        else:
            bad.append((ln, ident, dim, c, text))

print("=" * 74)
print(f"一、⚠ 不一致：{len(bad)} 处（关注维度有计数，声明可能是全局性误判）")
print("=" * 74)
if not bad:
    print("  无 —— 未见全局性误判。")
for ln, ident, dim, c, text in bad:
    print(f"\n  L{ln}  `{ident}`  核验维度={dim}  →  {dim} 计数 = {c[dim]}")
    print(f"    证据: 定义 {c['def']} / 赋值 {c['assign']} / 调用 {c['call']} / 读取 {c['read']}")
    print(f"    声明: {text[:94]}")
    for x in context(ident):
        print(f"    上下文: …{x}…")

print()
print("=" * 74)
print(f"二、？ 须人工判断：{len(manual)} 处")
print("=" * 74)
print("  原因分两类：① 声明含位置限定词（脚本无法判断「某处」是哪处）")
print("              ② 未指名标识符（声明关于 UI 行为，非代码符号）")
print("              ③ 标识符过短，与其他同名符号冲突风险高")
for ln, text, reason, ident in manual:
    tag = f"`{ident}`  " if ident else ""
    print(f"  L{ln:<5} {tag}{reason}")
    print(f"          {text[:92]}")

if a.show_ok:
    print()
    print("=" * 74)
    print(f"三、✓ 一致：{len(ok)} 处（关注维度计数为 0，证据支持声明）")
    print("=" * 74)
    for ln, ident, dim, c, why in ok:
        print(f"  L{ln}  `{ident}`  {dim}=0（定义 {c['def']} / 读取 {c['read']}）")
        print(f"          {why}")

print()
print(f"小结：{len(ok)} 一致 / {len(bad)} 不一致 / {len(manual)} 须人工判断")
print("注意：⚠ 不等于声明错误 —— 可能是定义了但走不到的分支。")
print("      须用 dump_prototype_js.py 回源码确认后再改结论。")
sys.exit(0)
