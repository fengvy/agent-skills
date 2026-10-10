#!/usr/bin/env python3
"""从原型 HTML 提取可见文本与交互元素索引，辅助 PRD 反推。

用法:
    python3 extract_prototype_ui.py <原型.html> [<原型2.html> ...]
    python3 extract_prototype_ui.py <原型.html> --plain-only   # 只输出正文文本
    python3 extract_prototype_ui.py <原型.html> --no-dedupe    # 不合并相邻重复行

输出按文档顺序:
    [h1]..[h6]  标题        [btn] 按钮       [link] 链接
    [th] 表格列头            [input] [select] [option] [textarea] 控件文本
    [input:placeholder] 等  控件无文本时的 placeholder/title 提示
    其余为正文可见文本

仅用 Python 标准库。输出为辅助索引，不能替代人工通读交互/JS 逻辑片段。
"""
import argparse
import re
import sys
from html.parser import HTMLParser

SKIP_TAGS = {"script", "style", "noscript", "svg", "template", "head"}
VOID_TAGS = {"input", "br", "img", "hr", "meta", "source", "wbr", "col"}
LABEL = {"h1": "h1", "h2": "h2", "h3": "h3", "h4": "h4", "h5": "h5", "h6": "h6",
         "a": "link", "button": "btn", "th": "th", "input": "input",
         "select": "select", "option": "option", "textarea": "textarea"}
ATTR_HINTS = ("placeholder", "title", "aria-label")


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.stack = []   # 打开的标题/控件栈: [label, has_text, attrs]
        self.lines = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if tag in LABEL:
            attrs = dict(attrs)
            label = "btn" if (tag == "a" and "btn" in attrs.get("class", "").split()) else LABEL[tag]
            self.stack.append([tag, label, False, attrs])  # [真实标签, 显示名, 是否含文本, 属性]
            if tag in VOID_TAGS:  # void 元素无 endtag,立即弹栈并输出属性提示
                self.handle_endtag(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            if self.skip_depth:
                self.skip_depth -= 1
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:  # 始终按真实标签弹栈
                entry = self.stack.pop(i)
                break
        else:
            return
        _, label, has_text, attrs = entry
        if not has_text:  # 无文本控件:取提示属性
            for key in ATTR_HINTS:
                val = clean(attrs.get(key, ""))
                if val:
                    self.lines.append(f"[{label}:{key}] {val}")
                    return

    def handle_data(self, data):
        if self.skip_depth:
            return
        text = clean(data)
        if not text:
            return
        if self.stack:
            _, label, _, _ = self.stack[-1]
            self.stack[-1][2] = True
            self.lines.append(f"[{label}] {text}")
        else:
            self.lines.append(text)


def main():
    ap = argparse.ArgumentParser(description="提取原型 HTML 可见文本与交互元素")
    ap.add_argument("files", nargs="+", help="原型 HTML 文件路径")
    ap.add_argument("--plain-only", action="store_true", help="只输出正文文本")
    ap.add_argument("--no-dedupe", action="store_true", help="不合并相邻重复行")
    args = ap.parse_args()

    for path in args.files:
        with open(path, encoding="utf-8", errors="replace") as fh:
            html = fh.read()
        if args.plain_only:
            text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", html, flags=re.I)
            text = re.sub(r"<[^>]+>", "\n", text)
            lines = [clean(ln) for ln in text.splitlines()]
        else:
            p = TextExtractor()
            try:
                p.feed(html)
            except Exception as exc:  # 解析异常不阻断
                print(f"# parse warning in {path}: {exc}", file=sys.stderr)
            lines = p.lines
        lines = [ln for ln in lines if ln]
        if not args.no_dedupe:
            lines = [ln for i, ln in enumerate(lines) if i == 0 or lines[i - 1] != ln]
        if len(args.files) > 1:
            print(f"\n===== {path} =====")
        sys.stdout.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
