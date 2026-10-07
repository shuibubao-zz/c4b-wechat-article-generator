#!/usr/bin/env python3
"""公众号排版主题定义（wechat-publisher 定制版）。

starter kit 的样式是写死在脚本里的常量，换配色就要改代码。
这里把样式抽成「主题」：基础样式 + 主题覆盖层，支持命令行选主题、
也支持用 --theme-file 传一个 JSON 覆盖任意键（用户自定义配色不必改代码）。

所有值必须是公众号允许的 inline CSS 属性
（见 references/wechat_restrictions.md：不能用 position/float/flex/height 等）。
"""

from __future__ import annotations

# ---------------------------------------------------------------- 基础样式
# 数值沿用 starter kit 的 wechat_styles.md（行高 1.75、正文 16px、#333 不用纯黑），
# 只在间距和层级上做了加强（h4、列表容器、图片）。
BASE: dict[str, str] = {
    "h2": (
        "font-size: 22px; font-weight: bold; line-height: 1.6; "
        "color: #1f2328; margin: 26px 0 12px 0;"
    ),
    "h3": (
        "font-size: 18px; font-weight: bold; line-height: 1.6; "
        "color: #1f2328; margin: 18px 0 8px 0;"
    ),
    "h4": (
        "font-size: 16px; font-weight: bold; line-height: 1.6; "
        "color: #444; margin: 14px 0 6px 0;"
    ),
    "p": "font-size: 16px; line-height: 1.75; color: #333; margin: 12px 0;",
    "li": "font-size: 16px; line-height: 1.75; color: #333; margin: 6px 0;",
    "ul": "margin: 12px 0; padding-left: 22px;",
    "ol": "margin: 12px 0; padding-left: 22px;",
    "code_inline": (
        "background-color: #f2f4f7; color: #c0341d; font-size: 14px; padding: 2px 4px;"
    ),
    "code_block": (
        "background-color: #f6f8fa; color: #24292e; font-size: 14px; "
        "line-height: 1.65; padding: 14px 16px; margin: 14px 0; white-space: pre-wrap;"
    ),
    "blockquote": (
        "background-color: #f7f8fa; color: #666; padding: 10px 15px; "
        "margin: 14px 0; border-left: 4px solid #d0d7de;"
    ),
    "table": "border-collapse: collapse; margin: 14px 0; font-size: 14px;",
    "th": (
        "background-color: #f6f8fa; color: #24292e; font-weight: bold; "
        "padding: 8px 10px; text-align: left; border: 1px solid #d0d7de;"
    ),
    "td": "padding: 8px 10px; border: 1px solid #d0d7de; color: #333;",
    "a": "color: #0366d6; text-decoration: underline;",
    "img": "max-width: 100%; margin: 14px 0;",
    "hr": "text-align: center; color: #c9c9c9; letter-spacing: 4px; margin: 24px 0;",
    # 文章元数据块
    "meta_title": (
        "font-size: 24px; font-weight: bold; line-height: 1.4; color: #1f2328; margin: 0 0 10px 0;"
    ),
    "meta_info": "font-size: 13px; color: #9a9a9a; margin: 0 0 18px 0;",
    "meta_abstract": (
        "font-size: 14px; line-height: 1.7; color: #666; background-color: #f7f8fa; "
        "padding: 12px 14px; margin: 0 0 20px 0;"
    ),
    # 目录
    "toc_title": "font-size: 16px; font-weight: bold; color: #1f2328; margin: 20px 0 8px 0;",
    "toc_h2": "font-size: 15px; color: #333; margin: 4px 0;",
    "toc_h3": "font-size: 14px; color: #888; margin: 3px 0 3px 18px;",
    # 页脚
    "footer": (
        "font-size: 13px; line-height: 1.8; color: #9a9a9a; background-color: #fafafa; "
        "padding: 12px 14px; margin: 30px 0 10px 0;"
    ),
    "strong": "font-weight: bold;",
    "em": "font-style: italic;",
    "del": "text-decoration: line-through;",
    # 正文高亮（==text== 语法）
    "mark": "background-color: #fff3a3; color: #333; padding: 1px 2px;",
}

# ---------------------------------------------------------------- 主题覆盖层
THEMES: dict[str, dict[str, str]] = {
    "default": {},
    "accent": {
        "h2": (
            "font-size: 22px; font-weight: bold; line-height: 1.6; "
            "color: #1a73e8; margin: 26px 0 12px 0;"
        ),
        "h3": (
            "font-size: 18px; font-weight: bold; line-height: 1.6; "
            "color: #1a73e8; margin: 18px 0 8px 0;"
        ),
        "blockquote": (
            "background-color: #f0f7ff; color: #555; padding: 10px 15px; "
            "margin: 14px 0; border-left: 4px solid #1a73e8;"
        ),
        "a": "color: #1a73e8; text-decoration: underline;",
        "th": (
            "background-color: #e8f2ff; color: #1a73e8; font-weight: bold; "
            "padding: 8px 10px; text-align: left; border: 1px solid #cfe3ff;"
        ),
    },
    "warm": {
        "h2": (
            "font-size: 22px; font-weight: bold; line-height: 1.6; "
            "color: #e65100; margin: 26px 0 12px 0;"
        ),
        "h3": (
            "font-size: 18px; font-weight: bold; line-height: 1.6; "
            "color: #e65100; margin: 18px 0 8px 0;"
        ),
        "blockquote": (
            "background-color: #fff8e1; color: #6d4c41; padding: 10px 15px; "
            "margin: 14px 0; border-left: 4px solid #ff9800;"
        ),
        "a": "color: #e65100; text-decoration: underline;",
        "code_block": (
            "background-color: #fff8e1; color: #5d4037; font-size: 14px; "
            "line-height: 1.65; padding: 14px 16px; margin: 14px 0; white-space: pre-wrap;"
        ),
    },
    "minimal": {
        "h2": (
            "font-size: 20px; font-weight: bold; line-height: 1.6; "
            "color: #333; margin: 24px 0 10px 0;"
        ),
        "h3": (
            "font-size: 17px; font-weight: bold; line-height: 1.6; "
            "color: #333; margin: 16px 0 8px 0;"
        ),
        "blockquote": (
            "background-color: #fafafa; color: #666; padding: 8px 14px; "
            "margin: 14px 0; border-left: 3px solid #999;"
        ),
        "code_block": (
            "background-color: #fafafa; color: #333; font-size: 14px; "
            "line-height: 1.65; padding: 12px 14px; margin: 14px 0; white-space: pre-wrap;"
        ),
        "table": "border-collapse: collapse; margin: 14px 0; font-size: 14px;",
    },
}

THEME_NAMES = list(THEMES.keys())

# ---------------------------------------------------------------- callout 配色
# starter 完全没有 callout；这里定义 4 种语义框。
# 主题可以给任一类型指定 accent/bg；未指定则用该类型的默认色。
CALLOUT_KINDS = {
    "note": {"icon": "📘", "label": "知识点", "accent": "#3b82f6", "bg": "#f0f7ff"},
    "tip": {"icon": "💡", "label": "小技巧", "accent": "#0ea5e9", "bg": "#e8f8ff"},
    "practice": {"icon": "🔧", "label": "动手做", "accent": "#10b981", "bg": "#eafaf3"},
    "warning": {"icon": "⚠️", "label": "注意", "accent": "#f59e0b", "bg": "#fff8e6"},
    "quote": {"icon": "💬", "label": "引用", "accent": "#8b5cf6", "bg": "#f5f3ff"},
}

# 别名：中文写法也能用
CALLOUT_ALIASES = {
    "NOTE": "note", "TIP": "tip", "WARNING": "warning", "IMPORTANT": "warning",
    "CAUTION": "warning", "DOING": "practice", "PRACTICE": "practice",
    "知识": "note", "技巧": "tip", "注意": "warning", "实践": "practice",
}

THEME_CALLOUT_OVERRIDES: dict[str, dict[str, dict[str, str]]] = {
    "minimal": {k: {"accent": "#666", "bg": "#fafafa"} for k in CALLOUT_KINDS},
    "warm": {"note": {"accent": "#e65100", "bg": "#fff8e1"}},
}


def build_theme(name: str = "default", overrides: dict[str, str] | None = None) -> dict[str, str]:
    """生成最终样式表：BASE ← 主题覆盖 ← 用户覆盖。未知主题名回退 default。"""
    if name not in THEMES:
        name = "default"
    theme = dict(BASE)
    theme.update(THEMES.get(name, {}))
    if overrides:
        theme.update(overrides)
    return theme


def callout_style(theme: dict[str, str], kind: str, pos: str) -> dict[str, str]:
    """按 callout 类型与位置（first/mid/last）返回配色与几何样式。"""
    spec = dict(CALLOUT_KINDS.get(kind, CALLOUT_KINDS["note"]))
    spec.update(THEME_CALLOUT_OVERRIDES.get(theme.get("_name", "default"), {}).get(kind, {}))
    accent, bg = spec["accent"], spec["bg"]
    common = (
        f"background-color: {bg}; border-left: 4px solid {accent}; "
        "font-size: 15px; line-height: 1.75; color: #333;"
    )
    geometry = {
        "first": "padding: 14px 14px 6px 14px; margin: 18px 0 0 0;",
        "mid": "padding: 0 14px; margin: 0;",
        "last": "padding: 0 14px 14px 14px; margin: 0 0 18px 0;",
        "only": "padding: 14px; margin: 18px 0;",
    }[pos]
    return {
        "style": common + " " + geometry,
        "accent": accent,
        "icon": spec["icon"],
        "label": spec["label"],
    }


def normalize_kind(raw: str) -> str:
    """把 '> [!NOTE]' / ':::' 里写的类型归一化到 CALLOUT_KINDS 的键。"""
    key = (raw or "").strip().upper()
    if key in CALLOUT_ALIASES:
        return CALLOUT_ALIASES[key]
    if (raw or "").strip() in CALLOUT_KINDS:
        return raw.strip()
    # 中文别名不走 upper
    return CALLOUT_ALIASES.get((raw or "").strip(), "note")
