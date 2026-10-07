#!/usr/bin/env python3
"""WeChat Publisher — Markdown / Word → 公众号 HTML（定制版）。

在 starter kit 的基础上新增的能力：
  1. 文章元数据（front-matter：标题/作者/日期/摘要/主题）
  2. 四套主题（default / accent / warm / minimal），支持 --theme-file 自定义
  3. callout 高亮框（> [!NOTE] 与 :::warning 两种写法）
  4. 自动目录（--toc）
  5. 页脚版权声明（--footer / front-matter copyright）
  6. 中文排版优化（中英文间距、标点，--typo 默认开）
  7. 本地图片自动转 base64 内嵌（--embed-images 默认开）
  8. 批量转换（传入目录即可，附索引页）
  9. 零依赖降级解析（装不上 markdown/bs4 也能跑完整流程）
 10. 输出合规自检（转换后自动跑 wechat_check）
 11. 多格式输出（公众号 HTML / 纯文本 / 知乎 Markdown）

基本用法（与 starter 兼容）：
    python convert_to_wechat.py input.md output.html
    python convert_to_wechat.py article.md out.html --theme accent --toc
    python convert_to_wechat.py ./articles ./out --batch
    python convert_to_wechat.py selftest            # 跑自检/eval
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import md_lite  # noqa: E402
import themes as T  # noqa: E402
import typography as TY  # noqa: E402
import wechat_check  # noqa: E402

MAX_IMAGE_BYTES = 10 * 1024 * 1024
EMBED_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

SHELL = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
</head>
<body style="max-width: 620px; margin: 0 auto; padding: 24px 16px; background-color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;">
<!-- 复制方式：浏览器打开本文件 → Ctrl+A → Ctrl+C → 粘贴到公众号编辑器（mp.weixin.qq.com） -->
{content}
</body>
</html>
"""


# ==================================================================== 读取
def read_markdown(path: Path, engine: str = "auto") -> tuple[dict, list[dict], str]:
    """返回 (front-matter, IR, 实际使用的引擎名)。"""
    text = path.read_text(encoding="utf-8", errors="replace")
    meta_fm, rest = md_lite.parse_front_matter(
        text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    )
    body = "\n".join(rest)

    if engine in ("auto", "markdown", "lib"):
        try:
            import markdown  # type: ignore
            from bs4 import BeautifulSoup  # type: ignore

            # ::: 围栏是我自己加的语法，markdown 库不认识，先改写成它认识的引用语法，
            # 这样两条解析路径（库 / 零依赖）产出完全一致的 callout。
            # 不用 nl2br：它会把源码里的一次换行变成两个 <br>，
            # 与零依赖路径（一个换行 = 一个 <br>）不一致。改为渲染时统一转换。
            html = markdown.markdown(
                convert_callout_fences(body),
                extensions=["extra", "fenced_code", "sane_lists"],
            )
            return meta_fm, html_to_ir(html, BeautifulSoup), "markdown-lib"
        except ImportError:
            if engine in ("markdown", "lib"):
                raise
    return meta_fm, md_lite.parse_markdown(body)[1], "lite(零依赖)"


_RE_FENCE_OPEN = re.compile(r"^\s{0,3}:::\s*([A-Za-z\u4e00-\u9fff]*)\s*(.*)$")


def convert_callout_fences(text: str) -> str:
    """:::kind 标题 … ::: → > [!KIND] 标题 / > 内容（给 markdown 库用的等价写法）。"""
    out: list[str] = []
    inside = False
    for ln in text.split("\n"):
        if not inside and ln.strip().startswith(":::"):
            m = _RE_FENCE_OPEN.match(ln)
            kind = (m.group(1) if m and m.group(1) else "note").upper()
            title = (m.group(2).strip() if m else "")
            out.append(f"> [!{kind}] {title}".rstrip())
            inside = True
        elif inside and ln.strip() == ":::":
            inside = False
        elif inside:
            out.append(("> " + ln).rstrip())
        else:
            out.append(ln)
    return "\n".join(out)


def html_to_ir(html: str, BeautifulSoup) -> list[dict]:
    """HTML → IR（处理 .html 输入，以及 markdown 库的输出）。"""
    soup = BeautifulSoup(html, "html.parser")
    for t in ("script", "style", "iframe", "svg", "video", "audio", "form", "input", "button"):
        for el in soup.find_all(t):
            el.decompose()
    for t in ("section", "article", "nav", "header", "footer", "aside", "main"):
        for el in soup.find_all(t):
            el.unwrap()
    for d in soup.find_all("div"):
        d.name = "p"
    root = soup.body or soup
    return _children_to_ir(root)


def _children_to_ir(node) -> list[dict]:
    blocks: list[dict] = []
    pending_text: list[str] = []

    def flush():
        if pending_text:
            blocks.append({"type": "para", "html": "".join(pending_text).strip()})
            pending_text.clear()

    for child in list(node.children):
        name = getattr(child, "name", None)
        if name is None:
            s = str(child)
            if s.strip():
                pending_text.append(s)
            continue
        if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            flush()
            blocks.append(
                {"type": "heading", "level": int(name[1]), "html": child.decode_contents()}
            )
            continue
        flush()
        if name == "p":
            blocks.append({"type": "para", "html": child.decode_contents()})
        elif name == "pre":
            code = child.find("code")
            blocks.append(
                {"type": "code", "text": (code.get_text() if code else child.get_text())}
            )
        elif name == "blockquote":
            # Python-Markdown 会把相邻的两个引用块合并成一个 blockquote，
            # 所以这里必须扫描块内所有段落，遇到 [!KIND] 就切分出一个新的 callout。
            blocks.extend(_split_callouts(_children_to_ir(child)))
        elif name in ("ul", "ol"):
            blocks.append(_list_to_ir(child))
        elif name == "table":
            blocks.append(_table_to_ir(child))
        elif name == "hr":
            blocks.append({"type": "hr"})
        else:
            blocks.extend(_children_to_ir(child))
    flush()
    return blocks


_RE_CALLOUT_MARK_HTML = re.compile(r"\s*\[!([A-Za-z\u4e00-\u9fff]+)\]\s*(.*)", re.S)


def _split_callouts(inner: list[dict]) -> list[dict]:
    """把引用块按 [!KIND] 标记切分：普通引用 / 一个或多个 callout。"""
    out: list[dict] = []
    cur: list[dict] = []
    kind: str | None = None
    title = ""

    def flush() -> None:
        nonlocal cur, kind, title
        if cur or kind is not None:
            out.append({"type": "quote", "kind": kind, "title": title, "blocks": cur})
        cur, kind, title = [], None, ""

    for node in inner:
        if node["type"] == "para":
            raw_html = node.get("html", "")
            plain = re.sub(r"<[^>]+>", "", re.sub(r"<br\s*/?>", "\n", raw_html))
            m = _RE_CALLOUT_MARK_HTML.match(plain)
            if m:
                flush()
                kind = m.group(1)
                lines = [l.strip() for l in m.group(2).split("\n") if l.strip()]
                title = lines[0] if lines else ""
                html2 = re.sub(r"^\s*\[!([A-Za-z\u4e00-\u9fff]+)\]\s*", "", raw_html, count=1)
                cut = re.match(r"^[^<]*?<br\s*/?>", html2)
                if cut:
                    html2 = html2[cut.end():]
                elif title:
                    # 没有 <br> 时（未启用 nl2br），按源码换行切掉标题行
                    nl = html2.find("\n")
                    html2 = html2[nl + 1:] if nl >= 0 else ""
                html2 = html2.strip()
                if html2:
                    cur.append({"type": "para", "html": html2})
                continue
        cur.append(node)
    if cur or kind is not None:
        flush()
    return out


def _list_to_ir(ul) -> dict:
    items = []
    for li in ul.find_all("li", recursive=False):
        nested = li.find(["ul", "ol"], recursive=False)
        if nested is not None:
            nested.extract()
        inline = li.decode_contents()
        items.append(
            {"text": "", "html": inline, "children": _list_to_ir(nested) if nested else None}
        )
    return {"type": "list", "ordered": ul.name == "ol", "items": items}


def _table_to_ir(table) -> dict:
    header: list[str] = []
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        vals = [c.decode_contents().strip() for c in cells]
        if tr.find("th") and not rows:
            header = vals
        else:
            rows.append(vals)
    if not header and rows:
        header = rows.pop(0)
    return {"type": "table", "header": header, "rows": rows, "html": True}


def read_docx(path: Path) -> tuple[dict, list[dict], str]:
    try:
        from docx import Document  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "读取 .docx 需要 python-docx：pip install python-docx（.md 无需任何依赖）"
        ) from exc
    doc = Document(str(path))
    blocks: list[dict] = []
    for para in doc.paragraphs:
        raw = para.text.strip()
        if not raw:
            continue
        style = para.style.name if para.style else ""
        if style.startswith("Heading"):
            level = 1
            m = re.search(r"(\d+)", style)
            if m:
                level = int(m.group(1))
            blocks.append({"type": "heading", "level": level, "text": raw})
            continue
        html = "".join(_run_html(r) for r in para.runs)
        blocks.append({"type": "para", "html": html or raw})
    for tb in doc.tables:
        rows = [[c.text.strip() for c in r.cells] for r in tb.rows]
        if rows:
            blocks.append({"type": "table", "header": rows[0], "rows": rows[1:]})
    return {}, blocks, "python-docx"


def _run_html(run) -> str:
    t = run.text
    if not t:
        return ""
    from html import escape

    t = escape(t, quote=False)
    if run.bold and run.italic:
        return f'<span style="font-weight: bold; font-style: italic;">{t}</span>'
    if run.bold:
        return f'<span style="font-weight: bold;">{t}</span>'
    if run.italic:
        return f'<span style="font-style: italic;">{t}</span>'
    return t


# ==================================================================== 内联清洗
_RE_MATH = re.compile(r"\$\$(?P<d>.+?)\$\$|\$(?P<i>[^$\n]+?)\$", re.S)
_RE_CODE_SPAN = re.compile(r"(<code\b[^>]*>.*?</code>)", re.S | re.I)


def _math_sub(text: str, theme: dict[str, str]) -> str:
    """片段内的 $..$ / $$..$$ → 公式图片（跳过 <code> 区域，避免误伤 shell 的 $）。"""

    def one(m: re.Match) -> str:
        display = m.group("d") is not None
        tex = (m.group("d") or m.group("i")).strip()
        return md_lite._math_html(tex, display, theme)

    return _RE_MATH.sub(one, text)


_MATH_SLOTS: list[str] = []


def sanitize_inline(frag: str, theme: dict[str, str], typo: bool) -> str:
    """把 HTML 片段里的 strong/em/code/a/img 换成带 inline style 的等价物。"""
    frag = re.sub(r"<br\s*/?>", "<br>", frag)  # 统一换行标签，保证两条引擎输出字节一致
    _MATH_SLOTS.clear()
    if md_lite.MATH_ENABLED and "$" in frag:
        # ① 必须在 <code> 被替换成 span 之前做，否则无法区分代码块里的 $ 提示符；
        # ② 公式的 <img> 会被后面的 img 归一化改写样式，所以先放占位符、最后再插回。
        def _slot(m: re.Match) -> str:
            display = m.group("d") is not None
            tex = (m.group("d") or m.group("i")).strip()
            _MATH_SLOTS.append(md_lite._math_html(tex, display, theme))
            return "\x00M%d\x00" % (len(_MATH_SLOTS) - 1)

        frag = "".join(
            p if p.lower().startswith("<code") else _RE_MATH.sub(_slot, p)
            for p in _RE_CODE_SPAN.split(frag)
        )
    frag = re.sub(r"</?(?:strong|b)>", lambda m: "</span>" if m.group(0).startswith("</")
                  else f'<span style="{theme["strong"]}">', frag)
    frag = re.sub(r"</?(?:em|i)>", lambda m: "</span>" if m.group(0).startswith("</")
                  else f'<span style="{theme["em"]}">', frag)
    frag = re.sub(r"</?(?:del|s)>", lambda m: "</span>" if m.group(0).startswith("</")
                  else f'<span style="{theme["del"]}">', frag)
    frag = re.sub(r"<code[^>]*>", f'<span style="{theme["code_inline"]}">', frag)
    frag = frag.replace("</code>", "</span>")

    def a_sub(m: re.Match) -> str:
        href = re.search(r'href\s*=\s*"([^"]*)"', m.group(0))
        if not href:
            return ""
        return f'<a href="{href.group(1)}" style="{theme["a"]}">'

    frag = re.sub(r"<a\s[^>]*>", a_sub, frag)

    def img_sub(m: re.Match) -> str:
        src = re.search(r'src\s*=\s*"([^"]*)"', m.group(0))
        alt = re.search(r'alt\s*=\s*"([^"]*)"', m.group(0))
        if not src:
            return ""
        return (
            f'<img src="{src.group(1)}" alt="{alt.group(1) if alt else ""}" '
            f'style="{theme["img"]}" />'
        )

    frag = re.sub(r"<img\s[^>]*>", img_sub, frag)
    frag = re.sub(r'\s(?:class|id)="[^"]*"', "", frag)
    for idx, slot_html in enumerate(_MATH_SLOTS):     # 公式插回（带自己的样式）
        frag = frag.replace("\x00M%d\x00" % idx, slot_html)
    frag = re.sub(r'<span style="[^"]*"><br\s*/?></span>', "", frag)
    if typo:
        frag = typo_html(frag)
    return frag


def typo_html(frag: str) -> str:
    """对 HTML 片段中的文本节点做中文排版（跳过 <code> 与标签内部）。"""
    parts = re.split(r"(<[^>]+>)", frag)
    in_code = False
    out = []
    for p in parts:
        if p.startswith("<"):
            low = p.lower()
            if low.startswith("<code"):
                in_code = True
            elif low.startswith("</code"):
                in_code = False
            out.append(p)
        else:
            out.append(p if in_code else TY.apply_typography(p))
    return "".join(out)


def inline_unit(unit, theme: dict[str, str], typo: bool) -> str:
    """渲染一个内联单元：优先用已渲染的 html，否则按 Markdown 渲染。"""
    if isinstance(unit, dict):
        html = unit.get("html")
        if html is not None:
            return sanitize_inline(html, theme, typo).replace("\n", "<br>")
        return md_lite.render_inline(unit.get("text", ""), theme,
                                     TY.apply_typography if typo else None)
    if unit.get("html") is not None:
        return sanitize_inline(unit["html"], theme, typo)
    return md_lite.render_inline(unit.get("text", ""), theme,
                                 TY.apply_typography if typo else None)


# ==================================================================== 渲染
def _esc(text: str) -> str:
    from html import escape

    return escape(text, quote=False)


def _code_html(text: str, style: str) -> str:
    lines = []
    for ln in text.split("\n"):
        lead = len(ln) - len(ln.lstrip(" "))
        body = _esc(ln[lead:])
        lines.append("&nbsp;" * lead + body)
    return f'<p style="{style}">' + "<br>".join(lines) + "</p>"


def render_blocks(blocks: list[dict], theme: dict[str, str], typo: bool,
                  headings: list[tuple[int, str]] | None = None) -> str:
    out: list[str] = []
    for b in blocks:
        t = b["type"]
        if t == "heading":
            lvl = b["level"]
            tag = "h2" if lvl <= 2 else "h3" if lvl == 3 else "h4"
            inner = inline_unit(b, theme, typo)
            if headings is not None:
                headings.append((2 if tag == "h2" else 3 if tag == "h3" else 4, inner))
            out.append(f'<{tag} style="{theme[tag]}">{inner}</{tag}>')
        elif t == "para":
            html = inline_unit(b, theme, typo)
            out.append(f'<p style="{theme["p"]}">' + html.replace("\n", "<br>") + "</p>")
        elif t == "code":
            out.append(_code_html(b["text"], theme["code_block"]))
        elif t == "hr":
            out.append(f'<p style="{theme["hr"]}">· · ·</p>')
        elif t == "quote":
            out.extend(render_quote(b, theme, typo))
        elif t == "list":
            out.append(render_list(b, theme, typo))
        elif t == "table":
            out.append(render_table(b, theme, typo))
    return "\n".join(out)


def render_quote(b: dict, theme: dict[str, str], typo: bool) -> list[str]:
    kind = b.get("kind")
    inner = b.get("blocks") or []
    if not inner:
        if not kind:
            return []
        # 只有标题、没有正文的 callout（> [!NOTE] 一句话）
        spec = T.callout_style(theme, T.normalize_kind(kind), "only")
        label = f'{spec["icon"]} {(b.get("title") or "").strip() or spec["label"]}'
        return [
            f'<p style="{spec["style"]}">'
            f'<span style="font-weight: bold; color: {spec["accent"]};">{_esc(label)}</span></p>'
        ]
    if not kind:
        out = []
        for sub in inner:
            if sub["type"] == "para":
                html = inline_unit(sub, theme, typo).replace("\n", "<br>")
                out.append(f'<p style="{theme["blockquote"]}">{html}</p>')
            else:
                out.append(render_blocks([sub], theme, typo))
        return out
    kind = T.normalize_kind(kind)
    title = (b.get("title") or "").strip()
    paras = [s for s in inner if s["type"] == "para"]
    n = len(paras)
    out: list[str] = []
    seen = 0
    for sub in inner:
        if sub["type"] != "para":
            extra = render_blocks([sub], theme, typo)
            out.append(extra)
            continue
        seen += 1
        pos = "only" if n == 1 else "first" if seen == 1 else "last" if seen == n else "mid"
        spec = T.callout_style(theme, kind, pos)
        html = inline_unit(sub, theme, typo).replace("\n", "<br>")
        if seen == 1:
            label = f'{spec["icon"]} {title or spec["label"]}'
            html = f'<span style="font-weight: bold; color: {spec["accent"]};">{_esc(label)}</span><br>{html}' if html else f'<span style="font-weight: bold; color: {spec["accent"]};">{_esc(label)}</span>'
        out.append(f'<p style="{spec["style"]}">{html}</p>')
    return out


def render_list(b: dict, theme: dict[str, str], typo: bool) -> str:
    tag = "ol" if b.get("ordered") else "ul"
    lis = []
    for it in b["items"]:
        html = inline_unit(it, theme, typo).replace("\n", "<br>")
        child = render_list(it["children"], theme, typo) if it.get("children") else ""
        lis.append(f'<li style="{theme["li"]}">{html}{child}</li>')
    return f'<{tag} style="{theme[tag]}">' + "".join(lis) + f"</{tag}>"


def render_table(b: dict, theme: dict[str, str], typo: bool) -> str:
    is_html = b.get("html", False)

    def cell(c):
        if is_html:
            return sanitize_inline(str(c), theme, typo)
        return md_lite.render_inline(str(c), theme, TY.apply_typography if typo else None)

    aligns = b.get("align") or []
    parts = [f'<table style="{theme["table"]}">']
    header = b.get("header") or []
    if header:
        parts.append("<tr>")
        for i, h in enumerate(header):
            al = f' text-align: {aligns[i]};' if i < len(aligns) and aligns[i] else ""
            parts.append(f'<th style="{theme["th"]}{al}">{cell(h)}</th>')
        parts.append("</tr>")
    for r in b.get("rows", []):
        parts.append("<tr>")
        for i, c in enumerate(r):
            al = f' text-align: {aligns[i]};' if i < len(aligns) and aligns[i] else ""
            parts.append(f'<td style="{theme["td"]}{al}">{cell(c)}</td>')
        parts.append("</tr>")
    parts.append("</table>")
    return "".join(parts)


def render_meta(meta: dict, theme: dict[str, str], plain: str) -> list[str]:
    out = []
    title = meta.get("title")
    if title:
        out.append(f'<h2 style="{theme["meta_title"]}">{_esc(title)}</h2>')
    bits = [x for x in (meta.get("author"), meta.get("date")) if x]
    minutes = TY.reading_minutes(plain)
    bits.append(f"约 {minutes} 分钟读完")
    if bits:
        out.append(f'<p style="{theme["meta_info"]}">' + " · ".join(_esc(b) for b in bits) + "</p>")
    if meta.get("abstract"):
        out.append(f'<p style="{theme["meta_abstract"]}">{_esc(meta["abstract"])}</p>')
    return out


def render_toc(headings: list[tuple[int, str]], theme: dict[str, str]) -> list[str]:
    out = [f'<p style="{theme["toc_title"]}">目录</p>']
    n = 0
    for lvl, html in headings:
        if lvl == 2:
            n += 1
            out.append(f'<p style="{theme["toc_h2"]}">{n}. {html}</p>')
        else:
            out.append(f'<p style="{theme["toc_h3"]}">- {html}</p>')
    return out


def render_footer(meta: dict, theme: dict[str, str], author: str) -> list[str]:
    text = meta.get("copyright") or (
        f"本文为原创内容，作者 {author}。欢迎转发分享，转载请注明出处。"
    )
    return [f'<p style="{theme["footer"]}">{_esc(text)}</p>']


# ==================================================================== 图片
def embed_images(html: str, base_dir: Path, enabled: bool, warns: list[str]) -> str:
    def sub(m: re.Match) -> str:
        src = m.group(1)
        if not enabled or src.startswith(("data:", "http://", "https://", "//")):
            return m.group(0)
        p = (base_dir / src) if not Path(src).is_absolute() else Path(src)
        if p.suffix.lower() == ".svg":
            warns.append(f"SVG 图片无法内嵌（公众号保存时会丢弃），请先转 PNG：{src}")
            return m.group(0)
        if not p.exists():
            warns.append(f"图片未找到，已保留原路径：{src}")
            return m.group(0)
        if p.suffix.lower() not in EMBED_SUFFIXES:
            warns.append(f"图片格式 {p.suffix} 不适合内嵌：{src}")
            return m.group(0)
        if p.stat().st_size > MAX_IMAGE_BYTES:
            warns.append(f"图片超过 10MB，公众号会拒收，请压缩：{src}")
            return m.group(0)
        mime = mimetypes.guess_type(p.name)[0] or "image/png"
        b64 = base64.b64encode(p.read_bytes()).decode("ascii")
        return m.group(0).replace(f'src="{src}"', f'src="data:{mime};base64,{b64}"')

    return re.sub(r'<img\s[^>]*src="([^"]+)"[^>]*>', sub, html)


# ==================================================================== 主流程
def convert_one(src: Path, out_path: Path, args) -> dict:
    warns: list[str] = []
    md_lite.MATH_ENABLED = (args.math != "off")
    md_lite.MATH_WARNS = []
    if src.suffix.lower() == ".md":
        meta, blocks, engine = read_markdown(src, args.engine)
    elif src.suffix.lower() == ".docx":
        meta, blocks, engine = read_docx(src)
    elif src.suffix.lower() in (".html", ".htm"):
        try:
            from bs4 import BeautifulSoup  # type: ignore
        except ImportError as exc:
            raise RuntimeError("处理 .html 输入需要 beautifulsoup4：pip install beautifulsoup4") from exc
        meta, blocks, engine = {}, html_to_ir(src.read_text(encoding="utf-8"), BeautifulSoup), "bs4"
    else:
        raise RuntimeError(f"不支持的格式：{src.suffix}（支持 .md / .docx / .html）")

    # 主题：命令行 > front-matter > default
    theme_name = args.theme or meta.get("theme", "default")
    overrides = {}
    if args.theme_file:
        overrides = json.loads(Path(args.theme_file).read_text(encoding="utf-8"))
    theme = T.build_theme(theme_name, overrides)
    theme["_name"] = theme_name

    typo = not args.no_typo
    plain = md_lite.blocks_to_plain(blocks)

    # 标题：front-matter > 首个一级标题
    if not meta.get("title") and blocks and blocks[0]["type"] == "heading" \
            and blocks[0]["level"] == 1:
        meta["title"] = md_lite.strip_inline_markdown(
            blocks[0].get("text") or re.sub(r"<[^>]+>", "", blocks[0].get("html", ""))
        )
        blocks = blocks[1:]
    if args.author:
        meta["author"] = args.author

    # 目录
    headings: list[tuple[int, str]] = []
    body_html = render_blocks(blocks, theme, typo, headings)
    want_toc = (args.toc or str(meta.get("toc", "")).lower() == "true")
    toc_html = (
        "\n".join(render_toc(headings, theme))
        if (want_toc and len(headings) >= 2)
        else ""
    )

    parts = render_meta(meta, theme, plain)
    if toc_html:
        parts.append(toc_html)
    parts.append(body_html)
    if not args.no_footer:
        parts.append("\n".join(render_footer(meta, theme, meta.get("author", "匿名作者"))))
    content = "\n".join(p for p in parts if p)

    content = embed_images(content, src.parent, not args.no_embed, warns)
    if md_lite.MATH_ENABLED and md_lite.MATH_WARNS:
        warns.append("数学公式降级为文本（未安装 matplotlib，pip install matplotlib 后可渲染成 PNG）："
                     + "、".join(md_lite.MATH_WARNS[:3]))

    if args.format == "wechat":
        final = content if args.fragment else SHELL.format(
            title=meta.get("title", src.stem), content=content
        )
    elif args.format == "text":
        final = plain
    else:  # markdown（知乎等平台）
        final = src.read_text(encoding="utf-8")
        final = re.sub(r"^---\n.*?\n---\n", "", final, flags=re.S)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(final, encoding="utf-8")

    report = {"source": str(src), "output": str(out_path), "engine": engine,
              "theme": theme_name, "warnings": warns}
    if args.format == "wechat":
        check = wechat_check.check_html(content)
        report["check"] = {"ok": check.ok, "errors": check.errors,
                           "warnings": check.warnings, "stats": check.stats}
        if not check.ok:
            report["compliance_failed"] = True
    return report


def batch_convert(src_dir: Path, out_dir: Path, args) -> dict:
    files = [p for p in sorted(src_dir.iterdir())
             if p.suffix.lower() in (".md", ".docx") and not p.name.startswith(".")]
    if not files:
        raise RuntimeError(f"{src_dir} 下没有找到 .md/.docx")
    reports = []
    for p in files:
        reports.append(convert_one(p, out_dir / (p.stem + ".html"), args))
    links = "\n".join(
        f'<p style="font-size: 15px; margin: 6px 0;"><a href="./{Path(r["output"]).name}" '
        f'style="color: #0366d6; text-decoration: underline;">'
        f'{Path(r["source"]).name} → {Path(r["output"]).name}</a></p>'
        for r in reports
    )
    index = (
        "<!DOCTYPE html><html><head><meta charset=\"UTF-8\">"
        f"<title>批量转换结果（{len(reports)} 篇）</title></head>"
        '<body style="max-width: 620px; margin: 0 auto; padding: 24px; font-family: '
        '-apple-system, \'PingFang SC\', sans-serif;">'
        f'<h2 style="font-size: 20px;">批量转换结果（{len(reports)} 篇）</h2>'
        f"{links}</body></html>"
    )
    (out_dir / "index.html").write_text(index, encoding="utf-8")
    return {"batch": True, "count": len(reports), "reports": reports,
            "index": str(out_dir / "index.html")}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="convert_to_wechat.py",
        description="Markdown / Word → 公众号 HTML（wechat-publisher 定制版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("input", nargs="?", help="输入文件（.md/.docx/.html）或目录（配合 --batch）")
    p.add_argument("output", nargs="?", help="输出文件（默认与输入同名的 .html）")
    p.add_argument("--theme", choices=T.THEME_NAMES, help="主题（默认取 front-matter theme 或 default）")
    p.add_argument("--theme-file", help="JSON 文件，覆盖任意样式键")
    p.add_argument("--engine", choices=["auto", "markdown", "lite"], default="auto",
                   help="Markdown 解析引擎（auto 优先用 markdown 库，缺失则零依赖降级）")
    p.add_argument("--toc", action="store_true", help="生成目录")
    p.add_argument("--no-footer", action="store_true", help="不追加页脚版权")
    p.add_argument("--no-typo", action="store_true", help="关闭中文排版优化")
    p.add_argument("--no-embed", action="store_true", help="不把本地图片转成 base64")
    p.add_argument("--format", choices=["wechat", "text", "markdown"], default="wechat")
    p.add_argument("--fragment", action="store_true", help="只输出正文片段（不含预览外壳）")
    p.add_argument("--math", choices=["auto", "on", "off"], default="auto",
                   help="数学公式（$..$ / $$..$$）→ PNG 内联；auto=有渲染器就渲染，无则降级为文本并告警")
    p.add_argument("--batch", action="store_true", help="输入为目录，批量转换")
    p.add_argument("--author", help="覆盖作者名（页脚与元信息用）")
    p.add_argument("--strict", action="store_true", help="合规自检有硬错误时以非 0 退出")
    p.add_argument("--report", help="把转换与自检结果写成 JSON")
    p.add_argument("--list-themes", action="store_true", help="列出可用主题后退出")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list_themes:
        print("可用主题：" + " / ".join(T.THEME_NAMES))
        print("callout 类型：" + " / ".join(T.CALLOUT_KINDS))
        return 0
    if not args.input:
        build_parser().print_help()
        return 1
    if args.input == "selftest":
        import selftest

        return selftest.main([])

    src = Path(args.input)
    if args.batch:
        if not src.is_dir():
            print(f"❌ --batch 需要目录，收到：{src}")
            return 1
        out_dir = Path(args.output) if args.output else src / "wechat_out"
        result = batch_convert(src, out_dir, args)
        print(f"✅ 批量转换完成：{result['count']} 篇 → {out_dir}")
        for r in result["reports"]:
            ck = r.get("check", {})
            print(f"   - {Path(r['source']).name}: 引擎 {r['engine']}，"
                  f"主题 {r['theme']}，合规 {'OK' if ck.get('ok') else '❌'}，"
                  f"{ck.get('stats', {}).get('chars', '-')} 字")
        print(f"   索引页：{result['index']}")
        if args.report:
            Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
        return 0

    if not src.exists():
        print(f"❌ 找不到输入文件：{src}")
        return 1
    out_path = Path(args.output) if args.output else src.with_suffix(".html")
    try:
        report = convert_one(src, out_path, args)
    except RuntimeError as e:
        print(f"❌ {e}")
        return 1

    print(f"✅ 已生成 {out_path}")
    print(f"   解析引擎：{report['engine']}　主题：{report['theme']}　格式：{args.format}")
    for w in report["warnings"]:
        print(f"   [提醒] {w}")
    if "check" in report:
        ck = report["check"]
        print("   合规自检：" + ("通过" if ck["ok"] else f"发现 {len(ck['errors'])} 个硬错误"))
        for e in ck["errors"][:10]:
            print(f"     [错误] {e}")
        for w in ck["warnings"][:10]:
            print(f"     [提醒] {w}")
        s = ck["stats"]
        print(f"   统计：{s['chars']} 字 / 图 {s['images']} 张 / h2 {s['h2']} / h3 {s['h3']}"
              f" / 表格 {s['tables']}")
        if args.strict and not ck["ok"]:
            return 2
    if args.report:
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
        print(f"   报告：{args.report}")
    print("\n📋 下一步：浏览器打开 → Ctrl+A → Ctrl+C → 粘贴到 mp.weixin.qq.com")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
