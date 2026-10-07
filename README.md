# C4B：公众号文章生成技能（wechat-publisher）

把 Markdown / Word 变成**可直接粘贴进公众号编辑器**的 HTML：inline CSS、标签合规、
中文排版优化，转换完自动做一次合规自检。

> 作者：卢怡然 ｜ 2026-10-06 首版 / 2026-10-07 补公式与发布 ｜ 基座：官方 `c4b-wechat-publisher-starter`
> （SHA-256 `6d42f43bfee8f90c…`，与资料包清单一致）
>
> **在线预览**：https://wechat-article-layout-38529.app.workbuddy.host/
> （文章 HTML 的真实网页发布，可点开复核）

---

## 一句话跑通

```bash
python wechat-publisher/scripts/convert_to_wechat.py 我的文章.md 我的文章.html
# 浏览器打开 → Ctrl+A → Ctrl+C → 粘贴到 mp.weixin.qq.com
```

---

## 本包有什么

```
C4B/
├── 卢怡然_C4B_wechat-publisher.skill   ← 打包好的技能（zip，SKILL.md 在根）
├── 卢怡然_C4B_文章源文件.md             ← 真实文章的 Markdown 源（4742 字，7 个坑）
├── 卢怡然_C4B_output.html              ← 技能生成的公众号 HTML（含公式 PNG，合规自检通过）
├── 卢怡然_C4B_文章链接.md               ← 发布状态（网页版已发 + 公众号未发诚实标注）+ 传播设计 + 数据追踪表
├── 卢怡然_C4B_教学说明.md               ← 怎么装、怎么用
├── 卢怡然_C4B_拿来说明.md               ← 从 starter 拿了什么、改了什么、为什么
├── 卢怡然_C4B_AI日志.md                 ← skill-creator 使用过程 + 7 轮 eval 迭代
├── 卢怡然_C4B_AAR.md                   ← 复盘（含 5 个失败）
├── README.md
├── site/                               ← 线上预览页源（index.html = output.html）
├── wechat-publisher/                   ← 技能源码（可改可跑）
│   ├── SKILL.md
│   ├── scripts/  convert_to_wechat.py · md_lite.py · themes.py
│   │             typography.py · wechat_check.py · selftest.py · math_render.py
│   ├── references/  wechat_restrictions.md · wechat_styles.md
│   │                capabilities.md · troubleshooting.md
│   ├── assets/     article_template.md
│   └── examples/   sample_article.md · sample_output.html
├── _starter/                           ← starter kit 原样（对照用，未修改）
└── evidence/                           ← 实测留档
    ├── selftest_16项.txt               第一轮 eval 全量输出 16/16（历史）
    ├── selftest_20项.txt               最终 eval 全量输出 20/20（含公式 4 项）
    ├── baseline_vs_custom.txt          与 starter 基线的量化对照
    ├── baseline_starter_output.html    starter 原版输出
    ├── mine_same_input.html            定制版（库路径）
    ├── mine_zero_dep.html              定制版（零依赖路径，与上一份字节一致）
    ├── article_convert_report.json     真实文章的转换与自检报告
    └── skill安装验证.txt               解包副本上独立运行的验证
```

### 对应挑战的必交文件

| 挑战要求 | 本包文件 |
|----------|----------|
| 定制后的技能包 | `卢怡然_C4B_wechat-publisher.skill` + `wechat-publisher/` |
| 公众号文章链接 | `卢怡然_C4B_文章链接.md`（**网页版已发布**；公众号后台发布需本人账号，如实标注） |
| 文章源文件 | `卢怡然_C4B_文章源文件.md` |
| 转换后的 HTML | `卢怡然_C4B_output.html` |
| 教学说明 | `卢怡然_C4B_教学说明.md` |
| ⚡ AI 日志 | `卢怡然_C4B_AI日志.md` |
| 拿来说明 | `卢怡然_C4B_拿来说明.md` |

---

## 相对 starter 新增的能力

| 能力 | starter | 现在 |
|------|---------|------|
| 主题/配色系统 | ❌ | ✅ 4 套 + JSON 自定义 |
| callout 高亮框 | ❌ | ✅ 5 种语义框，两种写法 |
| 自动目录 | ❌ | ✅ |
| 文章元数据 | ❌ | ✅ 标题/作者/日期/摘要 |
| 页脚版权 | ❌ | ✅ |
| 中文排版优化 | ⚠️ 基础 | ✅ 中英间距 / 标点 / 省略号 |
| 图片处理 | ⚠️ 只保留标签 | ✅ 本地图转 base64、SVG 拒绝、超限告警 |
| 批量转换 | ❌ | ✅ 目录批量 + 索引页 |
| 多格式输出 | ❌ | ✅ HTML / 纯文本 / 知乎 Markdown |
| 输出合规自检 | ❌ | ✅ 每次转换自动跑 |
| 零依赖降级 | ❌ | ✅ 装不上 markdown/bs4 也能跑 |
| 数学公式 | ❌ | ✅ `$…$`/`$$…$$` → mathtext 渲染 PNG 内嵌（缺渲染环境时降级为红字并告警） |

---

## 文章内容的深度体现在哪

`卢怡然_C4B_文章源文件.md`（4742 字）不是清单式罗列，每个坑都写成三层：

1. **现象** —— 在编辑器里看到的是什么（"样式像被抽走""图片隔天裂开"）
2. **原因** —— 平台为什么会这样（`<h1>` 被标题字段征用、SVG 无法被重新上传）
3. **解法** —— 给出可直接抄的 HTML 对照（❌ 会丢的写法 vs ✅ 能活的写法）

文章另外有两处不是"转载可得"的内容：

- **"三段式盒子"**：没有 `<div>` 时如何用三个 `<p>` 拼出完整的高亮卡片（带真实代码）
- **可复核的实测数据**：双引擎字节一致、20 项 eval、与 starter 的量化对照，全部在 `evidence/` 里

以及一条明确观点：**真正的解法不是记住 7 条规则，而是把规则固化成会让机器报错的检查器**。

---

## 验证：怎么确认它真的能用

```bash
python wechat-publisher/scripts/selftest.py
# → 自检结果：20/20 通过
```

20 项覆盖：主题系统、中文排版、零依赖解析、**双引擎结构等价**、
4 主题输出合规、h1 降级、callout、目录、元数据与页脚、图片 base64、
图片异常告警、纯文本输出、批量转换、docx 缺依赖提示、检查器能抓坏 HTML、代码块缩进、
**数学公式渲染/降级、公式双引擎字节一致、代码区 `$` 不误伤、`--math off` 开关**。

关键实测（留档在 `evidence/`）：

| 实测 | 结果 |
|------|------|
| 与 starter 同一输入对比 | 定制版多出元数据/摘要/页脚；无 h1/div/class/id |
| 两条解析引擎路径 | 输出 **sha256 完全一致** `1e506b85cffe6993…` |
| 真实文章转换 | 4742 字 / 14 个 h2 / 1 张公式图 / 2 个表格，合规自检通过 |
| 解包副本独立运行 | selftest 20/20，转换结果与源目录一致 |
| 公式渲染 | matplotlib mathtext → 200 DPI PNG → base64 内嵌，白底防深色模式隐形 |

---

## 诚实标注（没做的部分）

1. **没有真实发布到公众号** —— 无账号，也没有伪造链接或截图。
   已做的是**网页版发布**：https://wechat-article-layout-38529.app.workbuddy.host/（真实可访问）。
   公众号后台发布按 `卢怡然_C4B_文章链接.md` 的 SOP 由本人执行，后台阅读数据依然没有。
2. **没有接公众号官方 API 自动发布** —— 需要认证服务号 + IP 白名单，个人订阅号拿不到。
3. **`.docx` 只处理了文本、标题、粗斜体和表格文本**，未处理合并单元格与内嵌图片。
4. **公式用 mathtext 而非完整 LaTeX** —— 常见行内/行间公式够用，但不支持完整 LaTeX 宏包；
   公式渲染为图片后不可复制、不可搜索（这是公众号平台的约束，不是本工具的选择）。

---

## 依赖

- `.md` 输入：**零依赖**即可（有 `markdown` + `beautifulsoup4` 时优先用库）
- `.docx` 输入：`pip install python-docx`
- `.html` 输入：`pip install beautifulsoup4`
- 数学公式（可选）：`pip install matplotlib`；缺失时公式降级为红字等宽文本并输出告警
- 脚本不会自动 pip install（starter 会，我改掉了——见拿来说明）
