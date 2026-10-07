# 拿来说明：从 starter kit 拿了什么、改了什么、为什么

> 基座：`c4b-wechat-publisher-starter.zip`
> SHA-256：`6d42f43bfee8f90c4d682698979a568e912303988cdf79cd0090d879f34b35db`
> （与资料包 `README.md` 文件清单里的 `6d42f43bfee8f90c…` 一致，可复核）
> 基座原样保留在 `C4B/_starter/` 下，便于逐文件对照。

## 一、拿了什么（原样保留或增强后保留）

| 来自 starter | 我用它做了什么 |
|------|------|
| `scripts/convert_to_wechat.py` 的 5 步流水线（读取 → 清洗 → 上样式 → 清属性 → 外壳） | **保留流程顺序**，但把中间表示换成 IR（见下方"改了什么"） |
| `read_markdown()` 的扩展列表（extra / fenced_code / sane_lists） | 保留，但**去掉 `nl2br`**（原因见"改"第 2 条） |
| `read_docx()` 的 Word 标题映射与 run 级粗斜体 | 保留逻辑，改为直接产出 IR（不再绕一道 HTML） |
| `sanitize()` 的违规标签处理规则（h1→h2、div→p、script/style/iframe 删除） | **规则全部保留**，执行位置从"解析时"移到"渲染时"，这样样式可以跟主题联动 |
| `ALLOWED_TAGS` / `FORBIDDEN_TAGS` / `ALLOWED_CSS` 三张表 | 保留并扩展（补 h4、thead/tbody、SVG、video/audio 等），并拆成 `wechat_check.py` 里的可执行检查 |
| `references/wechat_styles.md` 的数值基线（16px 正文、1.75 行高、#333 不用纯黑） | **全部沿用**，只加强间距与层级 |
| `references/wechat_restrictions.md` | 保留，补充了 5 条实测条目（标注【实测】） |
| `examples/sample_article.md` | 原样保留为 `examples/sample_article_from_starter.md`，用作回归输入 |
| CLI 形态 `python convert_to_wechat.py 输入 输出` | **完全兼容**，老命令照跑 |

## 二、改了什么，以及为什么

### 改 1：样式从"写死的常量"改成"主题系统"

**原来**：`STYLES` 是一个写死在脚本里的字典，换配色要改代码。
**现在**：`scripts/themes.py` 里是「基础样式 + 主题覆盖层」，支持 `--theme` 与 `--theme-file xxx.json`。

理由：可复用性的关键不是"我能改"，而是"别人不改我的代码也能改"。把配色外置成 JSON，
别人换品牌色只需要写一个 3 行的文件。

### 改 2：去掉 `nl2br`，改为渲染时统一处理换行

`nl2br` 会把源码里的一次换行变成两个 `<br>`，而我自己写的零依赖解析器是一个换行对应一个 `<br>`。
两条路径输出不一致，就没法互相校验。**去掉 nl2br 后两条路径对同一输入产出字节一致**（见下方实测）。

### 改 3：新增零依赖 Markdown 解析路径

**原来**：`pip install markdown beautifulsoup4 python-docx lxml`，装不上就整个技能废掉；
而且脚本会在首次运行时**自动 pip install**（还会带 `--break-system-packages`）。
**现在**：内置 `scripts/md_lite.py`，`markdown` / `bs4` 缺失时自动降级，`.md` 输入零依赖也能跑完。
同时**删掉了自动安装依赖**——未经允许修改用户环境不是好行为，改为给出可操作提示。

### 改 4：从"HTML 洗 HTML"改成"IR → 渲染"

**原来**：markdown → HTML → BeautifulSoup 洗一遍 → 改标签 → 输出。
**现在**：任何输入都先转成统一中间表示（IR：heading / para / code / quote / list / table / hr），
再由渲染器按主题输出 HTML。

理由：这么做之后，双引擎等价性、纯文本输出、目录抽取、字数统计都变成对 IR 的一次遍历，
不必在 HTML 字符串上反复正则。也是我能让两条解析路径字节一致的前提。

### 改 5：把"限制规则"从文档变成可执行检查

starter 的 `wechat_restrictions.md` 写得对，但它只是一篇给人读的文档——
转换完能不能用，仍然要人粘贴进编辑器才知道。
新增 `scripts/wechat_check.py` 把这些规则形式化，每次转换后自动跑，`--strict` 可让硬错误直接失败。

### 改 6：新增数学公式渲染管线（2026-10-07）

**原来**：Markdown 里的 `$…$` 只能靠 MathJax/KaTeX 这类 `<script>` 方案——公众号会剥掉所有
`<script>`，公式粘贴即裸奔；SVG 输出还会在保存时消失。
**现在**：`scripts/math_render.py` 用 matplotlib 自带 mathtext 把公式渲染成 200 DPI 的**白底 PNG**
（白底是为了在公众号深色模式下不被吞掉），转 base64 内嵌；缺 matplotlib 时降级为红字等宽文本
并输出告警，不假装支持。转换器在 inline 清洗时**跳过 `<code>` 区域**再做公式解析，
防止命令行的 `$PATH`、价格 "$5" 被误伤。

理由：技术文发公式是刚需，而这是唯一能在公众号里活下来的方案；"能渲染"之外还必须
"在目标环境（含深色模式）里看得见"，这是我真渲染出来检查后改的一版。

## 三、新增了什么（starter 标注为"缺失/基础"的能力）

| 能力 | starter 状态 | 现在 | 入口 |
|------|-------------|------|------|
| 主题/配色系统 | ❌ 缺失 | ✅ 4 套 + JSON 自定义 | `themes.py` |
| callout 高亮框 | ❌ 缺失 | ✅ 5 种语义框，两种写法 | `> [!NOTE]` / `:::warning` |
| 自动目录 | ❌ 缺失 | ✅ | `--toc` / `toc: true` |
| 文章元数据 | ❌ 缺失 | ✅ 标题/作者/日期/摘要 | front-matter |
| 页脚版权 | ❌ 缺失 | ✅ 可自定义文案 | `--no-footer` 关闭 |
| 中文排版优化 | ⚠️ 基础 | ✅ 中英间距、标点、省略号 | `typography.py` |
| 图片处理 | ⚠️ 只保留标签 | ✅ 本地图转 base64、SVG 拒绝、超限告警 | `--no-embed` 关闭 |
| 批量转换 | ❌ 缺失 | ✅ 目录批量 + index.html | `--batch` |
| 多格式输出 | ❌ 缺失 | ✅ 公众号 HTML / 纯文本 / 知乎 Markdown | `--format` |
| 输出合规自检 | ❌ 缺失 | ✅ 每次转换自动跑 | `wechat_check.py` |
| 零依赖降级 | ❌ 缺失 | ✅ | `md_lite.py` |
| 数学公式 | ❌ 缺失 | ✅ `$…$`/`$$…$$` → mathtext 渲染 PNG 内嵌，代码区 `$` 不误伤 | `math_render.py` + `--math` |

## 四、实测对照（同一输入）

输入：starter 自带的 `examples/sample_article.md`

| 指标 | starter 基线 | 定制版（库路径） | 定制版（零依赖路径） |
|------|-------------|-----------------|---------------------|
| 输出字节 | 9,403 | 10,320 | 10,320 |
| 带 style 的元素 | 75 | 82 | 82 |
| h1 / div | 0 | 0 | 0 |
| class / id | 0 | 0 | 0 |
| 中英文空格处 | 28 | 30 | 30 |

两条引擎路径输出 **sha256 完全一致**：
`1e506b85cffe6993ae50f63c0dedc9c5a53baf75597d502d75cc43c151681d55`

定制版多出的字节来自元数据行、摘要框、页脚版权（starter 没有这三项）。
原始记录见 `evidence/baseline_vs_custom.txt`。

## 五、没做什么（诚实标注）

1. **公式用 mathtext 而非完整 LaTeX**：mathtext 只支持常用子集，不支持完整 LaTeX 宏包与自定义宏；
   渲染成图片后公式不可复制、不可搜索（平台约束）。复杂公式的现 workaround：先在别处导出 PNG 再插图。
2. **没有真实发布到公众号**（无账号；文章已通过**网页版**发布，链接见 `卢怡然_C4B_文章链接.md`）。
3. **没有接公众号官方 API 自动发布**。公众号的发布接口需要认证服务号 + 白名单 IP，
   个人订阅号拿不到；即使拿到，也不该把账号凭证交给脚本。
4. **starter 的 `.docx` 表格读取只处理了单元格文本**，没有处理合并单元格与图片。
