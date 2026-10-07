# 样式参考（inline CSS 取值）

## 通用排版原则（沿用 starter，做了加强）

- 正文 **16px** —— 低于 16px 在手机上明显吃力
- 行高 **1.75** —— 中文的舒适值
- 正文色 **#333** 而非纯黑，长时间阅读更柔和
- 标题与正文之间留 26px，段落之间 12px
- 图片一律 `max-width: 100%`

## 基础样式键（可被主题/--theme-file 覆盖）

| 键 | 默认值要点 |
|------|-----------|
| `h2` | 22px bold，#1f2328，margin 26px 0 12px |
| `h3` | 18px bold，#1f2328，margin 18px 0 8px |
| `h4` | 16px bold，#444 |
| `p` | 16px / 1.75 / #333 / margin 12px 0 |
| `li` | 16px / 1.75 / margin 6px 0 |
| `ul` `ol` | margin 12px 0，padding-left 22px |
| `code_inline` | 灰底 #f2f4f7，红字 #c0341d，14px |
| `code_block` | 灰底 #f6f8fa，14px，1.65，padding 14px 16px |
| `blockquote` | 浅灰底 #f7f8fa，左边框 4px #d0d7de |
| `table` / `th` / `td` | border-collapse，1px #d0d7de，cell padding 8px 10px |
| `a` | #0366d6，下划线 |
| `img` | max-width 100%，margin 14px 0 |
| `hr` | 居中 `· · ·`（公众号对 `<hr>` 支持不稳定，用字符代替） |
| `meta_title` | 24px bold |
| `meta_info` | 13px #9a9a9a（作者·日期·阅读时长） |
| `meta_abstract` | 14px #666，浅灰底摘要框 |
| `toc_title` / `toc_h2` / `toc_h3` | 目录三级 |
| `footer` | 13px #9a9a9a，浅灰底 |
| `strong` / `em` / `del` / `mark` | 加粗 / 斜体 / 删除线 / 荧光高亮 |

## 主题差异

| 主题 | h2 色 | 引用块 | 链接色 |
|------|-------|--------|--------|
| `default` | #1f2328 | #f7f8fa / #d0d7de | #0366d6 |
| `accent` | #1a73e8 | #f0f7ff / #1a73e8 | #1a73e8 |
| `warm` | #e65100 | #fff8e1 / #ff9800 | #e65100 |
| `minimal` | #333 | #fafafa / #999 | #0366d6 |

## callout 配色

| 类型 | 主色 | 底色 |
|------|------|------|
| note | #3b82f6 | #f0f7ff |
| tip | #0ea5e9 | #e8f8ff |
| practice | #10b981 | #eafaf3 |
| warning | #f59e0b | #fff8e6 |
| quote | #8b5cf6 | #f5f3ff |

callout 的几何样式（让多段看起来像一个整体盒子）：

```
首段：padding 14px 14px 6px 14px; margin 18px 0 0 0;
中段：padding 0 14px; margin 0;
尾段：padding 0 14px 14px 14px; margin 0 0 18px 0;
```

因为公众号不支持 `<div>` 容器，只能用"多个 `<p>` 拼一个盒子"的办法。

## 自定义示例（--theme-file）

```json
{
  "h2": "font-size: 21px; font-weight: bold; color: #0f766e; margin: 26px 0 12px 0;",
  "meta_abstract": "font-size: 14px; color: #556; background-color: #f0fdfa; padding: 12px 14px; margin: 0 0 20px 0;",
  "a": "color: #0f766e; text-decoration: underline;"
}
```
