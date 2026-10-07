---
name: wechat-publisher
description: >
  Convert Markdown or Word documents into WeChat Official Account (微信公众号)
  compatible HTML that can be copy-pasted directly into the WeChat editor.
  Applies inline CSS styling, sanitizes forbidden HTML elements, and produces
  mobile-friendly article formatting.
  Use whenever the user says "convert to WeChat", "公众号文章", "微信公众号格式",
  "转换成公众号", "make WeChat article", "generate WeChat HTML",
  or provides a .md or .docx file and asks to format it for WeChat publishing.
  Also trigger when the user mentions publishing an article to WeChat Official Account.
---

# WeChat Publisher — Markdown/Word → 公众号 HTML

## Purpose

Convert a Markdown (.md) or Word (.docx) document into copy-paste-ready HTML
for WeChat Official Account publishing. Think of it as a "print driver" for
WeChat — you give it your content, it gives you formatted HTML that survives
WeChat's strict editor rules.

## Quick Start

```bash
python scripts/convert_to_wechat.py input.md output.html
```

Then: open `output.html` in browser → Ctrl+A → Ctrl+C → paste into WeChat editor.

## Supported Input Formats

| Format | How It's Handled |
|--------|-----------------|
| Markdown (.md) | Converted via `markdown` library with tables, fenced code, footnotes |
| Word (.docx) | Extracted via `python-docx` — headings, paragraphs, bold/italic preserved |

## WeChat HTML Restrictions

WeChat's editor is strict. The converter enforces these rules automatically:

### Allowed Tags
`p, h2, h3, ul, ol, li, span, img, a, table, tr, th, td, br`

### Forbidden (auto-removed or converted)
| Forbidden | Converted To |
|-----------|-------------|
| `<h1>` | `<h2>` |
| `<div>` | `<p>` |
| `<script>` | removed |
| `<style>` | removed |
| `<iframe>` | removed |
| `class="..."` | removed |
| `id="..."` | removed |

### CSS Rule
**Inline styles only.** Every element must carry its own `style="..."` attribute.
No `<style>` blocks, no external CSS. See `references/wechat_styles.md` for values.

## Workflow

### Step 1 — Read Source

Detect file format (.md or .docx) and convert to raw HTML.

### Step 2 — Sanitize

Apply WeChat restrictions:
- Remove forbidden tags (`<script>`, `<style>`, `<iframe>`)
- Convert `<h1>` → `<h2>`, `<div>` → `<p>`
- Handle code blocks → styled `<p>` with monospace
- Handle blockquotes → styled `<p>` with left border
- Convert `<strong>` → `<span style="font-weight:bold">`
- Convert `<em>` → `<span style="font-style:italic">`

### Step 3 — Apply Styles

Apply default inline CSS from `references/wechat_styles.md`:
- Headings: 22px bold (h2), 18px bold (h3)
- Body: 16px, line-height 1.75, color #333
- Code: background #f6f8fa, monospace
- Tables: border-collapse, alternating header
- Links: blue, underlined

### Step 4 — Clean & Output

Remove remaining class/id attributes, filter non-allowed CSS properties,
output final HTML ready for pasting.

## Dependencies

```bash
pip install markdown beautifulsoup4 python-docx lxml --break-system-packages
```

## Usage Examples

### Convert a Markdown article
```bash
python scripts/convert_to_wechat.py my_article.md wechat_output.html
```

### Convert a Word document
```bash
python scripts/convert_to_wechat.py report.docx wechat_report.html
```

### Publishing workflow
```
1. Write content in Markdown (use AI to help)
2. Run converter: python scripts/convert_to_wechat.py article.md output.html
3. Open output.html in browser
4. Ctrl+A → Ctrl+C
5. Go to WeChat Official Account editor (mp.weixin.qq.com)
6. Ctrl+V paste into the editor
7. Upload images to WeChat media library if needed
8. Preview on phone → adjust → publish
```

## What This Starter Kit Does NOT Do (Yet)

These are opportunities for YOU to add:

- ❌ Multiple themes / color schemes
- ❌ Math formula rendering (LaTeX → PNG)
- ❌ Callout / highlight boxes (📘 知识点、⚠️ 注意)
- ❌ Auto-generated table of contents
- ❌ Article metadata (author, date, abstract)
- ❌ Footer / copyright notice
- ❌ Chinese typography optimization (spacing, punctuation)
- ❌ Image handling (local images → base64 embedding)

**Your mission: use skill-creator to add at least 2 of these capabilities.**

## Edge Cases

| Situation | Handling |
|-----------|----------|
| Empty file | Report error, don't generate empty HTML |
| Very long article (>10000 words) | Works, but warn about WeChat's article length limits |
| Non-UTF-8 encoding | Try UTF-8 first, fall back to GBK |
| Missing dependencies | Auto-install on first run |
| Images with external URLs | Keep as-is, warn user to upload to WeChat CDN |
| Tables wider than mobile screen | Current: no special handling. Opportunity: add horizontal scroll |
