#!/usr/bin/env python3
"""公众号 HTML 合规自检（wechat-publisher 定制版）。

starter 只负责"生成"，不负责"验证"——输出能不能在公众号编辑器里活下来，
全靠人肉粘贴到浏览器里看。这里把 references/wechat_restrictions.md 里的规则
形式化成可执行的检查，转换完成后自动跑一遍：

  硬错误（会导致排版丢失）：script/style/iframe/h1/div/svg/video/audio/form…
  属性错误：class / id / on* 事件
  CSS 错误：不在白名单里的属性（position/float/flex/animation 等）
  软警告：外链图片、正文外链、SVG data URI、超长文章、超大图片

只用标准库正则解析，因此零依赖环境下也能跑。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

ALLOWED_TAGS = {
    "p", "h2", "h3", "h4", "ul", "ol", "li", "span", "img", "a",
    "table", "thead", "tbody", "tr", "th", "td", "br", "strong", "em", "b", "i",
}

# 出现即判定排版可能丢失
FORBIDDEN_TAGS = {
    "script", "style", "iframe", "h1", "div", "svg", "video", "audio",
    "form", "input", "button", "textarea", "select", "canvas", "link", "meta",
    "nav", "header", "footer", "article", "section", "aside", "main",
    "figure", "figcaption", "pre", "code", "blockquote", "center", "font",
}

# 不保证被保留，但不算硬错误
SOFT_TAGS = {"section", "footer", "header", "article", "nav", "aside", "main"}

FORBIDDEN_ATTRS = {"class", "id"}
EVENT_ATTR_RE = re.compile(r"^on[a-z]+$", re.I)

ALLOWED_CSS = {
    "color", "background-color", "font-size", "font-weight", "font-style",
    "font-family", "line-height", "letter-spacing", "text-align",
    "text-decoration", "text-indent", "margin", "margin-top", "margin-bottom",
    "margin-left", "margin-right", "padding", "padding-top", "padding-bottom",
    "padding-left", "padding-right", "border", "border-left", "border-top",
    "border-bottom", "border-right", "border-collapse", "border-radius",
    "display", "vertical-align", "max-width", "width", "white-space",
    "word-break", "word-wrap", "overflow-wrap",
}

FORBIDDEN_CSS_HINT = {
    "position", "float", "flex", "grid", "animation", "transition",
    "transform", "z-index", "top", "left", "right", "bottom", "height",
}

TAG_RE = re.compile(r"<\s*(/?)\s*([A-Za-z][A-Za-z0-9]*)([^>]*?)(/?)>", re.S)
ATTR_RE = re.compile(r"([A-Za-z_:][-A-Za-z0-9_:]*)\s*=\s*\"([^\"]*)\"")


@dataclass
class CheckResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    def error(self, msg: str) -> None:
        self.errors.append(msg)
        self.ok = False

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def check_html(html: str, strict_css: bool = True) -> CheckResult:
    """检查一段最终 HTML（含或不含外壳均可）。"""
    res = CheckResult()
    body = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    body_no_doctype = re.sub(r"<!DOCTYPE[^>]*>", "", body, flags=re.I)

    tag_counts: dict[str, int] = {}
    src_values: list[str] = []

    for _tm in TAG_RE.finditer(body_no_doctype):
        closing, name, attrs = _tm.group(1), _tm.group(2), _tm.group(3)
        lname = name.lower()
        if lname in ("!doctype",):
            continue
        if not closing:  # 只统计开始标签，避免成对标签被计两次
            tag_counts[lname] = tag_counts.get(lname, 0) + 1

        if lname in FORBIDDEN_TAGS and lname not in SOFT_TAGS:
            res.error(f"违规标签 <{lname}>（公众号会剥离或掉排版）")
        elif lname in SOFT_TAGS:
            res.warn(f"标签 <{lname}> 不在白名单，公众号可能不保留")
        elif lname not in ALLOWED_TAGS:
            res.warn(f"标签 <{lname}> 不在已验证白名单内")

        for am in ATTR_RE.finditer(attrs):
            an = am.group(1).lower()
            avalue = am.group(2)
            if an in FORBIDDEN_ATTRS:
                res.error(f"违规属性 {an}=\"{avalue[:24]}\"（公众号不支持 class/id）")
            elif EVENT_ATTR_RE.match(an):
                res.error(f"违规事件属性 {an}（公众号禁止 JS）")
            if an == "style":
                for decl in avalue.split(";"):
                    prop = decl.split(":", 1)[0].strip().lower()
                    if not prop:
                        continue
                    if prop in FORBIDDEN_CSS_HINT:
                        res.error(f"违规 CSS 属性 {prop}（公众号不支持布局/定位属性）")
                    elif strict_css and prop not in ALLOWED_CSS:
                        res.warn(f"CSS 属性 {prop} 不在已知可用白名单，建议核对")
            if an == "src":
                src_values.append(avalue)

    # 统计
    text = re.sub(r"<[^>]+>", "", body_no_doctype)
    text = re.sub(r"\s+", "", text)
    res.stats["chars"] = len(text)
    res.stats["images"] = tag_counts.get("img", 0)
    res.stats["h2"] = tag_counts.get("h2", 0)
    res.stats["h3"] = tag_counts.get("h3", 0)
    res.stats["p"] = tag_counts.get("p", 0)
    res.stats["tables"] = tag_counts.get("table", 0)
    res.stats["links"] = tag_counts.get("a", 0)
    res.stats["code_blocks"] = tag_counts.get("span", 0)

    # 软警告
    external_img = [s for s in src_values if s.startswith(("http://", "https://"))]
    data_img = [s for s in src_values if s.startswith("data:")]
    svg_img = [s for s in data_img if "svg" in s[:40]]
    if external_img:
        res.warn(
            f"{len(external_img)} 张图片使用外链，粘贴到公众号时可能丢失，"
            "建议改用本地图（自动转 base64）或上传到公众号素材库"
        )
    if svg_img:
        res.warn("检测到 SVG data URI —— 公众号保存时会消失，必须转成 PNG")
    for s in data_img:
        if len(s) > 10 * 1024 * 1024 * 4 / 3:
            res.warn("有图片 base64 超过 10MB，超过公众号单图上限")
    if res.stats["chars"] > 20000:
        res.warn(f"正文约 {res.stats['chars']} 字，接近公众号 2 万字上限")
    if res.stats["links"] > 0:
        res.warn(
            f"正文含 {res.stats['links']} 个外链 —— 公众号正文通常不允许跳转外部域名，"
            "建议把链接放到「阅读原文」或文末"
        )
    return res


def format_report(res: CheckResult) -> str:
    lines = []
    lines.append("合规自检：" + ("✅ 通过（无硬错误）" if res.ok else "❌ 存在硬错误"))
    for e in res.errors[:20]:
        lines.append(f"  [错误] {e}")
    for w in res.warnings[:20]:
        lines.append(f"  [提醒] {w}")
    lines.append(
        "  统计：正文 {chars} 字 / 图 {images} 张 / h2 {h2} 个 / h3 {h3} 个 / 表格 {tables} 个".format(
            **res.stats
        )
    )
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python wechat_check.py <file.html>")
        raise SystemExit(1)
    content = open(sys.argv[1], encoding="utf-8").read()
    r = check_html(content)
    print(format_report(r))
    raise SystemExit(0 if r.ok else 1)
