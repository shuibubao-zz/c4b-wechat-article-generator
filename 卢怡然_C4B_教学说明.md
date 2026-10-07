# 教学说明：怎么装、怎么用这个公众号文章生成技能

## 零、30 秒速通

```bash
python scripts/convert_to_wechat.py 我的文章.md 我的文章.html
```

浏览器打开 `我的文章.html` → Ctrl+A → Ctrl+C → 粘贴到 mp.weixin.qq.com 编辑器 → 手机预览 → 发布。

就这样。下面是有更多需求时才需要看的部分。

---

## 一、安装

### 方式 A：直接用源码目录（推荐，改起来方便）

```bash
# 放到用户级技能目录（所有项目可用）
cp -r wechat-publisher ~/.workbuddy/skills/

# 或者放到某个项目里（只在这个项目可用）
cp -r wechat-publisher .workbuddy/skills/
```

### 方式 B：装打包好的 `.skill`

```bash
# .skill 本质是 zip，SKILL.md 在根目录
unzip 卢怡然_C4B_wechat-publisher.skill -d ~/.workbuddy/skills/wechat-publisher
```

### 依赖（大多数情况下可以不装）

| 输入格式 | 必需依赖 | 说明 |
|----------|----------|------|
| `.md` | **无** | 有 `markdown` + `beautifulsoup4` 时走库路径，没有就走内置解析器 |
| `.docx` | `python-docx` | `pip install python-docx` |
| `.html` | `beautifulsoup4` | `pip install beautifulsoup4` |
| 数学公式（可选） | `matplotlib` | 不装也能转换，公式降级为红字并告警 |

脚本**不会自动帮你装依赖**（那会悄悄改动你的环境）。缺依赖时会明确告诉你装什么。

想体验全部能力（推荐）：

```bash
pip install markdown beautifulsoup4 python-docx
```

---

## 二、作为 AI 技能使用

装好之后，直接对 AI 说人话就行，不需要记命令：

- "把这篇 Markdown 转成公众号文章"
- "帮我把 `report.docx` 排版成公众号可以粘贴的 HTML"
- "这个目录下所有文章都转成公众号格式"
- "换个蓝色主题再生成一遍"

技能会自动被触发（触发条件写在 SKILL.md 的 `description` 里）。
想让 AI 按你的意思做，就在话里带上：主题、要不要目录、作者名。

---

## 三、命令行用法

### 基本

```bash
python scripts/convert_to_wechat.py 输入.md 输出.html
```

### 常用参数

| 参数 | 作用 |
|------|------|
| `--theme default\|accent\|warm\|minimal` | 换配色 |
| `--theme-file my.json` | 用 JSON 覆盖任意样式 |
| `--toc` | 生成目录 |
| `--author 名字` | 页脚与元信息里的作者 |
| `--no-footer` | 不要页脚版权 |
| `--no-typo` | 关闭中文排版优化 |
| `--no-embed` | 不要把本地图片转成 base64 |
| `--format wechat\|text\|markdown` | 输出公众号 HTML / 纯文本 / 知乎用 Markdown |
| `--math auto\|on\|off` | 数学公式渲染（auto=有 matplotlib 就渲染，off=强制关闭） |
| `--batch` | 输入是目录，批量转换 |
| `--strict` | 合规自检有硬错误就报错退出 |
| `--report r.json` | 把转换与自检结果写成 JSON |
| `--fragment` | 只输出正文片段（不套预览外壳） |
| `--engine auto\|markdown\|lite` | 强制指定解析引擎 |

### 例子

```bash
# 技术文：蓝色主题 + 目录
python scripts/convert_to_wechat.py 教程.md out.html --theme accent --toc

# 一个目录全转
python scripts/convert_to_wechat.py ./articles ./out --batch

# 只想要纯文本（比如做字数统计或发邮件）
python scripts/convert_to_wechat.py 文章.md 文章.txt --format text

# 单独检查一份 HTML 合不合规
python scripts/wechat_check.py out.html
```

---

## 四、写一篇能被正确转换的文章

### 文章开头写 front-matter（可选）

```markdown
---
title: 文章标题
author: 卢怡然
date: 2026-10-06
abstract: 一句话摘要
theme: accent
toc: true
---
```

不写也能用：标题会取文档里第一个 `# 一级标题`。

### 正文里能用的增强语法

```markdown
> [!NOTE] 知识点标题
> 框里的正文。

:::warning 易错点
围栏写法，适合放多段落。
:::

==这句会被高亮==，**加粗**，`行内代码`

行内公式 $S_{b64} \approx \frac{4}{3} S_{bin}$ 和行间公式：

$$S_{b64} \approx \frac{4}{3} S_{bin}$$

（有 matplotlib 时渲染成 200 DPI 白底 PNG 内嵌——公众号唯一能活的公式方案；
没有时降级为红字文本并告警。代码块/行内代码里的 `$` 不会被当成公式。）

![本地图片会转 base64](img.png)
```

callout 类型：`note`(📘) / `tip`(💡) / `practice`(🔧) / `warning`(⚠️) / `quote`(💬)。
中文写法（知识/技巧/实践/注意）也能识别。

> ⚠️ 两个引用块之间**必须空一行**，否则会被合并成一个块。

### 建议的写作顺序

1. 先按 Markdown 正常写，不要管排版
2. 跑一次转换，看统计与自检输出
3. 用浏览器看效果，不满意就换主题或改 `--theme-file`
4. **一定要用手机预览**再发布

---

## 五、常见问题

**Q：转换时报"找不到图片"？**
图片路径是相对 `.md` 文件所在目录解析的。把图片放到文章同目录下，或改成绝对路径。

**Q：SVG 图片被跳过了？**
故意的。公众号保存时会丢弃 SVG，所以转换器拒绝内嵌并提示你先转 PNG。

**Q：粘贴到公众号后样式还是丢了？**
先跑 `python scripts/wechat_check.py 输出.html`。如果它说合规通过，
再对照 `references/troubleshooting.md` 的现象表排查——多数情况是编辑器本身的行为差异。

**Q：目录点了不跳转？**
正常。公众号不支持页内锚点（`id` 会被剥离），目录只是纯文本索引。

**Q：正文里的链接点不动？**
公众号正文通常不允许跳外部域名。把链接放「阅读原文」，参考资料写成纯文本。

**Q：想改配色但不想改代码？**
写个 JSON 传给 `--theme-file`，可覆盖的键见 `references/wechat_styles.md`。

---

## 六、验证这个技能真的能用

```bash
python scripts/selftest.py
```

会跑 20 项能力测试（主题、排版、双引擎一致、合规、callout、目录、图片、批量、
公式渲染/降级、公式双引擎一致、代码区 `$` 不误伤、`--math off`……），
全部通过会显示 `自检结果：20/20 通过`。
这份输出在 `evidence/selftest_20项.txt` 里有留档（第一轮 16 项的留档也保留为 `selftest_16项.txt`）。
