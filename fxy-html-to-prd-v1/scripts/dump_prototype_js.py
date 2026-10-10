#!/usr/bin/env python3
"""从原型 HTML 抽取 JS 函数体 / 变量赋值 / 原始行区间，按固定宽度折行输出。

原型 HTML 常为 200-400KB、单行超长（>2000 字符），直接阅读会被工具截断。
本脚本按花括号配对抽出完整函数体，并按 --width 折行，便于逐段阅读。

用法:
    python3 dump.py list                         列出全部函数名（含体量字符数）
    python3 dump.py fn <name> [<name> ...]        输出函数体
    python3 dump.py var <name> [<name> ...]       输出 "var <name> =" 赋值块
    python3 dump.py lines <start> <end>           输出原始行区间

选项:
    --file PATH    原型 HTML 路径（省略时自动使用当前目录下唯一的 .html）
    --width N      折行宽度（默认 180，0 表示不折行）
    --grep PAT     从输出中只保留含 PAT 的行（大小写不敏感）
"""
import argparse
import re
import sys
from pathlib import Path

ap = argparse.ArgumentParser(add_help=True)
ap.add_argument("mode", nargs="?", help="list | fn | var | lines")
ap.add_argument("args", nargs="*", help="函数名 / 变量名 / 行号")
ap.add_argument("--file", default=None, help="原型 HTML 路径（省略时自动取当前目录下唯一的 .html）")
ap.add_argument("--width", type=int, default=180)
ap.add_argument("--grep", default=None)
a = ap.parse_args()

# 未指定 --file 时自动发现当前目录下唯一的 .html，避免绑定某个具体项目
if not a.file:
    cands = sorted(Path.cwd().glob("*.html"))
    if len(cands) == 1:
        a.file = str(cands[0])
    elif not cands:
        sys.exit("当前目录下没有 .html 文件。请用 --file <路径> 指定原型。")
    else:
        sys.exit(
            "当前目录下有多个 .html，请用 --file 指定其一：\n  "
            + "\n  ".join(str(c) for c in cands)
        )


try:
    src = open(a.file, encoding="utf-8", errors="replace").read()
except OSError as exc:
    sys.exit(f"读不到文件 {a.file}: {exc}")


def wrap(text: str) -> str:
    if not a.width:
        return text
    out = []
    for ln in text.splitlines():
        while len(ln) > a.width:
            out.append(ln[:a.width])
            ln = ln[a.width:]
        out.append(ln)
    return "\n".join(out)


def find_func(name: str):
    """返回 (start, end, body)。end 为闭括号后一位。"""
    m = re.search(r"\bfunction\s+" + re.escape(name) + r"\s*\([^)]*\)\s*\{", src)
    if not m:
        return None
    i, depth = m.end() - 1, 0
    while i < len(src):
        c = src[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return m.start(), i + 1, src[m.start():i + 1]
        i += 1
    return m.start(), len(src), src[m.start():]


def find_var(name: str):
    """从 'var NAME =' 起到下一个顶层 var/function/注释块之前。"""
    m = re.search(r"\bvar\s+" + re.escape(name) + r"\s*=", src)
    if not m:
        return None
    nxt = re.search(r"\n(?:var\s+\w+\s*=|function\s+\w+\s*\(|/\* )", src[m.end():])
    end = m.end() + nxt.start() if nxt else len(src)
    return m.start(), end, src[m.start():end].rstrip()


def emit(title: str, body: str):
    if a.grep and not re.search(a.grep, body, re.I):
        return
    print(f"\n{'=' * 72}\n### {title}   [{len(body)} 字符]\n{'=' * 72}")
    print(wrap(body))


if a.mode == "list":
    names = sorted(set(re.findall(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(", src)))
    print(f"{len(names)} 个函数（按体量降序）")
    rows = [(n, find_func(n)) for n in names]
    for n, f in sorted(rows, key=lambda x: -(len(x[1][2]) if x[1] else 0)):
        print(f"{n:<28}{len(f[2]) if f else 0:>7}")
elif a.mode == "fn":
    for n in a.args:
        f = find_func(n)
        emit(f"function {n}", f[2]) if f else print(f"[未找到] {n}")
elif a.mode == "var":
    for n in a.args:
        v = find_var(n)
        emit(f"var {n}", v[2]) if v else print(f"[未找到] var {n}")
elif a.mode == "lines":
    s, e = int(a.args[0]), int(a.args[1])
    lines = src.splitlines()
    emit(f"lines {s}-{e}", "\n".join(lines[s - 1:e]))
else:
    ap.print_help()
