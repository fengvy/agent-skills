#!/usr/bin/env python3
"""按端切片 PRD，供 audit_coverage.py 与 audit_unimplemented.py 共用。

约定（见 references/prd-output-template.md 第五章）：
- 第五章一个端一个 `#### 5.X <端名>` 分节，模块以 `#####` 挂在分节下；
- 第三章页面表用「端」列、第六章各表用「端 / 发起端 / 接收端」列标注所属端；
- 端名在全文逐字一致。

切片规则：
- 第一、二、四、八章整章保留（全局内容）；
- 第三、六、七、九章的表格只保留含该端名的数据行，表头与分隔行保留；
- 第五章只保留该端分节以及可选的「共用」分节；
- 含「共用」「全项目」的数据行在所有端视图中保留。
"""
import re

CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
          "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
GLOBAL_MARKS = ("共用", "全项目")
FILTERED_CHAPTERS = (3, 6, 7, 9)
CHAPTER_RE = re.compile(r"^#{1,6}\s+([一二三四五六七八九十]+)、")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


class SectionError(ValueError):
    pass


def _chapter(line):
    m = CHAPTER_RE.match(line)
    return CN_NUM.get(m.group(1)) if m else None


def _is_table_row(line):
    return line.lstrip().startswith("|")


def _is_separator(line):
    return bool(SEP_RE.match(line))


def end_sections(lines):
    """返回第五章的 `####` 分节标题列表，用于校验端名与报错。"""
    titles, chapter = [], 0
    for line in lines:
        h = HEADING_RE.match(line)
        if not h:
            continue
        ch = _chapter(line)
        if ch is not None:
            chapter = ch
        elif chapter == 5 and len(h.group(1)) == 4:
            titles.append(h.group(2).strip())
    return titles


def build_view(lines, end):
    """返回 [(原始行号, 行内容)]；end 不在任何分节标题中时抛 SectionError。"""
    titles = end_sections(lines)
    if not titles:
        raise SectionError(
            "第五章没有 `#### 5.X <端名>` 端分节，无法按端切片；"
            "请先按模板建端分节，或去掉 --section 跑全量"
        )
    if not any(end in t for t in titles):
        raise SectionError(
            f"第五章没有端「{end}」的分节；现有分节：{'、'.join(titles)}"
        )

    out, chapter, in_end, seen_section = [], 0, False, False
    for i, line in enumerate(lines):
        h = HEADING_RE.match(line)
        if h:
            ch = _chapter(line)
            if ch is not None:
                chapter, in_end, seen_section = ch, False, False
                out.append((i + 1, line))
                continue
            if chapter == 5 and len(h.group(1)) == 4:
                seen_section = True
                title = h.group(2)
                in_end = end in title or "共用" in title
                if in_end:
                    out.append((i + 1, line))
                continue
            if chapter == 5 and seen_section:
                if in_end:
                    out.append((i + 1, line))
                continue
            out.append((i + 1, line))
            continue
        if chapter == 5 and seen_section and not in_end:
            continue
        if chapter in FILTERED_CHAPTERS and _is_table_row(line):
            keep = (_is_separator(line) or end in line
                    or any(m in line for m in GLOBAL_MARKS))
            if not keep and i + 1 < len(lines) and _is_separator(lines[i + 1]):
                keep = True
            if not keep:
                continue
        out.append((i + 1, line))
    return out
