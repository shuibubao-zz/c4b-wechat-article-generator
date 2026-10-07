#!/usr/bin/env python3
"""零依赖 Markdown 解析器（wechat-publisher 定制版）。

为什么要有它：starter kit 强依赖 `markdown` / `bs4` / `lxml` / `python-docx`，
装不上就整个技能废掉。而"装不上"并不罕见——离线机器、受限环境、
或者只是不想为一个转换脚本装四个包。

本模块用标准库把 Markdown 解析成统一的中间表示（IR），再由渲染器输出 HTML，
因此**零第三方依赖也能完成 md → 公众号 HTML 的全流程**。
有 `markdown` 库时走库路径，两条路径产出的 IR 结构一致（selftest 里有等价性断言）。

IR 节点（dict）：
  heading  {level, text}
  para     {text}
  code     {text, lang}
  quote    {kind, title, blocks:[...]}
  list     {ordered, items:[{text, children}]}
  table    {header:[], align:[], rows:[[]]}
  hr       {}
"""

from __future__ import annotations

import re
from html import escape as _esc

# ------------------------------------------------------------------ inline
_TOKEN = re.compile(
    r"""
      (?P<code>`+)(?P<codebody>[^`]+?)(?P=code)
    | !\[(?P<ialt>[^\]]*)\]\((?P<isrc>[^)\s]+)\)
    | \[(?P<ltext>[^\]]*)\]\((?P<lsrc>[^)\s]+)\)
    | \*\*(?P<bbody>.+?)\*\*
    | __(?P<bbody2>.+?)__
    | ~~(?P<dbody>.+?)~~
    | ==(?P<mbody>.+?)==
    | \*(?P<ebody>[^*\n]+)\*
    | (?<![\w])_(?P<ebody2>[^_\n]+)_(?![\w])
    | \$\$(?P<dmath>.+?)\$\$
    | \$(?P<imath>[^$\n]+?)\$
    """,
    re.X,
)

# 数学公式开关与告警收集（由 convert_to_wechat 按 --math 设置）
MATH_ENABLED = True
MATH_WARNS: list[str] = []


def _math_html(tex: str, display: bool, theme: dict[str, str]) -> str:
    """公式 → <img>：有 matplotlib 时渲染成 PNG，否则降级为等宽文本并告警。"""
    if not MATH_ENABLED:
        return _esc(("$$" if display else "$") + tex + ("$$" if display else "$"), quote=False)
    import math_render as MR

    uri = MR.render(tex, display=display)
    dollar = ("$$" if display else "$") + tex + ("$$" if display else "$")
    if uri is None:
        MATH_WARNS.append(tex[:40])
        return (f'<span style="font-family: Consolas, Menlo, monospace; '
                f'color: #c7254e;">{_esc(dollar, quote=False)}</span>')
    if display:
        return (f'<span style="display:block; text-align:center; margin:14px 0;">'
                f'<img src="{uri}" style="max-width:100%;" /></span>')
    return (f'<img src="{uri}" style="max-width:100%; '
            f'vertical-align:middle; margin:0 2px;" />')


def _plain(text: str, theme: dict[str, str], typo) -> str:
    if not text:
        return ""
    if typo:
        text = typo(text)
    return _esc(text, quote=False)


def render_inline(text: str, theme: dict[str, str], typo=None) -> str:
    """把一段内联 Markdown 渲染成 WeChat 安全的 HTML 片段。"""
    out: list[str] = []
    pos = 0
    for m in _TOKEN.finditer(text):
        out.append(_plain(text[pos : m.start()], theme, typo))
        if m.group("code"):
            body = m.group("codebody")
            out.append(f'<span style="{theme["code_inline"]}">{_esc(body, quote=False)}</span>')
        elif m.group("isrc"):
            src = m.group("isrc")
            alt = _esc(m.group("ialt") or "", quote=True)
            out.append(f'<img src="{_esc(src, quote=True)}" alt="{alt}" style="{theme["img"]}" />')
        elif m.group("lsrc"):
            inner = render_inline(m.group("ltext"), theme, typo)
            src = _esc(m.group("lsrc"), quote=True)
            out.append(f'<a href="{src}" style="{theme["a"]}">{inner}</a>')
        elif m.group("bbody") or m.group("bbody2"):
            inner = render_inline(m.group("bbody") or m.group("bbody2"), theme, typo)
            out.append(f'<span style="{theme["strong"]}">{inner}</span>')
        elif m.group("dbody"):
            inner = render_inline(m.group("dbody").strip(), theme, typo)
            out.append(f'<span style="{theme["del"]}">{inner}</span>')
        elif m.group("mbody"):
            inner = render_inline(m.group("mbody").strip(), theme, typo)
            out.append(f'<span style="{theme["mark"]}">{inner}</span>')
        elif m.group("ebody") or m.group("ebody2"):
            inner = render_inline(m.group("ebody") or m.group("ebody2"), theme, typo)
            out.append(f'<span style="{theme["em"]}">{inner}</span>')
        elif m.group("dmath") or m.group("imath"):
            out.append(_math_html(m.group("dmath") or m.group("imath"),
                                  bool(m.group("dmath")), theme))
        pos = m.end()
    out.append(_plain(text[pos:], theme, typo))
    return "".join(out)


# ------------------------------------------------------------------ blocks
_RE_FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")
_RE_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
_RE_HR = re.compile(r"^\s{0,3}(-{3,}|\*{3,}|_{3,})\s*$")
_RE_ULI = re.compile(r"^(\s*)[-*+]\s+(.*)$")
_RE_OLI = re.compile(r"^(\s*)\d+[.)]\s+(.*)$")
_RE_QUOTE = re.compile(r"^\s{0,3}>\s?(.*)$")
_RE_CALLOUT_FENCE = re.compile(r"^\s{0,3}:::\s*([A-Za-z\u4e00-\u9fff]*)\s*(.*)$")
_RE_CALLOUT_MARK = re.compile(r"^\[!([A-Za-z\u4e00-\u9fff]+)\]\s*(.*)$")
_RE_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def _indent_of(line: str) -> int:
    expanded = line.replace("\t", "  ")
    return len(expanded) - len(expanded.lstrip(" "))


def parse_front_matter(lines: list[str]) -> tuple[dict[str, str], list[str]]:
    """解析文件开头的 YAML-lite front-matter（只支持 key: value，不引第三方 YAML）。"""
    meta: dict[str, str] = {}
    if not lines or lines[0].strip() != "---":
        return meta, lines
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            end = i
            break
    if end is None:
        return meta, lines
    for raw in lines[1:end]:
        if ":" not in raw:
            continue
        k, v = raw.split(":", 1)
        v = v.strip().strip('"').strip("'")
        if v:
            meta[k.strip().lower()] = v
    return meta, lines[end + 1 :]


def _build_list_items(raw: list[tuple[int, str]], ordered: bool) -> list[dict]:
    """把 (缩进, 文本) 序列递归成嵌套列表。

    子列表包装成完整的 list 节点（而不是裸列表），这样 IR 只有一种节点类型，
    渲染器/统计器/签名函数都不需要为"列表里的列表"写特例。
    """
    idx = 0

    def build(base: int) -> list[dict]:
        nonlocal idx
        items: list[dict] = []
        while idx < len(raw):
            ind, txt = raw[idx]
            if ind < base:
                break
            if ind > base:
                child = {"type": "list", "ordered": ordered, "items": build(ind)}
                if items:
                    items[-1]["children"] = child
                else:
                    items.append({"text": "", "children": child})
                continue
            idx += 1
            items.append({"text": txt, "children": None})
        return items

    return build(raw[0][0]) if raw else []


def parse_markdown(text: str) -> tuple[dict[str, str], list[dict]]:
    """Markdown → (front-matter, IR blocks)。"""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    meta, lines = parse_front_matter(lines)
    blocks: list[dict] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # 空行
        if not line.strip():
            i += 1
            continue

        # 围栏代码块
        fm = _RE_FENCE.match(line)
        if fm:
            fence, lang = fm.group(1), fm.group(2)
            i += 1
            buf: list[str] = []
            while i < n and not lines[i].strip().startswith(fence[0] * 3):
                buf.append(lines[i])
                i += 1
            i += 1  # 跳过闭合围栏
            blocks.append({"type": "code", "text": "\n".join(buf), "lang": lang})
            continue

        # ::: callout 围栏
        cm = _RE_CALLOUT_FENCE.match(line)
        if cm:
            kind, title = cm.group(1), cm.group(2).strip()
            i += 1
            buf = []
            while i < n and lines[i].strip() != ":::":
                buf.append(lines[i])
                i += 1
            i += 1
            _m, inner = parse_markdown("\n".join(buf))
            blocks.append({"type": "quote", "kind": kind or "note", "title": title, "blocks": inner})
            continue

        # 标题
        hm = _RE_HEADING.match(line)
        if hm:
            blocks.append({"type": "heading", "level": len(hm.group(1)), "text": hm.group(2)})
            i += 1
            continue

        # 分隔线（front-matter 已剥离，此处 --- 即 hr）
        if _RE_HR.match(line):
            blocks.append({"type": "hr"})
            i += 1
            continue

        # 引用 / callout（> [!NOTE]）
        if _RE_QUOTE.match(line):
            buf = []
            while i < n and _RE_QUOTE.match(lines[i]):
                buf.append(_RE_QUOTE.match(lines[i]).group(1))
                i += 1
            kind, title = None, None
            first = buf[0].strip() if buf else ""
            mk = _RE_CALLOUT_MARK.match(first)
            if mk:
                kind = mk.group(1)
                title = mk.group(2).strip()
                buf = buf[1:]
            _m, inner = parse_markdown("\n".join(buf))
            blocks.append({"type": "quote", "kind": kind, "title": title, "blocks": inner})
            continue

        # 表格
        if "|" in line and i + 1 < n and _RE_TABLE_SEP.match(lines[i + 1]):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            align_raw = [c.strip() for c in lines[i + 1].strip().strip("|").split("|")]
            align = [
                "center" if c.startswith(":") and c.endswith(":")
                else "right" if c.endswith(":")
                else "left" if c.startswith(":")
                else ""
                for c in align_raw
            ]
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            blocks.append({"type": "table", "header": header, "align": align, "rows": rows})
            continue

        # 列表
        if _RE_ULI.match(line) or _RE_OLI.match(line):
            ordered = bool(_RE_OLI.match(line))
            raw: list[tuple[int, str]] = []
            while i < n and lines[i].strip():
                m1 = _RE_ULI.match(lines[i]) or _RE_OLI.match(lines[i])
                if m1:
                    raw.append((_indent_of(lines[i]), m1.group(2)))
                    i += 1
                elif _indent_of(lines[i]) >= 2 and raw:
                    # 续行：并入上一个 item
                    raw[-1] = (raw[-1][0], raw[-1][1] + "\n" + lines[i].strip())
                    i += 1
                else:
                    break
            blocks.append(
                {"type": "list", "ordered": ordered, "items": _build_list_items(raw, ordered)}
            )
            continue

        # 段落：直到空行或下一个块起始
        buf = []
        while i < n and lines[i].strip():
            nxt = lines[i]
            if (
                _RE_HEADING.match(nxt)
                or _RE_FENCE.match(nxt)
                or _RE_QUOTE.match(nxt)
                or _RE_CALLOUT_FENCE.match(nxt)
                or _RE_HR.match(nxt)
                or _RE_ULI.match(nxt)
                or _RE_OLI.match(nxt)
            ):
                break
            buf.append(nxt.strip())
            i += 1
        if buf:
            blocks.append({"type": "para", "text": "\n".join(buf)})
        else:
            i += 1

    return meta, blocks


# ------------------------------------------------------------------ 工具
def strip_inline_markdown(text: str) -> str:
    """把内联 Markdown 记号去掉，得到纯文本（用于字数统计与纯文本输出）。"""
    t = re.sub(r"`+([^`]+?)`+", r"\1", text)
    t = re.sub(r"!\[([^\]]*)\]\([^)]*\)", "", t)  # 图片不计入正文字数，也保证两条解析路径文本一致
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"[*_~=]{1,2}([^*_~=]+)[*_~=]{1,2}", r"\1", t)
    return t


def node_text(node: dict) -> str:
    """取节点的纯文本（Markdown 源 或 已渲染 HTML 去标签后的文本）。"""
    if node.get("text"):
        return str(node["text"])
    html = node.get("html") or ""
    return re.sub(r"<[^>]+>", "", html)


def blocks_to_plain(blocks: list[dict]) -> str:
    """IR → 纯文本（保留段落结构），用于字数统计与 --format text。"""
    out: list[str] = []

    def walk(nodes):
        for b in nodes:
            t = b["type"]
            if t in ("heading", "para"):
                out.append(strip_inline_markdown(node_text(b)))
            elif t == "code":
                out.append(b["text"])
            elif t == "quote":
                if b.get("title"):
                    out.append(b["title"])
                walk(b.get("blocks", []))
            elif t == "list":
                for it in b["items"]:
                    out.append(strip_inline_markdown(node_text(it)))
                    if it.get("children"):
                        walk([it["children"]])
            elif t == "table":
                out.append(" | ".join(strip_inline_markdown(c) for c in b["header"]))
                for r in b["rows"]:
                    out.append(" | ".join(strip_inline_markdown(c) for c in r))
            elif t == "hr":
                out.append("")

    walk(blocks)
    return "\n\n".join(x for x in out if x.strip())


def node_signature(blocks: list[dict]) -> list[str]:
    """IR 结构签名：用于比较两条解析路径是否等价。"""
    sig: list[str] = []

    def walk(nodes, depth=0):
        for b in nodes:
            t = b["type"]
            if t == "heading":
                sig.append(f"h{min(b['level'], 6)}:{strip_inline_markdown(node_text(b)).strip()}")
            elif t == "para":
                sig.append(f"p:{strip_inline_markdown(node_text(b)).strip()[:40]}")
            elif t == "code":
                sig.append(f"code:{b['text'].strip()[:24]}")
            elif t == "quote":
                sig.append(f"quote:{(b.get('kind') or 'plain').lower()}")
                walk(b.get("blocks", []), depth + 1)
            elif t == "list":
                sig.append(f"list{'o' if b['ordered'] else 'u'}{len(b['items'])}")
                for it in b["items"]:
                    if it.get("children"):
                        walk([it["children"]], depth + 1)
            elif t == "table":
                sig.append(f"table:{len(b['header'])}x{len(b['rows'])}")
            elif t == "hr":
                sig.append("hr")

    walk(blocks)
    return sig
