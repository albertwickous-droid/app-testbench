# 发布文案工具包 / Launch Copy Kit

发布前替换：

- `[REPO_URL]`：GitHub 仓库地址
- `[RELEASE_URL]`：v0.1.1 Release 地址
- `[DATE]`：发布日期

所有数字以 `README.md`、`docs/validation.md` 和 GitHub Release notes 为准。公开截图只使用 `docs/assets/cases/` 下已审计的真实 MuMu 运行图。

## 1. 一句话介绍 / One-line pitch

**中文**

> 用成熟 MuMu 运行时跑可重复的 Android App 测试：一条 YAML 串起安装、启动、交互、断言、截图和 logcat，结束时生成离线 HTML 报告。

**English**

> Run repeatable Android app tests on the mature MuMu runtime: one YAML flow for install, launch, actions, assertions, screenshots, and logcat, followed by an offline HTML evidence report.

**传播版**

- **AI 可以写测试，但测试环境不能靠猜。**
- **真 App、真冷启动、真断言。**
- **不只是能点：失败时把截图、UI 树和 logcat 一起交出来。**
- **A mature MuMu runtime. Repeatable app tests. Evidence you can hand off.**

## 2. GitHub Release 开头 / GitHub Release lead

```markdown
# App TestBench v0.1.1 — Real App Tests, Retained Evidence

**简体中文 | English**

App TestBench v0.1.1 用两条真实、成熟的开源 Android App 流程验证执行层：创建内容、强制停止、冷启动、重新打开并断言状态仍存在。

v0.1.1 validates the execution layer against two mature open-source Android apps: create real data, force-stop, cold-launch, reopen, and assert that state survived.

> AI 可以写测试，但测试环境不能靠猜。
> AI can write the test. It should not guess the test environment.

- AnkiDroid 2.25.3: **49/49** steps passed in **75.203 s**.
- Markor 2026.10.0: **46/46** steps passed in **80.203 s**.
- Failed `run --json`: exit `1`, structured `error`, complete `data`, packaged `cli-v1.schema.json` PASS.
- Runtime for both live cases: MuMu Player `6.8.8.0`, Android 12, ADB `1.0.41`, `720x1280`, Simplified Chinese.

Repository: [REPO_URL]
Release: [RELEASE_URL]
Live cases: [REPO_URL]/blob/main/docs/cases.md
Validation: [REPO_URL]/blob/main/docs/validation.md
```

## 3. Pinned discussion / 置顶讨论

```markdown
# Welcome to App TestBench — start here / 从这里开始

App TestBench is a Windows CLI for Android app testing through MuMu Player, MuMuManager, and ADB. It is built for repeatable flows and evidence you can inspect after a failure.

Recommended first steps:

1. Install from source or from the wheel attached to the GitHub Release.
2. Run `app-testbench doctor --json`.
3. Reproduce one live case:
   - `examples/ankidroid-deck-persistence/run.ps1`
   - `examples/markor-note-persistence/run.ps1`
4. Report the MuMu version, Windows/Python version, failing step, and whether the case is reproducible.

Do not post tokens, cookies, real account screenshots, unfiltered logcat, UI XML, private package names, or local paths. Security issues should use Private Vulnerability Reporting.
```


## 4. V2EX「分享创造」

**标题**

```text
AI 可以写测试，但测试环境不能靠猜：我把 App 自动化跑在成熟 MuMu 上
```

**正文**

```markdown
最近更新了 app-testbench v0.1.1。它不是一个“让模型看截图随便点”的演示，而是把 MuMu Player、MuMuManager 和 ADB 包成一个可重复的 Android App 测试执行层。

一条 JSON/YAML flow 可以写清安装、启动、点击、输入、等待和断言。跑完后会留下步骤耗时、截图、UI 树、logcat、结构化 JSON 和离线 HTML 报告。失败时退出码仍然是 1，但现场不会只剩一行错误。

这次没有拿空壳 App 做展示，而是跑了两条真实开源 App：

- AnkiDroid 2.25.3：首次引导、创建牌组和问答卡片、强制停止、冷启动、重新打开卡片验证内容，49/49 步通过。
- Markor 2026.10.0：完成引导、创建 Markdown 笔记、保存、冷启动、按文件名搜索并重新打开正文，46/46 步通过。

为什么强调 MuMu？因为测试需要的是稳定、可管理的运行后端，而不是每次让 AI 临时拼一套环境。MuMu 负责成熟运行时，App TestBench 负责流程、断言和证据，AI 可以帮忙写 flow 和分析失败，但不负责决定测试是否通过。

项目也适用于 Web 端功能不全、但组织拥有原生 App 和专用测试账号的业务场景。边界很明确：只用于你有权测试的系统、应用、账号和设备，不提供登录绕过、验证码破解、反爬或风控规避。

Windows + MuMu + ADB，MIT License，本地优先，无遥测。

仓库：[REPO_URL]
Release：[RELEASE_URL]

我是项目维护者，欢迎拿真实 MuMu 环境复现后提 issue。
```

## 5. Reddit / Show HN

**Title**

```text
Show HN: App TestBench – repeatable Android app tests on the MuMu runtime
```

**Body**

```text
I built App TestBench after repeatedly running into the same problem: ADB scripts could send taps, but when something failed I had no clean record of the screen, UI tree, logs, step timing, or app state after a restart.

App TestBench is a Windows CLI around MuMuManager and ADB. JSON/YAML flows describe install, launch, waits, selectors, input, assertions, screenshots, UI dumps, and logcat. A run produces result.json, optional JUnit XML, and a self-contained HTML report.

v0.1.1 includes two live cases on MuMu Player 6.8.8.0 / Android 12:

- AnkiDroid 2.25.3: create a deck and card, force-stop, cold-launch, reopen, and verify both fields. 49/49 steps passed.
- Markor 2026.10.0: create and save a note, cold-launch, search by exact filename, reopen, and verify the body. 46/46 steps passed.

It is deliberately scoped to Windows + MuMu + ADB. CI uses deterministic fake ADB/MuMuManager backends; the live MuMu evidence is documented separately. It does not bypass login, CAPTCHA, anti-automation, or access controls.

Repo: [REPO_URL]

I would appreciate feedback on the flow format, failure evidence, and which MuMu/Windows combinations should be prioritized next.
```

Reddit 各 subreddit 版规不同，先阅读规则，避免同一文本批量粘贴。不要伪装成普通用户。

## 6. LinkedIn

```text
A quick Android demo is not a regression suite. What small teams need is a stable runtime, a repeatable flow, and evidence when something fails.

I released App TestBench v0.1.1: a Windows CLI that uses the mature MuMu Player runtime with MuMuManager and ADB, plus JSON/YAML flows, UI assertions, screenshots, UI trees, logcat, and offline HTML reports.

The release includes two live open-source app cases:
• AnkiDroid: deck/card creation and state persistence after a cold start, 49/49 steps.
• Markor: note creation, exact-file search, and read-after-restart, 46/46 steps.

AI can help author and analyze tests. It should not invent the runtime or decide the verdict. The project is local-first, MIT licensed, and explicitly scoped to Windows + MuMu + ADB.

Repo: [REPO_URL]
```

## 7. 图片 alt 文案 / Image alt text

```text
AnkiDroid card form populated by App TestBench with a test question and answer.
```

```text
AnkiDroid after a forced stop and cold launch, still showing the TestBench deck and one due card.
```

```text
Markor file browser after a cold launch, still listing app-testbench-markor.md.
```

```text
App TestBench failure report with a failed step, embedded screenshot, UI hierarchy, logcat, and timing evidence.
```

## 8. FAQ 回复

### “和 Appium 有什么区别？”

```text
Appium 是更完整的跨平台移动测试框架；App TestBench 的目标更窄：在 Windows 上把 MuMuManager + ADB、JSON/YAML flow、断言和证据报告封装成一个可直接调用的本地执行层。它不试图替代 Appium。
```

### “为什么选 MuMu，而不是让 AI 现场搭环境？”

```text
测试环境需要可管理、可重复和可诊断。MuMu 提供成熟的实例、Android 系统和 ADB 通道；App TestBench 只负责测试编排、断言和证据。这样失败可以复现，而不是依赖模型每一步临时决定。
```

### “能绕过登录、验证码、反爬或风控吗？”

```text
不能，也不会加入。项目用于你有权测试的 App、账号、设备和环境，不提供绕过访问控制、验证码、反爬、限流或风控的能力。
```

### “Web 端限制多，能用这个吗？”

```text
如果组织拥有被测系统、专用测试账号和数据，并允许在原生 App 上测试，可以使用正常的 App UI 流程做回归。这里使用的是合法测试环境，不是绕过 Web 安全机制。
```

### “为什么只有两个案例？”

```text
首版优先把两条不同难点链路做完整：AnkiDroid 覆盖对话框、数据库和冷启动持久化；Markor 覆盖文件编辑器、权限、搜索和重启后读取。案例数量比可复现性更容易造假，所以先保证每张截图、每个断言和每个限制都能查清。
```

### “CI 通过就代表所有 MuMu 都能跑吗？”

```text
不代表。CI 使用 fake ADB/MuMuManager 验证命令、流程、报告和 Schema；真实 MuMu 结果另行记录。其他 MuMu、Windows、Android 镜像和分辨率需要真实兼容性反馈。
```

## 9. 不要使用 / Avoid

- “支持任何 App / 任何模拟器”
- “适配所有 MuMu 版本”
- “一键全自动，无需配置”
- “可绕过反爬、风控、验证码或登录”
- “生产级、企业级、完全稳定”
- “大量客户 / 大量用户”
- “零失败率”
- “完全安全”

更可信的总结：

```text
A small, local-first Android test execution layer with a mature MuMu runtime, explicit limits, deterministic assertions, and inspectable evidence.
```
