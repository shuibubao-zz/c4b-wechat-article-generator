#!/usr/bin/env python3
"""中文排版优化（wechat-publisher 定制版）。

starter 对中文排版的处理是「没有处理」——中英文之间没有空隙、标点半角，
在小屏手机上显得拥挤。这里做三条保守规则，只作用于正文文本节点，
**不作用于代码、URL、HTML 属性**：

1. 中英文/中数字之间插入一个半角空格（`第3节` → `第 3 节`），已有空格不重复插入
2. 中文后的半角 `!` `?` 转全角（`真的!` → `真的！`），英文语境不动
3. `...` 转中文省略号 `……`

保守是有意的：排版规则越激进，误伤原文的概率越高。
"""

from __future__ import annotations

import re

# CJK 统一表意文字 + 中日韩假名 + 全角符号 + 中文标点
_CJK = r"\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff\uff01-\uff60\u3000-\u303f"
_LATIN = r"A-Za-z0-9"

_CJK_THEN_LATIN = re.compile(rf"(?<=[{_CJK}])(?=[{_LATIN}])")
_LATIN_THEN_CJK = re.compile(rf"(?<=[{_LATIN}])(?=[{_CJK}])")
_CJK_BANG = re.compile(rf"(?<=[{_CJK}])!(?=\s|$)")
_CJK_QUESTION = re.compile(rf"(?<=[{_CJK}])\?(?=\s|$)")
_ELLIPSIS = re.compile(r"\.\.\.")


def apply_typography(text: str) -> str:
    """对一段纯文本应用中英混排规则。调用方需保证这不是代码内容。"""
    if not text:
        return text
    out = _CJK_THEN_LATIN.sub(" ", text)
    out = _LATIN_THEN_CJK.sub(" ", out)
    # 中英文之间插入空格后可能破坏 !/? 的中文前置判断（如 "好 !"），先取原字符判定
    out = _CJK_BANG.sub("！", out)
    out = _CJK_QUESTION.sub("？", out)
    out = _ELLIPSIS.sub("……", out)
    return out


def count_cjk(text: str) -> int:
    return sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")


def reading_minutes(plain_text: str, cpm: int = 400) -> int:
    """预计阅读时长（分钟）。中文按每分钟 400 字，至少 1 分钟。"""
    n = len([c for c in plain_text if not c.isspace()])
    return max(1, round(n / cpm))


if __name__ == "__main__":
    cases = [
        "我在做C4B挑战的第3节",
        "真的!",
        "等等...还有一件事",
        "iOS 用户注意",
    ]
    for c in cases:
        print(f"{c!r} -> {apply_typography(c)!r}")
