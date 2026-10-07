# 公众号 HTML 限制规则

在 starter kit 同名文件的基础上，补充了本次实测与踩坑得到的条目（标注【实测】）。

## 允许使用的标签

```
p, h2, h3, h4, ul, ol, li, span, img, a, table, thead, tbody, tr, th, td, br
```

`<h1>` 保留给文章标题字段，正文里的 h1 会被丢弃或降级——转换器统一降为 h2。

## 禁止/会掉排版的标签

| 标签 | 后果 | 处理 |
|------|------|------|
| `<h1>` | 被占用 | 降级为 `<h2>` |
| `<div>` | 渲染不稳定 | 转为 `<p>` |
| `<script>` | 一律剥离 | 删除 |
| `<style>` | CSS 必须 inline | 删除，样式改写到 `style=""` |
| `<iframe>` | 外部嵌入禁止 | 删除或转成链接 |
| `<svg>` | 保存时消失 | 删除；矢量图请导出 PNG |
| `<video>` / `<audio>` | 必须用公众号自己的组件 | 删除或转链接 |
| `<pre>` / `<code>` | 【实测】会被压成一行 | 用 `<p>` + `white-space` + `&nbsp;` 保留缩进 |

## 属性限制

| 属性 | 说明 |
|------|------|
| `class` | 不支持，会被剥离 |
| `id` | 不支持（因此正文内无法做锚点跳转，目录只能是纯文本） |
| `onclick` 等事件 | 禁止 |

## CSS 规则

- **必须 inline**：每个元素自带 `style="..."`
- 可用属性：
  ```
  color, background-color, font-size, font-weight, font-style, font-family,
  line-height, letter-spacing, text-align, text-decoration, text-indent,
  margin*, padding*, border*, border-collapse, border-radius,
  display, vertical-align, max-width, width, white-space, word-break
  ```
- 不可用：`position`、`float`、`flex`、`grid`、`animation`、`transition`、
  `@media` 查询、`@font-face` 自定义字体
- 【实测】`height` 在多数模板里无效，图片只设 `max-width: 100%` 即可保持比例

## 图片规则

| 方式 | 结果 |
|------|------|
| `https://` 外链 | 可能显示，也可能被拦截；建议替换 |
| `data:image/png;base64,...` | ✅ 粘贴时公众号自动转存到自己的 CDN |
| `data:image/svg+xml;base64,...` | ❌ 保存后消失 |
| 单图大小 | ≤ 10MB |
| 单篇图片数 | ≤ 100 张 |

## 正文长度与外链

- 正文上限约 20,000 字（超出会被截断）
- 【实测】正文里的外部超链接通常无法跳转（除白名单与公众号文章链接），
  建议把链接放到「阅读原文」或文末"参考资料"里写成纯文本

## 常见翻车现场

1. **粘贴后样式全丢** —— 八成用了 `<style>` 或 `class`
2. **图片第二天裂了** —— 用了外链或 SVG
3. **代码块挤成一坨** —— 用了 `<pre>`，或换行没转成 `<br>` / `&nbsp;`
4. **手机上表格溢出** —— 公众号没有横向滚动，宽表要拆成两张或转成列表
5. **段间距忽大忽小** —— 公众号对 margin 的合并规则与浏览器不同，
   统一用 `margin: 12px 0` 这类显式写法
