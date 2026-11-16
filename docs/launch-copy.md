# 发布文案工具包 / Launch Copy Kit

先替换：

- `[REPO_URL]` → `https://github.com/albertwickous-droid/app-testbench`
- `[RELEASE_URL]` → `https://github.com/albertwickous-droid/app-testbench/releases/tag/v0.1.1`
- `[DATE]` → 实际发布日期

所有数字以 `README.md`、`docs/validation.md` 和 GitHub Release 为准。公开图片只使用 `docs/assets/cases/` 下已经审计的真实 MuMu 截图。

## 1. 一句话 / One-line pitch

**中文主标题**

> 别让一次 App 回归失败只剩一句“复现不了”。

**中文副标题**

> App TestBench 用成熟的 MuMu Android 运行时执行可重复测试；失败时自动留下截图、UI 树、logcat 和 HTML 报告。

**English headline**

> A failed Android regression should leave evidence, not just “cannot reproduce.”

**English subhead**

> App TestBench runs deterministic app tests on the mature MuMu Android runtime and retains screenshots, UI trees, logcat, and an HTML report on failure.

## 2. GitHub About

**Description**

> Repeatable Android app testing on MuMu Player. JSON/YAML flows, deterministic assertions, screenshots, UI trees, logcat, self-contained HTML, JSON, and JUnit evidence.

**Topics**

```text
android
android-testing
appium-alternative
adb
mumu-player
automation
qa
regression-testing
test-automation
html-report
junit
python
windows
codex-skill
```

## 3. 短发布帖 / Short launch post

**中文**

> 很多 Android 自动化最后只剩两样东西：一段很长的录屏，和一句“我这边复现不了”。
>
> 我做了 App TestBench：用 MuMu Player 作为 Android 运行底座，用 JSON/YAML 描述安装、启动、点击、输入、等待和断言。通过与否由明确断言决定，失败时自动保留截图、UI 树、logcat、步骤耗时和 HTML 报告。
>
> v0.1.1 跑了三个真实案例：
> - Wikipedia：搜索 Ada Lovelace、阅读文章、创建收藏、冷启动后恢复（63/63）
> - Firefox：Cookie + LocalStorage、文件下载、双标签页、冷启动恢复（66/66）
> - VLC：真实 MP4、播放器 Activity、codec/AudioTrack 日志、横竖屏（43/43）
>
> 不是 AI 逐屏猜着点，也不是临时拼一个模拟器。MuMu 负责成熟的 Android 运行环境，App TestBench 负责测试执行和证据交付。
>
> 仓库：[REPO_URL]
> Release：[RELEASE_URL]

**English**

> Most Android automation demos end with a long screen recording and “it works on my machine.”
>
> App TestBench turns the same work into repeatable JSON/YAML flows on MuMu Player. Assertions decide pass/fail; failed runs retain screenshots, UI trees, logcat, timings, and a self-contained HTML report.
>
> v0.1.1 includes three live cases:
> - Wikipedia: live search, article WebView, saved list, cold-start restore (63/63)
> - Firefox/Fennec: Cookie + LocalStorage, download verification, two tabs, session restore (66/66)
> - VLC: real MP4, player Activity, codec/AudioTrack logs, orientation (43/43)
>
> This is not a vision model guessing the next tap. MuMu provides the Android runtime foundation; App TestBench provides deterministic execution and evidence delivery.
>
> Repo: [REPO_URL]
> Release: [RELEASE_URL]

## 4. 标题备选 / Title options

**中文**

1. 别再把 Android 测试录屏当报告
2. 一次失败，带着现场回来：App TestBench v0.1.1
3. 在 MuMu 上跑可复现的 Android App 测试
4. 从“点到这里失败”到可交接的测试证据

**English**

1. Android tests should leave evidence, not a screen recording
2. App TestBench: repeatable Android app testing on MuMu
3. When an Android regression fails, keep the scene
4. Deterministic Android app testing with HTML, JSON, and JUnit evidence

## 5. 截图顺序 / Evidence order

1. `assets/banner.png`：项目与 MuMu → flow → report 的关系。
2. `docs/assets/cases/wikipedia/article.png`：真实网络 App 和 WebView 内容。
3. `docs/assets/cases/firefox/orders.png`：Cookie + LocalStorage 授权状态。
4. `docs/assets/cases/firefox/tabs.png`：双标签页与浏览器状态。
5. `docs/assets/cases/vlc/landscape.png`：原生媒体、Activity、横竖屏。
6. `docs/assets/cases/evidence/report-failed.png`：失败报告和诊断价值。

不要先用欢迎页、空页面或桌面截图。读者应先看到可交付结果，而不是环境启动过程。

## 6. 回答“为什么用 MuMu”

> 因为测试工具最不应该把时间花在维护一套临时 Android 环境上。MuMu 已经提供实例管理、Android 镜像和 ADB 通路；App TestBench 把精力放在 flow、等待、断言、失败证据和 CI 输出上。这样比“AI 临时搭一个模拟器再逐屏点击”更容易复现和定位问题。

> The test tool should not spend its time maintaining a one-off Android environment. MuMu already provides instance management, an Android runtime, and ADB connectivity. App TestBench focuses on flows, waits, assertions, failure evidence, and CI output. That is easier to reproduce and diagnose than an AI-assembled emulator plus screen-by-screen guessing.

## 7. 边界表述 / Boundary language

推荐：

> 用于你有权测试的 App、账号、设备和环境；当 Web 端功能不全或只能在移动 App 验证时，在组织批准的 MuMu 实例中执行正常 UI 流程并保留证据。

Avoid claiming that the project bypasses login, CAPTCHA, anti-automation, anti-scraping, risk controls, rate limits, paywalls, or access controls. The supported value is repeatable authorized testing, not evasion.

## 8. Call to action

> 如果你正在做 Windows 上的 Android 冒烟、回归或缺陷交付，可以先跑一个案例，看看失败时拿到的证据是否足够让开发直接开始定位。
> [REPO_URL]
