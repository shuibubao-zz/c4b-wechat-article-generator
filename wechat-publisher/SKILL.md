---
name: wechat-publisher
description: |
  把 Markdown / Word 文档转换成可直接粘贴到微信公众号编辑器的 HTML（inline CSS、
  标签合规、中文排版优化），并自动做合规自检。支持四套主题、callout 高亮框、
  自动目录、文章元数据、页脚版权、本地图片转 base64、数学公式渲染成 PNG 内嵌、
  批量转换，且在没有第三方库的环境下也能跑完整流程。
  当用户说"转成公众号""公众号文章""微信公众号格式""make WeChat article"
  "生成公众号 HTML"，或者给出 .md / .docx 文件并要求排版成公众号可发布的样式时使用。
  也适用于需要把技术文章、周报、学习笔记批量发布到公众号的场景。
agent_created: true
---

# WeChat Publisher — Markdown / Word → 公众号 HTML

## Overview

把一份 Markdown 或 Word 文档，变成复制粘贴即可发布的公众号 HTML：自动应用 inline CSS、
剔除公众号不允许的标签与属性、优化中文排版，并在转换完成后做一次合规自检。

与通用 HTML 转换工具的区别：输出**必须**能在公众号编辑器里活下来——
不能用 `<style>`、`<h1>`、`<div>`、`class/id`，图片不能是 SVG data URI。
本技能把这些规则写成了可执行检查（`scripts/wechat_check.py`），而不是靠肉眼看。

## Quick Start

```bash
# 最简：一条命令产出可粘贴的 HTML
python scripts/convert_to_wechat.py 我的文章.md 我的文章.html

# 常用组合：主题 + 目录 + 指定作者
python scripts/convert_to_wechat.py 我的文章.md out.html --theme accent --toc --author 卢怡然

# 批量：一个目录里的全部文章
python scripts/convert_to_wechat.py ./articles ./out --batch

# 跑 eval（20 项能力测试）
python scripts/selftest.py
```

产出后：浏览器打开 HTML → Ctrl+A → Ctrl+C → 粘贴到 mp.weixin.qq.com 编辑器 → 手机预览 → 发布。

## Workflow

### Step 1 — 确认输入与主题

输入支持 `.md` / `.docx` / `.html`。主题用 `--theme` 指定（`default` / `accent` / `warm` / `minimal`），
也可以写在 Markdown 的 front-matter 里（见 Step 2）。不确定时用 `default`。

### Step 2 — 在源文件里写 front-matter（可选但推荐）

文章开头用 `---` 包裹，支持这些键：

```markdown
---
title: 文章标题
author: 卢怡然
date: 2026-10-06
abstract: 一句话摘要，会渲染成灰色摘要框
theme: accent
toc: true
copyright: 自定义页脚文案
---
```

没有 front-matter 时，标题取文档里第一个 `#` 一级标题。

### Step 3 — 用增强语法写正文

| 语法 | 作用 |
|------|------|
| `> [!NOTE] 标题` + `> 内容` | 📘 知识点框（另有 TIP / PRACTICE / WARNING） |
| `:::warning 标题` … `:::` | 同上，围栏写法，适合多段落 |
| `> 普通引用` | 灰色引用块 |
| `==高亮==` | 荧光笔高亮 |
| `--toc` 或 `toc: true` | 自动生成目录 |
| `$行内公式$` / `$$行间公式$$` | 渲染成 200 DPI 白底 PNG 内嵌（需 matplotlib；缺失时降级为红字并告警）；代码区里的 `$` 不解析 |
| 本地图片 `![](img.png)` | 自动转 base64 内嵌（SVG 会被拒绝并告警） |

完整语法与主题自定义见 `references/capabilities.md`。

### Step 4 — 转换并检查输出

转换结束后脚本会自动打印：解析引擎、主题、合规自检结果、字数与图表统计。
出现 `[错误]` 必须修；`[提醒]` 需要人判断（例如正文外链在公众号里通常不可点）。
需要零容忍时用 `--strict`，有硬错误就以非 0 退出。

### Step 5 — 粘贴发布

浏览器打开 → 全选复制 → 粘贴进公众号编辑器 → 上传封面 → 手机预览 → 发布。
粘贴后排版丢失的排查顺序见 `references/troubleshooting.md`。

## 能力与对应实现

| 能力 | 入口 |
|------|------|
| 四套主题 + 自定义配色 | `scripts/themes.py`，`--theme` / `--theme-file x.json` |
| 中文排版（中英间距、标点、省略号） | `scripts/typography.py`，`--no-typo` 关闭 |
| 零依赖 Markdown 解析 | `scripts/md_lite.py`，`--engine lite` 强制 |
| 合规自检 | `scripts/wechat_check.py`，也可单独跑：`python scripts/wechat_check.py out.html` |
| 数学公式 → PNG 内嵌 | `scripts/math_render.py`，`--math auto\|on\|off` 控制 |
| 批量转换 | `--batch`，附带 index.html 索引页 |
| 多格式输出 | `--format wechat \| text \| markdown` |

## 依赖策略（与常见做法不同）

- `.md` 输入：**零依赖也能跑**。有 `markdown` + `beautifulsoup4` 时走库路径，缺失时自动回退到内置的
  `md_lite` 解析器。两条路径对同一输入的产出**字节一致**（selftest 有断言）。
- `.docx` 输入：需要 `python-docx`（`pip install python-docx`）。
- `.html` 输入：需要 `beautifulsoup4`。
- 数学公式（可选）：需要 `matplotlib`（用自带的 mathtext，**不需要本机装 LaTeX**）。
  缺失时公式降级为红字等宽文本并输出告警，转换本身不受影响。
- **不会自动 pip install**。starter kit 的做法是在首次运行时静默安装依赖，
  这会修改用户环境；改为"能降级就降级，不能降级就给出可操作的安装提示"。

## Edge Cases

| 情况 | 处理 |
|------|------|
| 空文件 / 无内容 | 输出空正文，合规自检通过，统计显示 0 字 |
| 只有标题没有正文的 callout | 渲染成一个只有标题的高亮框 |
| 两个相邻引用块之间没空行 | 会被合并成一个块（两条引擎行为一致），callout 之间务必空一行 |
| 嵌套列表缩进 2 空格 | 零依赖引擎支持；markdown 库遵循 CommonMark 需要 4 空格，写 4 空格最稳 |
| 图片是 SVG | 拒绝内嵌并告警（公众号保存时会丢失 SVG） |
| 公式环境缺 matplotlib | 公式降级为红字等宽文本保留原文，并输出"数学公式降级为文本"告警 |
| 代码块 / 行内代码里出现 `$` | 不做公式解析（防止 `$PATH`、"$5" 被误伤） |
| 图片超过 10MB | 告警提示压缩 |
| 正文含外部链接 | 告警：公众号正文通常不允许跳外链，建议放"阅读原文" |
| 非 UTF-8 编码 | 按 UTF-8 读取并容错替换，不崩 |

## Resources

- `references/wechat_restrictions.md` — 公众号 HTML 限制规则（在 starter 基础上补充了实测项）
- `references/wechat_styles.md` — 各主题 inline CSS 取值
- `references/capabilities.md` — 新增能力的语法与自定义方法
- `references/troubleshooting.md` — 粘贴后排版丢失的排查清单
- `assets/article_template.md` — 带 front-matter 与各类语法的文章模板
- `examples/` — 输入样例与生成结果
