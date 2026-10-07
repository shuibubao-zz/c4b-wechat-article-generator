#!/usr/bin/env python3
"""LaTeX 公式 → PNG（base64 data URI），供公众号 HTML 内联。

为什么必须是位图：公众号编辑器会删掉 <script>（MathJax/KaTeX 全废），
保存时还会丢 SVG。参考官方 wechat-math-html 的思路——渲染成 PNG 再内联，
是目前唯一能在公众号里活下来的公式方案。

实现选择：用 matplotlib 自带的 mathtext 渲染，**不需要本机装 LaTeX**。
代价是只支持 mathtext 语法子集（常见的行内/行间公式够用）。

降级策略（重要）：matplotlib 缺失时 render() 返回 None，调用方降级为等宽文本
并给出告警——**不用"当成普通文本"假装支持**。
"""

from __future__ import annotations

import base64
import io

_CACHE: dict[tuple[str, bool], str] = {}


def available() -> bool:
    try:
        import matplotlib  # noqa: F401
    except Exception:
        return False
    return True


def render(tex: str, display: bool = False) -> str | None:
    """把公式渲染成 data URI；不可用时返回 None。"""
    key = (tex.strip(), display)
    if key in _CACHE:
        return _CACHE[key]
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None

    try:
        fig = plt.figure(figsize=(0.01, 0.01))
        fig.text(0.0, 0.5, "$%s$" % key[0], fontsize=20 if display else 16, color="#24292f")
        buf = io.BytesIO()
        # 不用透明底：透明+黑字在公众号深色模式下会隐形；白底在白色正文里无缝且深色模式可见
        fig.savefig(
            buf, format="png", dpi=200, transparent=False,
            facecolor="white", edgecolor="none",
            bbox_inches="tight", pad_inches=0.08,
        )
        plt.close(fig)
        uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return None
    _CACHE[key] = uri
    return uri
