# 发布文案工具包 / Launch Copy Kit

使用前替换：

- `[REPO_URL]`：GitHub 仓库链接
- `[RELEASE_URL]`：Release 链接
- `[TESTED_MUMU_VERSION]`：实际测试过的 MuMu 版本；未完成真机验证时写“待补充”，不要编造
- `[DATE]`：发布日期

所有文案都必须和 `README.md`、Release notes 一致。截图、视频和日志只能使用合成或脱敏数据。

---

## 1. 一句话介绍 / One-line pitch

**中文**

> 成熟 MuMu 运行时 + 可重复 App 测试 + 可交付的原始证据：一条 YAML 完成安装、启动、交互、断言、截图和 logcat。

**English**

> A mature MuMu runtime, repeatable app tests, and raw evidence: one YAML flow for install, launch, actions, assertions, screenshots, and logcat.

**传播版备选 / Hook-first variants**

- 中文短钩子：**AI 可以写测试，但测试环境不能靠猜。**
- 中文可靠性钩子：**成熟 MuMu 运行时，可重复 App 测试，失败保留原始证据。**
- 中文技术版：**把 MuMu 从手动点按的模拟器，变成可重复执行、可断言、可交付证据的 Android 测试流水线。**
- English short hook: **AI can write the test. It should not guess the test environment.**
- English reliability hook: **A mature MuMu runtime. Repeatable app tests. Evidence you can hand off.**
- English technical hook: **Turn a mature MuMu runtime into a deterministic Android app test pipeline with YAML flows and evidence-rich reports.**

---

## 2. GitHub Release 开头 / GitHub Release lead

```markdown
# app-testbench v0.1.0 — Mature Runtime, Evidence-First App Testing / 成熟运行时，证据优先的 App 测试

> AI 可以写测试，但测试环境不能靠猜。成熟 MuMu 运行时，可重复 App 测试，失败保留原始证据。
>
> AI can write the test. It should not guess the test environment. A mature MuMu runtime, deterministic app flows, and raw evidence.

`app-testbench` 是一个面向 MuMu Player 的 Android 自动化执行层。它用 CLI 封装 MuMuManager 与 ADB，支持 JSON/YAML 流程、UI 断言、截图、UI 树、logcat 和自包含 HTML 报告。

`app-testbench` is an Android automation execution layer for MuMu Player. It wraps MuMuManager and ADB with a CLI, JSON/YAML flows, UI assertions, screenshots, UI hierarchy dumps, logcat, and self-contained HTML reports.

- Repository: [REPO_URL]
- Quick start: [REPO_URL]#快速开始
- English README: [REPO_URL]/blob/main/README.en.md
- Security policy: [REPO_URL]/blob/main/SECURITY.md
```

---

## 3. GitHub Discussions 欢迎贴 / Pinned discussion

**标题 / Title**

```text
Welcome to app-testbench — start here / 从这里开始
```

**正文 / Body**

```markdown
欢迎使用 `app-testbench`。

这是一个本地优先的 Android 自动化执行层，重点不是“能点”，而是每一步都有可检查的证据：状态、耗时、错误、截图、UI 树、logcat，以及最终 HTML 报告。

如果你准备第一次使用，建议：

1. 按 README 完成安装
2. 运行 `app-testbench doctor --json`
3. 跑 `examples/smoke.yaml`
4. 告诉我你的 MuMu 版本、Windows/Python 版本和卡住的位置

请不要在公开讨论中粘贴 token、cookie、真实账号截图、未脱敏 logcat 或私有业务包名。

真实兼容性报告和 Bug 请使用对应 Issue 模板。安全问题请使用 Private Vulnerability Reporting。
```

---

## 4. V2EX「分享创造」/ V2EX launch post

**标题**

```text
AI 可以写测试，但测试环境不能靠猜：我把 App 自动化跑在成熟 MuMu 上
```

**正文**

```markdown
最近把项目整理到了 v0.1.0，想分享一个自己实际会用的 Android 自动化小工具：app-testbench。

它的目标很简单：**别让 AI 临时拼一个“看起来能跑”的安卓环境，也别让失败只剩终端里的一行报错。** 一条 YAML 可以串起安装、启动、点击、等待和断言；跑完以后，截图、UI 树、logcat 和耗时都会被收进一份离线 HTML 报告。

AI 可以帮助写流程、解释失败和整理报告，但我更在意测试能不能重复：环境要成熟、步骤要显式、失败要证据。因此默认运行时选择成熟的 MuMu Player，而不是把运行环境、执行器和最终裁判都交给模型。

它也不是单纯把几条 ADB 命令包一层，而是解决一个很具体的问题：脚本点完以后，怎么知道哪一步失败、当时界面是什么、logcat 里发生了什么。

典型合规场景：

- Web 端功能不全，但需要在授权的测试环境中验证原生 App 流程；
- 专用测试账号在隔离 MuMu 实例中正常登录后，做已登录状态的回归；
- 切换实例、安装版本和启动状态，定位环境相关回归；
- 失败时把截图、UI 树和 logcat 作为同一份证据交付。

它不用于绕过登录、验证码、反自动化、反爬、风控、限流或地域限制，也不提供 Cookie/token 导出或会话伪造。

目前支持：

- doctor 检查 MuMuManager、ADB、实例和端口
- 安装 APK、启动/关闭应用
- tap / swipe / text / keyevent
- screenshot / dump-ui / logcat
- JSON/YAML flow，带 wait、assert、setup/teardown
- 失败时保留诊断截图和日志
- 自包含 HTML 报告，截图会内嵌
- 所有命令支持 --json，方便 Codex 或 CI 调用

项目是 Python + MIT，本地运行，无遥测，也不上传报告。首版主要支持 Windows + MuMu Player；真实 MuMu 版本差异仍需要更多用户反馈。

仓库：[REPO_URL]

测试环境 / 已知限制都写在 README 和 Release notes 里。欢迎指出安装、兼容性和流程设计上的问题，但请不要贴真实账号或未脱敏日志。
```

---

## 5. 掘金/知乎技术文 / Technical article

**标题候选**

```text
AI 可以写测试，但测试环境不能靠猜：为什么我把 App 自动化跑在 MuMu 上
```

或：

```text
从 AI 点击到确定性测试：app-testbench 为什么选择成熟 MuMu 运行时
```

**文章结构**

1. AI demo 与回归测试的区别：为什么临时环境不能成为判决依据
2. 为什么默认复用成熟 MuMu 运行时
3. 四层架构：发现、设备操作、流程编排、证据输出
4. 为什么使用严格 JSON/YAML schema
5. 外部命令为什么用参数数组而不是 `shell=True`
6. 失败时如何自动抓截图和 logcat
7. HTML 报告为什么必须自包含
8. 如何用 fake backend 测命令边界
9. 首次公开版本的限制和下一步
10. CTA：[REPO_URL]

**结尾 CTA**

```text
项目是 MIT，欢迎拿一个你有权测试的 App 跑 `examples/smoke.yaml`，然后把 MuMu 版本、Windows/Python 版本和失败步骤发到 Issue。真实兼容性反馈比一句“看起来不错”更有价值。
```

---

## 6. B站视频 / Bilibili demo

**标题**

```text
AI 可以写测试，但环境不能靠猜：在成熟 MuMu 上跑可重复 App 测试
```

**简介**

```text
不用把测试环境交给模型临时发挥：app-testbench v0.1.0 在成熟 MuMu 运行时上演示 doctor 检查环境 → YAML 描述流程 → 执行安装/启动/点击/断言 → 生成带截图、耗时和 logcat 的 HTML 报告。

项目：[REPO_URL]
文档：[REPO_URL]/tree/main/docs

演示使用合成或脱敏数据。项目本地运行，无遥测。
```

**字幕重点**

- 不是万能 RPA
- 重点是失败证据和可重复流程
- Windows + MuMu 首版
- 真实版本兼容性欢迎反馈

---

## 7. 小红书/即刻短帖 / Social short post

```text
AI 可以帮你写测试，但不该临时搭一个安卓环境，更不该靠“看起来没问题”宣布测试通过。

所以我做了 app-testbench：成熟 MuMu 运行时 + 确定性 flow + 原始证据。

它能：
1. 找到 MuMu 和 ADB
2. 按 YAML 安装、启动、点击、等待、断言
3. 失败时自动留截图和 logcat
4. 生成一个离线 HTML 测试报告

不是“万能脚本”，而是给 App 自动化加一层成熟运行时、确定性流程和可复核证据。
Python / MIT / 本地运行 / 无遥测

仓库：[REPO_URL]
```

不要放真实企业 App 界面和账号信息。

---

## 8. X / Twitter thread

**Post 1**

```text
AI can write the test. It should not guess the test environment.

I built app-testbench on the mature MuMu Player runtime: deterministic YAML flows, explicit assertions, and step-by-step evidence:
JSON result + screenshots + UI dump + logcat + self-contained HTML report.

[REPO_URL]
```

**Post 2**

```text
The CLI wraps MuMuManager + ADB:

doctor
install / launch / close
tap / swipe / text / keyevent
screenshot / dump-ui / logcat
validate / run JSON or YAML flows
```

**Post 3**

```text
Why another Android tool?

Because an AI demo that taps a temporary Android environment is not a regression test.

You need to know:
- which step failed
- how long it took
- what the screen looked like
- what the logs said
```

**Post 4**

```text
v0.1.0 is Windows + MuMu focused.

No telemetry. No upload. MIT.
Reports can contain sensitive data, so they stay local.

Docs and limits: [REPO_URL]
```

---

## 9. Show HN

**Title**

```text
Show HN: app-testbench – deterministic Android app tests on a mature MuMu runtime
```

**Body**

```text
I built a small Python CLI that turns repetitive Android app testing into repeatable YAML flows instead of manual tapping or a prompt-built Android demo.

The runtime choice is deliberate. Instead of asking a model to instantiate an ad-hoc Android environment and infer pass/fail from screenshots, it uses the mature MuMu Player runtime plus typed ADB commands, explicit UI assertions, and raw artifacts. AI can author flows and explain failures, but it does not own the verdict.

The design goal is evidence, not just input replay. A JSON/YAML flow can install/launch an app, wait for UI text, tap/swipe, assert UI state, take screenshots, dump the UI hierarchy, and collect logcat. The result is a structured JSON file plus a self-contained HTML report with embedded screenshots.

The first release is intentionally narrow: Windows + MuMu + ADB. No OCR, no universal RPA, no bypassing app security. Automated tests use deterministic fake ADB/MuMuManager backends; live compatibility with each MuMu release still needs real-device feedback.

Repo: [REPO_URL]
Docs: [REPO_URL]/tree/main/docs

I would especially value feedback on the flow DSL, report evidence model, and MuMu version differences.
```

---

## 10. Reddit 文案 / Reddit post

**Subreddit:** r/androiddev、r/QualityAssurance、r/softwaretesting 先逐条阅读版规。

**Title**

```text
AI can write the test, but should it guess the Android test environment?
```

**Body**

```text
I kept running into the same problem with emulator scripts: they could send taps, but when something failed I had no clean evidence of the screen, UI tree, logs, or which step broke.

So I built app-testbench on the mature MuMu Player runtime, with a Python CLI around MuMuManager and ADB. It supports JSON/YAML flows, UI assertions, screenshots, `dump-ui`, logcat, and a self-contained HTML report. AI can help write the flow, but deterministic assertions and raw evidence decide whether it passed.

It is deliberately scoped: Windows + MuMu + ADB for v0.1.0. No OCR, no universal RPA, no security bypassing. The automated suite uses fake backends, and I’m explicitly documenting that live MuMu compatibility needs real-device testing.

Repo: [REPO_URL]

Useful feedback:
- Does the flow format make sense?
- What evidence would you need on failure?
- Which MuMu version should be prioritized?

I’m the maintainer. Happy to answer implementation questions.
```

不要伪装成第三方推荐。

---

## 11. LinkedIn

```text
AI can generate a quick Android demo, but a demo is not a regression suite. Small teams need a mature runtime, a reproducible way to exercise an Android app, and evidence when it fails.

I published app-testbench v0.1.0: a Python CLI for MuMu Player that combines MuMuManager and ADB with JSON/YAML flows, UI assertions, screenshots, UI dumps, logcat, and self-contained HTML reports.

It is local-first, MIT licensed, and deliberately scoped to Windows + MuMu + ADB. Automated checks use deterministic fake backends; live compatibility is documented separately.

Repo: [REPO_URL]

I’m the maintainer and would appreciate feedback from QA and Android automation engineers.
```

---

## 12. 回复模板 / Reply templates

### “和 Appium 有什么区别？”

```text
Appium 是更完整的跨平台移动测试框架；app-testbench 的目标更窄：在 Windows 上把 MuMuManager + ADB、流程 DSL 和证据报告封装成一个可直接调用的本地执行层，尤其适合小团队、交付脚本和 Agent 工具调用。它不试图替代 Appium。
```

### “支持其他模拟器吗？”

```text
首版只验证 MuMu。ADB 操作部分理论上可以复用，但实例发现、端口和 MuMuManager 生命周期是 MuMu 专属，其他模拟器需要单独验证，不能直接宣称兼容。
```

### “能自动绕过登录/验证码吗？”

```text
不提供，也不会加入。项目用于你有权测试的 App，不绕过应用安全机制，不提供未授权账号或设备访问能力。
```

### “这和让 AI 直接搭个安卓环境、点手机有什么区别？”

```text
AI 可以参与编写 flow、解释失败和归纳报告，但运行环境和测试判决不应该靠猜。项目默认复用成熟的 MuMu 运行时，执行层使用显式 ADB 命令和 UI 断言，失败时保留截图、UI 树和 logcat。这样同一条 flow 可以重复执行，结果也能被人工复核。
```

### “为什么没有 OCR / 图像识别？”

```text
v0.1 刻意保持小而完整，使用坐标、UI 文本和显式断言。OCR/视觉识别会扩大依赖和误判面，应作为有明确需求的后续能力评估，而不是首版默认功能。
```

### “CI 过了是不是就能在所有 MuMu 版本跑？”

```text
不是。CI 使用假 ADB/MuMuManager 验证命令构造、流程和报告行为。真实 MuMu 版本、Android 镜像和 App 差异必须在目标 Windows 主机上验证，release notes 会区分两者。
```

---

## 13. 图片 alt 文案 / Image alt text

```text
Synthetic app-testbench HTML report preview showing a passed login flow, step timings, evidence artifacts, and a fake mobile login screen.
```

```text
app-testbench social preview showing a mature MuMu runtime feeding deterministic JSON/YAML app test steps and a self-contained HTML evidence report.
```

---

## 14. 不要使用的宣传语 / Avoid these claims

- “支持任何模拟器”
- “适配所有 MuMu 版本”
- “无需配置，一键全自动”
- “自动绕过检测/验证码/风控”
- “替代 Appium”
- “生产级、企业级、完全稳定”
- “已有大量用户/客户”
- “零失败率”
- “完全安全”

首版更可信的说法是：

```text
A small, local-first execution layer with explicit limits, deterministic automated tests, and room for real-device compatibility feedback.
```
