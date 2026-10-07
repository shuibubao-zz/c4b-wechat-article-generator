#!/usr/bin/env python3
"""wechat-publisher 自检 / eval。

skill-creator 的流程要求"写测试用例 → 跑 eval → 迭代"。这里就是那套 eval：
每个用例断言一项能力真的生效，而不是"脚本没报错"。

    python selftest.py            # 跑全部用例
    python selftest.py --json r.json
"""

from __future__ import annotations

import base64
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import md_lite  # noqa: E402
import math_render  # noqa: E402
import themes as T  # noqa: E402
import typography as TY  # noqa: E402
import wechat_check  # noqa: E402
import convert_to_wechat as C  # noqa: E402

PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

SAMPLE = """---
title: 公众号排版的 6 个坑
author: 卢怡然
date: 2026-10-06
abstract: 从 Markdown 到公众号，中间有 6 个会吃掉你排版的技术坑。
theme: accent
toc: true
---

# 开篇

这是第3节内容，真的!

## 坑一：h1 被禁用

公众号把 h1 留给文章标题，正文里的 h1 会被丢弃或降级。

### 细节

- 列表项 A
- 列表项 B
    - 子项 B1

1. 第一步
2. 第二步

> [!NOTE] 记住这条
> 所有 CSS 必须写成 inline style。

:::warning 别踩
SVG 在保存时会消失。
:::

（注意：两个引用块之间必须留空行，否则会被合并成一个块）

> 普通引用段落。

| 能力 | starter | 定制版 |
|------|---------|--------|
| 主题 | 无 | 4 套 |

```python
def hello():
    print("hi")
```

---

正文里有 **加粗**、`code`、[链接](https://example.com) 和 ![配图](img.png)。
"""


class Fail(AssertionError):
    pass


def _tmpdir() -> Path:
    d = Path(tempfile.mkdtemp(prefix="wpselftest_"))
    return d


def _prepare(tmp: Path) -> Path:
    md = tmp / "sample.md"
    md.write_text(SAMPLE, encoding="utf-8")
    (tmp / "img.png").write_bytes(PNG_1PX)
    return md


def run_convert(md: Path, out: Path, extra: list[str] | None = None) -> dict:
    argv = [str(md), str(out), *(extra or [])]
    return C.convert_one(md, out, C.build_parser().parse_args(argv))


# ---------------------------------------------------------------- 用例
def t_themes():
    for name in T.THEME_NAMES:
        th = T.build_theme(name)
        assert th["p"] and th["h2"], f"{name} 缺样式"
    assert "#1a73e8" in T.build_theme("accent")["h2"], "accent 主题未生效"
    assert T.build_theme("不存在的主题")["p"] == T.build_theme("default")["p"], "未知主题未回退"
    th = T.build_theme("default", {"p": "font-size: 17px;"})
    assert th["p"] == "font-size: 17px;", "theme-file 覆盖未生效"


def t_typography():
    assert TY.apply_typography("这是第3节") == "这是第 3 节", TY.apply_typography("这是第3节")
    assert TY.apply_typography("用C4B挑战") == "用 C4B 挑战", TY.apply_typography("用C4B挑战")
    assert TY.apply_typography("真的!") == "真的！", TY.apply_typography("真的!")
    assert TY.apply_typography("iOS 用户") == "iOS 用户", "已有空格不应重复插入"
    assert TY.apply_typography("等等...") == "等等……"


def t_lite_parse():
    meta, blocks = md_lite.parse_markdown(SAMPLE)
    assert meta["title"] == "公众号排版的 6 个坑", meta.get("title")
    assert meta["theme"] == "accent"
    sig = md_lite.node_signature(blocks)
    joined = "\n".join(sig)
    for want in ["h2:坑一", "listu2", "listo2", "quote:note", "quote:warning", "table:3x1", "code:"]:
        assert any(want in s for s in sig), f"缺少结构 {want}\n{joined}"


def t_dual_engine():
    """markdown 库路径与零依赖路径必须产出等价结构。"""
    tmp = _tmpdir()
    md = _prepare(tmp)
    _m1, lite_blocks = md_lite.parse_markdown(md.read_text(encoding="utf-8"))
    _m2, lib_blocks, engine = C.read_markdown(md, "auto")
    if engine == "lite(零依赖)":
        raise Fail(f"本机 markdown 库不可用，无法做等价性对比（engine={engine}）")
    a, b = md_lite.node_signature(lite_blocks), md_lite.node_signature(lib_blocks)
    assert len(a) == len(b), f"节点数不一致：lite={len(a)} lib={len(b)}\nlite={a}\nlib={b}"
    for x, y in zip(a, b):
        assert x.rstrip("…") == y.rstrip("…"), f"结构不一致：{x!r} != {y!r}"


def t_output_compliance():
    tmp = _tmpdir()
    md = _prepare(tmp)
    for theme in T.THEME_NAMES:
        out = tmp / f"out_{theme}.html"
        rep = run_convert(md, out, ["--theme", theme])
        ck = rep["check"]
        assert ck["ok"], f"{theme} 主题合规自检失败：{ck['errors']}"
        html = out.read_text(encoding="utf-8")
        for bad in ("<h1", "<div", "<script", "<style", "<iframe", "<svg", 'class="', 'id="'):
            assert bad not in html, f"{theme} 输出仍含 {bad}"


def t_heading_mapping():
    tmp = _tmpdir()
    md = _prepare(tmp)
    out = tmp / "o.html"
    run_convert(md, out)
    html = out.read_text(encoding="utf-8")
    assert "<h1" not in html, "h1 未降级"
    assert '<h2 style' in html and '<h3 style' in html, "缺少 h2/h3"


def t_callout():
    tmp = _tmpdir()
    md = _prepare(tmp)
    out = tmp / "o.html"
    run_convert(md, out)
    html = out.read_text(encoding="utf-8")
    assert "📘" in html and "border-left: 4px solid" in html, "知识点框缺失"
    assert "⚠️" in html, "注意框缺失"
    assert "普通引用段落" in html and '#f7f8fa' in html, "普通引用样式缺失"


def t_toc():
    tmp = _tmpdir()
    md = _prepare(tmp)
    out = tmp / "o.html"
    run_convert(md, out, ["--toc"])
    html = out.read_text(encoding="utf-8")
    assert "目录" in html, "目录标题缺失"
    items = len(re.findall(r'font-size: 15px; color: #333; margin: 4px 0;', html))
    assert items >= 1, "目录条目缺失"


def t_footer_and_meta():
    tmp = _tmpdir()
    md = _prepare(tmp)
    out = tmp / "o.html"
    run_convert(md, out)
    html = out.read_text(encoding="utf-8")
    assert "卢怡然" in html, "作者元信息缺失"
    assert "分钟读完" in html, "阅读时长缺失"
    assert "原创" in html, "页脚版权缺失"


def t_image_embed():
    tmp = _tmpdir()
    md = _prepare(tmp)
    out = tmp / "o.html"
    run_convert(md, out)
    html = out.read_text(encoding="utf-8")
    assert "data:image/png;base64," in html, "本地图片未转成 base64"
    assert "img.png" not in html, "图片仍引用外部路径"


def t_image_warnings():
    tmp = _tmpdir()
    md = tmp / "a.md"
    md.write_text("![x](missing.png)\n\n![s](a.svg)\n", encoding="utf-8")
    (tmp / "a.svg").write_text("<svg/>", encoding="utf-8")
    out = tmp / "o.html"
    rep = run_convert(md, out)
    joined = " ".join(rep["warnings"] + rep["check"]["warnings"])
    assert "未找到" in joined, f"缺图未告警：{joined}"
    assert "SVG" in joined, f"SVG 未告警：{joined}"


def t_text_format():
    tmp = _tmpdir()
    md = _prepare(tmp)
    out = tmp / "o.txt"
    rep = run_convert(md, out, ["--format", "text"])
    text = out.read_text(encoding="utf-8")
    assert "公众号排版的 6 个坑" in text or "坑一" in text, "纯文本输出为空"
    assert "<p" not in text, "纯文本输出混入 HTML"


def t_batch():
    tmp = _tmpdir()
    src = tmp / "src"
    src.mkdir()
    for i in range(3):
        (src / f"a{i}.md").write_text(f"# 标题{i}\n\n内容{i}\n", encoding="utf-8")
    out_dir = tmp / "out"
    res = C.batch_convert(src, out_dir, C.build_parser().parse_args([str(src), str(out_dir), "--batch"]))
    assert res["count"] == 3, res["count"]
    assert (out_dir / "index.html").exists(), "索引页缺失"
    assert len(list(out_dir.glob("a*.html"))) == 3, "批量输出文件数不对"


def t_docx_graceful():
    """没有 python-docx 时必须给出可操作提示，而不是堆栈。"""
    tmp = _tmpdir()
    docx = tmp / "a.docx"
    docx.write_bytes(b"PK\x03\x04fake")
    out = tmp / "o.html"
    try:
        C.convert_one(docx, out, C.build_parser().parse_args([str(docx), str(out)]))
    except RuntimeError as e:
        assert "python-docx" in str(e), f"提示不可操作：{e}"
    except Exception as e:  # python-docx 已安装时，损坏文件应被明确报错或正常失败
        assert not isinstance(e, AssertionError)


def t_checker_catches_bad_html():
    bad = '<div class="x"><h1>标题</h1><script>alert(1)</script><p style="position: absolute;">x</p></div>'
    res = wechat_check.check_html(bad)
    assert not res.ok, "检查器没有发现违规 HTML"
    joined = " ".join(res.errors)
    for want in ("div", "h1", "script", "class", "position"):
        assert want in joined, f"未报出 {want}：{joined}"


def t_code_block_preserved():
    tmp = _tmpdir()
    md = tmp / "c.md"
    md.write_text("```python\ndef f():\n    return 1\n```\n", encoding="utf-8")
    out = tmp / "o.html"
    run_convert(md, out)
    html = out.read_text(encoding="utf-8")
    assert "&nbsp;" in html, "代码缩进未保留"
    assert "def f():" in html and "return 1" in html, "代码内容丢失"


def _write(tmp: Path, name: str, text: str) -> Path:
    p = tmp / name
    p.write_text(text, encoding="utf-8")
    return p


def t_math_render_or_fallback():
    """公式：有 matplotlib → base64 PNG；没有 → 等宽文本 + 告警（不假装支持）。"""
    tmp = _tmpdir()
    md = _write(tmp, "m.md", "行内 $E=mc^2$ 与行间：\n\n$$\\int_0^1 x^2 dx = \\frac{1}{3}$$\n")
    out = tmp / "o.html"
    rep = run_convert(md, out)
    html = out.read_text(encoding="utf-8")
    if math_render.available():
        assert "data:image/png;base64," in html, "公式未渲染成 PNG"
        assert html.count("<img") >= 2, f"行内/行间公式应各有一个 img：{html.count('<img')}"
        assert not rep["warnings"], f"有渲染器时不应有降级告警：{rep['warnings']}"
    else:
        assert "E=mc^2" in html, "降级时应保留公式原文"
        assert any("公式降级" in w for w in rep["warnings"]), "缺少降级告警"


def t_math_dual_engine_identical():
    """两条解析引擎对公式的处理必须字节一致（否则换台机器排版就变了）。"""
    tmp = _tmpdir()
    md = _write(tmp, "m.md", "行内 $a^2+b^2=c^2$ 结束。\n")
    a, b = tmp / "a.html", tmp / "b.html"
    run_convert(md, a, ["--engine", "markdown"])
    run_convert(md, b, ["--engine", "lite"])
    assert a.read_bytes() == b.read_bytes(), "双引擎对公式的输出不一致"


def t_math_code_guard():
    """代码里的 $ 提示符不能被当成公式（shell 命令最常见的误伤点）。"""
    tmp = _tmpdir()
    md = _write(tmp, "c.md", "```bash\n$ python convert.py a.md out.html\n```\n\n行内 `$x$` 也不是公式。\n")
    out = tmp / "o.html"
    run_convert(md, out)
    html = out.read_text(encoding="utf-8")
    assert "$ python convert.py" in html, "代码块里的 $ 提示符被吃掉了"
    if math_render.available():
        assert "data:image/png;base64," not in html, "代码/行内 code 里的 $ 被误渲染成公式"


def t_math_off_flag():
    tmp = _tmpdir()
    md = _write(tmp, "m.md", "公式 $x^2$ 保持原样。\n")
    out = tmp / "o.html"
    run_convert(md, out, ["--math", "off"])
    html = out.read_text(encoding="utf-8")
    assert "x^2" in html and "data:image/png;base64," not in html, "--math off 未生效"


TESTS = [
    ("主题系统（4 套 + 覆盖 + 回退）", t_themes),
    ("中文排版（间距/标点/省略号）", t_typography),
    ("零依赖解析（front-matter + 全部块类型）", t_lite_parse),
    ("双引擎结构等价（markdown 库 ↔ 零依赖）", t_dual_engine),
    ("输出合规（4 主题均无违规标签/属性）", t_output_compliance),
    ("h1 降级为 h2", t_heading_mapping),
    ("callout 框（知识点/注意/普通引用）", t_callout),
    ("自动目录", t_toc),
    ("元数据与页脚版权", t_footer_and_meta),
    ("本地图片转 base64", t_image_embed),
    ("图片异常告警（缺图/SVG）", t_image_warnings),
    ("纯文本输出", t_text_format),
    ("批量转换 + 索引页", t_batch),
    ("docx 缺失时的可操作报错", t_docx_graceful),
    ("合规检查器能抓到坏 HTML", t_checker_catches_bad_html),
    ("代码块缩进与内容保留", t_code_block_preserved),
    ("数学公式（PNG 渲染 / 缺依赖降级告警）", t_math_render_or_fallback),
    ("数学公式：双引擎输出字节一致", t_math_dual_engine_identical),
    ("数学公式：代码块里的 $ 不被误伤", t_math_code_guard),
    ("数学公式：--math off 可关闭", t_math_off_flag),
]


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    passed, failed = [], []
    for name, fn in TESTS:
        try:
            fn()
            passed.append(name)
            print(f"  ✅ {name}")
        except Exception as e:  # noqa: BLE001 - eval 需要看到全部失败原因
            failed.append((name, f"{type(e).__name__}: {e}"))
            print(f"  ❌ {name}\n       {type(e).__name__}: {e}")
    total = len(TESTS)
    print(f"\n自检结果：{len(passed)}/{total} 通过")
    if "--json" in argv:
        idx = argv.index("--json")
        Path(argv[idx + 1]).write_text(
            json.dumps({"total": total, "passed": passed,
                        "failed": [{"name": n, "error": e} for n, e in failed]},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
