# 新增能力速查（相对 starter kit）

## 1. 文章元数据（front-matter）

```markdown
---
title: 文章标题
author: 卢怡然
date: 2026-10-06
abstract: 一句话摘要
theme: accent
toc: true
copyright: 自定义页脚（不写则用默认原创声明）
---
```

解析不依赖 PyYAML（零依赖），只支持 `key: value` 一行一项。
渲染顺序：大标题 → 作者·日期·预计阅读时长 → 摘要框 → 目录 → 正文 → 页脚。

## 2. 主题系统

四套内置主题：

| 主题 | 观感 | 主色 |
|------|------|------|
| `default` | 石墨灰蓝，通用 | `#1f2328` 标题 / `#0366d6` 链接 |
| `accent` | 蓝色强调，技术文 | `#1a73e8` |
| `warm` | 暖橙，随笔/故事 | `#e65100` |
| `minimal` | 极简灰，克制 | `#333` |

自定义配色不需要改代码：

```bash
python scripts/convert_to_wechat.py a.md o.html --theme-file my.json
```

```json
{ "h2": "font-size: 22px; color: #0f766e; margin: 26px 0 12px 0;",
  "a": "color: #0f766e; text-decoration: underline;" }
```

JSON 里的键覆盖内置样式表，未覆盖的沿用主题默认值。可用键见 `wechat_styles.md`。

## 3. callout 高亮框

两种写法等价：

```markdown
> [!NOTE] 建议这样写
> 这里是框里的正文。

:::warning 别踩
围栏写法适合放多段落。
:::
```

| 类型 | 图标 | 默认标题 | 用途 |
|------|------|----------|------|
| `note` | 📘 | 知识点 | 概念解释 |
| `tip` | 💬→💡 | 小技巧 | 提效建议 |
| `practice` | 🔧 | 动手做 | 操作步骤 |
| `warning` | ⚠️ | 注意 | 易错点 |
| `quote` | 💬 | 引用 | 他人观点 |

别名：`IMPORTANT`/`CAUTION` → `warning`，中文写法（知识/技巧/注意/实践）同样可用。

**注意：两个引用块之间必须留一个空行**，否则会被合并成一个块。

## 4. 自动目录

`--toc` 或 front-matter `toc: true`，标题数 ≥ 2 时生成。
公众号不支持页内锚点，所以目录是纯文本编号列表（不跳转）。

## 5. 中文排版优化

默认开启，`--no-typo` 关闭。规则（保守，只作用于正文文本节点，不动代码与 URL）：

1. 中英文/中数字之间补一个半角空格：`第3节` → `第 3 节`
2. 中文后的半角 `!` `?` 转全角：`真的!` → `真的！`
3. `...` → `……`

## 6. 图片处理

| 情况 | 行为 |
|------|------|
| 本地 PNG/JPG/GIF/WEBP | 转 base64 内嵌（默认开启，`--no-embed` 关闭） |
| 本地 SVG | 拒绝内嵌并告警（公众号保存时会丢 SVG） |
| 外链图片 | 保留原 URL 并告警，建议改本地图或传公众号素材库 |
| 图片 > 10MB | 告警提示压缩 |
| 图片不存在 | 告警并保留原路径 |

## 7. 批量转换

```bash
python scripts/convert_to_wechat.py ./articles ./out --batch
```

输出目录里每篇一个 HTML，外加 `index.html` 索引页。

## 8. 多格式输出

`--format wechat`（默认）/ `text`（纯文本，用于字数统计或发邮件）/ `markdown`（去 front-matter，用于知乎等平台）。

## 9. 零依赖降级

`--engine auto`（默认）优先 `markdown` 库；缺失则用内置 `md_lite` 解析器。
两条路径对同一输入**字节一致**（`scripts/selftest.py` 里有断言）。

## 10. 合规自检

转换后自动执行，也可单独跑：`python scripts/wechat_check.py out.html`。
硬错误（div/h1/script/class/禁止的 CSS 属性）会让 `--strict` 以非 0 退出。

## 11. 数学公式（LaTeX 子集 → PNG 内嵌）

```markdown
行内：质能方程 $E = mc^2$ 写在句子里。
行间：
$$S_{b64} \approx \frac{4}{3} S_{bin}$$
```

- 渲染：matplotlib 自带 **mathtext**（不需要本机装 LaTeX），200 DPI **白底** PNG → base64 内嵌。
  白底是刻意的：透明底黑字在公众号**深色模式**下会隐形。
- 开关：`--math auto`（默认，有 matplotlib 就渲染）/ `on`（强制，缺环境则告警降级）/ `off`。
- 降级：缺 matplotlib 时公式保留为红字等宽文本，并输出"数学公式降级为文本"告警——**不假装支持**。
- 保护：代码块与行内代码里的 `$` 不做公式解析（`$PATH`、"$5" 不会被误伤）。
- 局限（诚实标注）：mathtext 只是 LaTeX 子集，不支持宏包与自定义宏；
  公式成图后不可复制、不可搜索——这是公众号平台的约束，不是本工具的选择。
