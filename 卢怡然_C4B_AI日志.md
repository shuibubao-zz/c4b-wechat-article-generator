# C4B AI 日志：用 skill-creator 做一个公众号文章生成技能

> 作者：卢怡然 ｜ 日期：2026-10-06
> 挑战要求：**必须使用 skill-creator** 来创建/迭代技能，且 AI 日志是评审必交项。
> 本文记录真实过程，包括跑不通的地方与改了几次。

---

## 一、起点：任务与硬约束

| 约束 | 来源 | 我的处理 |
|------|------|----------|
| 必须从 starter kit 出发 | CHALLENGE.md 拿来主义原则 | 保留 `C4B/_starter/` 原样，逐文件对照改造 |
| 必须使用 skill-creator | CHALLENGE.md AI-First 原则 | 走完整六步（见第二节） |
| 必须发布一篇真实文章 | Level 3 | **网页版已发布**（真实链接见第五节）；公众号后台发布需本人账号，未完成，如实标注（见 `卢怡然_C4B_文章链接.md`） |
| 评分维度 | 平台 `rubric.json` | 内容质量 25 / 传播设计 20 / 产物完整性 15 / AI 使用质量 20 / 复盘质量 20 |

一个必须先说清楚的偏差：CHALLENGE.md 写的是"文章质量 30% / 技能定制深度 25%"，
而随包的 `rubric.json` 是"内容质量 25 / 传播设计 20 / 产物完整性 15 / AI 20 / 复盘 20"。
**我按 rubric.json 准备**（它是平台机读的评分卡），同时兼顾 CHALLENGE.md 里"新增 ≥2 项能力"的要求。

---

## 二、skill-creator 六步流程实录

### Step 1 — Understanding the Skill with Concrete Examples（问清楚怎么用）

skill-creator 要求先用具体例子界定能力边界，不能直接开写。我向用户提了两个问题（这是真实提问，不是自问自答）：

1. **有没有可发布的公众号？** → 答：没有，如实标注未发布。
   这个答案直接决定了"传播设计 20 分"怎么拿：拿不到真实阅读数据，就转而交付发布 SOP + 数据追踪表。
2. **文章写什么主题？** → 答：公众号排版踩坑指南。
   这个答案决定了技能要先支持什么：技术文必须支持代码块、表格、callout，所以这三项排在最前面。

同时我自己列了 4 条"用户会怎么说"的触发语句，写进了 SKILL.md 的 `description`。

### Step 2 — Planning the Reusable Skill Contents（规划可复用内容）

按 skill-creator 的建议逐项判断该放 scripts / references / assets 哪一类：

| 内容 | 归类 | 理由 |
|------|------|------|
| 转换器、主题、排版、检查器、测试 | `scripts/` | 需要确定性、会反复执行 |
| 限制规则、样式取值、能力语法、排障清单 | `references/` | 让 SKILL.md 保持精简，按需加载 |
| 文章模板 | `assets/` | 直接被复制到输出里用 |

### Step 3 — Initializing the Skill（用官方脚本初始化）

```bash
python <skill-creator>/scripts/init_skill.py wechat-publisher --path C:/Users/卢怡然/Desktop/C4B
```

输出：`✅ Created SKILL.md / scripts/example.py / references/api_reference.md / assets/example_asset.txt`。
随后删掉了三个示例文件——它们只是模板占位，留着会让评审以为交付物是空的。

### Step 4 — Edit the Skill（实现）

按"先做可复用资源，再写 SKILL.md"的顺序：

1. `themes.py` 主题系统 → 2. `typography.py` 中文排版 → 3. `md_lite.py` 零依赖解析
→ 4. `wechat_check.py` 合规检查 → 5. `convert_to_wechat.py` 主流程 → 6. `selftest.py` eval
→ 7. 四份 references + 文章模板 + 样例 → 8. 最后写 SKILL.md（frontmatter 含 `agent_created: true`）

### Step 5 — Packaging（用官方脚本打包 + 校验）

```bash
python <skill-creator>/scripts/package_skill.py C:/Users/卢怡然/Desktop/C4B/wechat-publisher
```

官方脚本会先做校验（frontmatter、命名、结构、描述完整度），通过才打包。
**这一步真的报错了一次**：

```
❌ Validation failed: Description cannot contain angle brackets (< or >)
```

原因是我把 description 写成了 YAML 折叠标量 `description: >`，那个 `>` 被校验器判为尖括号。
改成 `description: |` 后通过（`✅ Skill is valid!`）。
这是"用官方工具"才有价值的地方——自己打包永远不会发现这个约定。
产物留档在 `evidence/官方打包器输出_wechat-publisher.zip`；
交付用的 `卢怡然_C4B_wechat-publisher.skill` 是 SKILL.md 在根的格式（便于直接解包到技能目录）。

### Step 6 — Iterate（按 eval 结果迭代）

`selftest.py` 就是 eval harness。首轮 **5/16**，最终 **20/20**。中间每一轮修的都是真问题，见下。

---

## 三、迭代轮次（eval 驱动的 6 轮修复）

| 轮次 | eval 结果 | 修了什么 | 性质 |
|------|-----------|----------|------|
| 初版 | 5/16 | `re.finditer` 的 Match 对象不能直接解包（写成了 `for a, b in finditer`），导致 11 个用例全崩 | 我的低级 bug |
| 2 轮 | 9/16 | 列表子节点用裸 list 存，导致遍历时 `KeyError: 'type'`；改为把子列表包装成完整 list 节点 | 设计教训：IR 里只保留一种节点类型 |
| 3 轮 | 12/16 | `:::warning` 围栏 markdown 库不认识 → 新增 `convert_callout_fences()` 把它改写成 `> [!WARNING]`；`[!NOTE]` 标记识别不支持多行 → 改成扫描块内所有段落并切分 | **真缺陷**（不跑双引擎对比发现不了） |
| 4 轮 | 14/16 | Python-Markdown 会把相邻两个引用块合并成一个 `<blockquote>`，callout 全部串味 → 改为块内扫描切分 | 真缺陷 |
| 5 轮 | 15/16 | 空引用块被输出成 `quote:plain` 占位；签名里 kind 大小写不一致 | 一致性 |
| 6 轮 | 16/16 | 合规检查把闭合标签也计进统计（h2 数翻倍） | 统计口径 |

2026-10-07 追加 **第 7 轮（公式 + 发布轮）**：eval 从 16 项扩到 **20 项**（新增 4 条公式用例），
全部通过。这一轮的动机、实现与两个新发现见第七节。

### 两个"不跑 eval 就发现不了"的发现

**发现 1：Python-Markdown 会合并相邻引用块。**
同一个 Markdown 文件里写两个 callout，中间只隔一个空行，Python-Markdown 会把它们合并成一个
`<blockquote>`，导致第二个 callout 变成第一个的正文。我原来的代码只检查块内第一段，于是"注意框"消失了。
修法是扫描块内所有段落，遇到 `[!KIND]` 就切分出新的 callout。

**发现 2：`nl2br` 让两条解析路径永远对不齐。**
starter 用了 `nl2br` 扩展，它会把源码里一次换行渲染成两个 `<br>`；
我写的零依赖解析器是一个换行一个 `<br>`。为了让"零依赖降级"这件事可信，
我必须让两条路径产出一致——去掉 `nl2br`，改在渲染时统一转换。
最终两条路径对同一输入的输出 **sha256 完全一致**（`1e506b85cffe6993…`）。

---

## 四、AI 用得好的地方 / 用得不好的地方

### 用得好的

1. **先问再写**。问"有没有公众号"不是走形式——它决定了 20 分维度的策略，
   也让我一开始就放弃"伪造发布截图"这条路。
2. **用断言代替"看着没问题"**。16 条 eval 里最有价值的不是"能跑"，
   而是"两条引擎字节一致"和"检查器能抓到坏 HTML"这两条互相验证的断言。
3. **保留基线做对照**。starter 的原版输出存在 `evidence/baseline_starter_output.html`，
   "我改了什么"因此是可量化的，不是自述。

### 用得不好的（失败记录）

1. **第一版把 `~~( ?P<dbody>.+?)~~` 写错了正则语法**（空格混进了组名），
   语法层面就直接报错，浪费一轮。教训：正则写长表达式时先单独跑一遍再嵌进大正则。
2. **最初想让 `selftest.py` 复用 starter 的 `read_docx`**，
   结果在无 python-docx 环境下直接抛 ImportError 堆栈而不是可操作提示。
   改成"捕获并给出 `pip install python-docx` 的明确提示"，并为此加了一条 eval。
3. **一度想让脚本自动 pip install**（starter 就是这么做的）。
   写到一半停手了：未经允许修改用户环境不是好行为。改成"能降级就降级，不能降级就给提示"。

---

## 五、2026-10-07 追加轮：发布与数学公式

### 6.1 传播设计补完：网页版发布

用户确认后，把 `卢怡然_C4B_output.html` 以静态页方式发布上线：
**https://wechat-article-layout-38529.app.workbuddy.host/**（真实可访问，`site/index.html` 为源）。
公众号后台发布仍需本人账号，`文章链接.md` 里按"是什么/不是什么"如实区分。

### 6.2 补齐数学公式（LaTeX → PNG）

当初"诚实标注没做"的能力，在装好 matplotlib 后补上了。方案与理由：

- **为什么必须是图片**：MathJax/KaTeX 依赖 `<script>`，公众号保存时全剥（文章坑 4）；
  SVG 输出也会消失（坑 5）。PNG + base64 内嵌是唯一活路。
- **为什么用 mathtext**：matplotlib 自带，**不需要本机装 LaTeX**；代价是只支持子集，常见公式够用。
- **实现**：`scripts/math_render.py`（渲染 + 缓存）；`md_lite.py` 的 tokenizer 增加 `$…$` / `$$…$$`，
  渲染成 `<img>`，**缺 matplotlib 时降级为红字等宽文本并写入告警——不假装支持**；
  `convert_to_wechat.py` 在 inline 清洗阶段**跳过 `<code>` 区域**再做公式替换
  （防止命令行 `$PATH` 被误伤），并用占位符延后插回（防止公式 `<img>` 被图片归一化覆盖样式）。
- **eval 扩项**：渲染/降级、双引擎字节一致、代码区 `$` 不误伤、`--math off`，16 → **20 项**。

### 6.3 这一轮抓到的两个真问题

1. **透明底公式图在深色模式会隐形。** 我先按习惯用透明 PNG + 黑字渲染，真渲染出来一看：
   深色背景上几乎看不见。公众号有深色模式，黑字透明图会被吞掉。改为**白底深字**
   （白底在白色正文里无缝，深色模式下也不会消失）。
   教训：**"能渲染出来"和"在目标环境里看得见"是两回事，必须真的看一眼产物。**
2. **自家检查器抓到了自家输出。** 第一次转换后合规自检报 `[错误] 违规 CSS 属性 height`——
   来源是我给公式 `<img>` 写的 `height:auto`。img 只约束 `max-width` 时浏览器本就保持纵横比，
   删掉即可。这正是文章里"把规则固化成检查器"的价值：**写检查器的人第一个救的是自己。**

---

## 六、时间与证据

| 时间 | 动作 | 产出 |
|------|------|------|
| 20:34 | 读挑战资料、解压 starter（校验 SHA-256 与官方清单一致） | `C4B/_starter/` |
| 20:40 | 用 skill-creator 初始化骨架 | `wechat-publisher/` |
| 20:41–21:00 | 实现 6 个模块 + 4 份 references | `scripts/*.py` |
| 21:00–21:10 | 6 轮 eval 迭代 5/16 → 16/16 | `evidence/selftest_16项.txt` |
| 21:10 | starter 基线 vs 定制版对照、屏蔽依赖跑零依赖路径 | `evidence/baseline_vs_custom.txt` |
| 21:15 | 写文章源文件并转换 | `卢怡然_C4B_output.html`（4125 字，合规通过） |
| 次日 | 用户确认后发布网页版文章页 | **https://wechat-article-layout-38529.app.workbuddy.host/** |
| 次日 | 装环境、写 `math_render.py`、改造 `md_lite.py` / `convert_to_wechat.py`、eval 扩到 20 项 | `scripts/math_render.py`、`evidence/selftest_20项.txt` |
| 次日 | 真渲染验证发现透明底隐患 → 改白底；自家检查器抓到 `height:auto` → 修复后重转换 | `卢怡然_C4B_output.html`（4742 字 / 1 图，合规通过） |

**证据文件**

| 文件 | 内容 |
|------|------|
| `evidence/selftest_16项.txt` | 第一轮 eval 全量输出（16/16，历史） |
| `evidence/selftest_20项.txt` | 最终 eval 全量输出（20/20，含公式 4 项） |
| `evidence/baseline_vs_custom.txt` | 与 starter 基线的量化对照 + 双引擎 sha256 |
| `evidence/baseline_starter_output.html` | starter 原版输出（未经修改） |
| `evidence/mine_same_input.html` / `mine_zero_dep.html` | 定制版两条路径输出（字节一致） |
| `evidence/article_convert_report.json` | 真实文章的转换与自检报告（4742 字 / 1 图） |
| `evidence/skill安装验证.txt` | 解包副本上独立运行验证 |
| `evidence/submit_guard_audit.txt` | 提交前体检报告（交付物核对 / 命名 / 红线 / 五维粗估；工具自述为机器粗估，非官方评分） |
| `evidence/审计说明_命名与空文件.md` | 对体检报告两个自指假异常的说明（命名规范适用对象、「有深度」信号震荡） |
| `evidence/官方打包器输出_wechat-publisher.zip` | 官方打包器重打的技能包（17 个条目，含全部 `scripts/`） |
| 线上链接 | https://wechat-article-layout-38529.app.workbuddy.host/ |
