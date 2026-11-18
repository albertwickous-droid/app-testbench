# App TestBench

**简体中文** | [English](README.en.md) | [Agent](docs/agent-deployment.md)

![App TestBench：在 MuMu 上执行可重复的 Android App 测试](assets/banner.png)

**在成熟的 MuMu 运行时上执行 Android App 测试；每一步可复现，失败时保留截图、UI 树、logcat 和 HTML 报告。**

App TestBench 是一个面向 Windows 的 Android App 自动化测试命令行工具。它把安装 APK、启动应用、点击、输入、等待、断言、截图、读取 UI 树和收集 logcat 组织成 JSON/YAML flow，并在每次运行后生成自包含 HTML、`result.json` 和可选 JUnit XML。

它不依赖视觉模型逐屏猜测下一步。每一步由 flow 明确声明，是否通过由 UI 文本、Activity、logcat 或文件内容等断言决定。出问题时，你能看到失败步骤、耗时、当前界面、UI 树和最近的日志，而不是只剩一句“复现不了”。

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)
![Platform](https://img.shields.io/badge/platform-Windows-0078D4.svg)
![Status](https://img.shields.io/badge/status-v0.1.1-0B7A75.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> 独立开源项目，与网易 / MuMu 官方无隶属关系。只测试你拥有或明确获授权测试的应用、账号、设备和数据。

## 先看结论：它适合什么、不适合什么

| 你可能正在面对的情况 | 是否适合 |
| --- | --- |
| 同一套 App 流程要反复执行，不想每次手工点 | **适合**：把步骤、等待和断言写进 JSON/YAML |
| 测试失败后没有现场，开发无法判断卡在哪一步 | **适合**：保存失败截图、UI 树、logcat、耗时和 HTML |
| 需要 Windows 上的 Android 运行时，又不想临时拼环境 | **适合**：以 MuMu Player 作为当前首选的成熟运行时 |
| 需要 CI 或 Agent 读取结构化结果 | **适合**：`result.json`、JUnit XML 和版本化 `--json` envelope |
| 只想做一次点击，不需要复用和报告 | **可以用**：直接执行单条 CLI，但 flow 才是主要价值 |
| 想绕过登录、验证码、反爬、风控或访问控制 | **不适合**：本项目不提供规避能力 |

## 能做什么

| 能力类别 | 已支持的功能 | 可得到的结果 |
| --- | --- | --- |
| 环境与实例 | `doctor`、MuMu 实例列表/启动/停止/重启、ADB 路径发现、指定实例或 serial | 执行前确认工具链、实例和 ADB 状态 |
| APK 与 App 生命周期 | 安装 APK、包名/版本核验、启动、打开 URI、关闭、清空数据、横竖屏 | 安装、冷启动、深链和清理都能进入同一条流程 |
| 基础 UI 操作 | 坐标点击 `tap`、按文本/`content-desc` 点击 `tap_text`、滑动、ASCII 输入、清空输入、按键、返回、Home | 用可复用步骤代替手工操作 |
| 等待与断言 | 固定等待、`wait_for_text`、`wait_for_activity`、UI 包含/不包含、logcat 包含、ANR 可见对话框恢复 | 把“应该到页面了”变成明确的通过/失败条件 |
| 证据收集 | 截图、UI 树、logcat、失败诊断、步骤耗时和状态 | 失败后仍能说明“在哪一步、看到了什么、日志是什么” |
| 流程编排 | JSON/YAML、`setup`/`steps`/`teardown`、环境变量、`continue_on_error`、开机就绪门禁 | 把安装、测试、清理和证据收集组合起来 |
| 本地测试服务 | `reverse-port` 将宿主机端口映射到设备、`open` 打开 URI | 覆盖 WebView、下载、媒体和本地 QA fixture |
| 报告与 CI | 自包含 HTML、`result.json`、可选 JUnit XML、失败 JSON envelope | 人看报告，CI/Agent 读结构化结果 |
| Agent 协助 | 打包的 Codex skill、English Agent runbook、严格 schema、五个可复现案例 | Agent 按步骤执行，不靠猜坐标和临时环境 |

## 第一次使用：从安装到第一份 HTML 报告

### 1. 准备环境

需要：

- Windows 10/11；
- Python 3.10 或更高版本；
- 已安装 MuMu Player，并启用 ADB 调试；
- 一个专门用于测试的 MuMu 实例，建议先用实例 `0`；
- 你拥有或获授权测试的 App、账号和数据。

先启动 MuMu 实例。不要在生产账号、真实个人数据或未授权设备上试跑。

### 2. 安装 App TestBench

当前以源码安装为主：

```powershell
git clone https://github.com/albertwickous-droid/app-testbench.git
cd app-testbench
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
app-testbench --version
```

看到 `app-testbench 0.1.1` 即可继续。

### 3. 检查 MuMu、ADB 和实例

```powershell
app-testbench doctor --json
```

重点看三件事：

- `MuMuManager` 和 `adb` 是否找到；
- 目标实例是否在运行；
- ADB 是否能连到该实例。

如果自动发现失败，可显式传入路径或使用环境变量：

```powershell
app-testbench doctor --json `
  --mumumanager "C:\path\to\MuMuManager.exe" `
  --adb "C:\path\to\adb.exe" `
  --instance 0
```

也可以设置 `APP_TESTBENCH_MUMUMANAGER`、`APP_TESTBENCH_ADB`、`APP_TESTBENCH_INSTANCE` 和 `APP_TESTBENCH_SERIAL`。命令名是 `--mumumanager`。

### 4. 创建第一份最小 flow

把下面内容保存为 `first-flow.yaml`。它不依赖业务 App，只打开 Android 设置，截一张图，导出 UI 树和 logcat，用来确认执行链和报告链是通的。

```yaml
version: 1
name: first-smoke
description: Open Android Settings and capture the first evidence bundle.
device:
  instance: 0
  wait_for_boot: true
  boot_timeout: 60
report:
  title: First App TestBench smoke test
  capture_screenshots: all
  collect_logcat: true
  clear_logcat: true
  include_ui_xml: true
steps:
  - name: Launch Android Settings
    action: launch
    package: com.android.settings
  - name: Let the first screen settle
    action: wait
    seconds: 2
  - name: Capture the settings screen
    action: screenshot
    label: settings
  - name: Capture the UI hierarchy
    action: dump_ui
    label: settings
teardown:
  - name: Capture recent logcat
    action: logcat
    label: final
    lines: 1000
```

### 5. 先校验，再执行

```powershell
app-testbench validate .\first-flow.yaml --json
app-testbench run .\first-flow.yaml `
  --output .\runs `
  --junit-xml .\runs\first-smoke-junit.xml `
  --json
```

`validate` 只检查 JSON/YAML 和字段，不连接设备。`run` 才会执行设备动作。成功时退出码为 `0`；执行失败为 `1`；参数或 flow 配置错误为 `2`；环境未就绪为 `3`；中断为 `130`。

### 6. 打开产物

运行目录形如：

```text
runs/<timestamp>-first-smoke/
├── report.html       # 自包含 HTML，可直接离线打开
├── result.json       # 版本化结构化结果
├── screenshots/
├── ui/
└── logs/
```

先打开 `report.html`。如果需要给 CI 或 Agent 使用，读取 `result.json`；如果给测试平台使用，传入 `--junit-xml`。

![App TestBench HTML 报告预览](assets/report-preview.png)

报告内嵌截图、UI 树片段和 logcat，不依赖 CDN、外部脚本或外部样式表。右侧步骤栏可滚动；Light / Dark 主题可在报告内切换。

## 换成自己的 App：最短路径

### 路径 A：先验证单条命令

```powershell
# 安装并核对包名、versionCode、versionName
app-testbench install .\app.apk `
  --expected-package com.example.app `
  --expected-version-code 42 `
  --expected-version-name 1.2.3

# 启动、截图、导 UI、抓日志
app-testbench launch com.example.app
app-testbench screenshot --output .\artifacts\home.png
app-testbench dump-ui --output .\artifacts\home.xml
app-testbench logcat --output .\artifacts\logcat.txt --lines 2000
```

### 路径 B：把动作固化成 flow

1. 用 `app-testbench init --output .\app-testbench-flow.yaml` 生成模板；
2. 把 `device.package`、APK 路径和步骤改成你的测试对象；
3. 用 `screenshot` / `dump_ui` 查看真实页面，优先使用 `wait_for_text` 和 `tap_text`，最后才用坐标；
4. 加上 `assert_ui_contains`、`wait_for_activity` 或 `assert_logcat_contains`；
5. 运行 `app-testbench validate`，再运行 `app-testbench run`。

一个更接近真实项目的骨架：

```yaml
version: 1
name: login-smoke
device:
  instance: 0
  package: com.example.app
  wait_for_boot: true
setup:
  - action: install
    apk: ./app.apk
    expected_package: com.example.app
    expected_version_code: 42
steps:
  - action: launch
  - action: wait_for_text
    text: Login
    timeout: 20
  - action: tap_text
    text: Username
  - action: text
    text: qa-user
  - action: tap_text
    text: Continue
  - action: wait_for_activity
    activity: com.example.app/.HomeActivity
    timeout: 10
  - action: assert_ui_contains
    text: Home
teardown:
  - action: logcat
    label: final
    lines: 2000
    continue_on_error: true
```

`text` 目前只支持可打印 ASCII。中文、日文或其他 Unicode 输入需要单独接入 ADBKeyboard、剪贴板或专用 IME，并确认测试环境允许这种方案。

## 我想实现一个功能，应该怎么做

| 我想…… | 直接用命令 | 在 flow 中使用 |
| --- | --- | --- |
| 启动/停止/重启 MuMu 实例 | `app-testbench instance start 0` | 通常在 flow 外准备环境 |
| 检查环境是否就绪 | `app-testbench doctor --json` | 运行前执行，不建议放进业务 flow |
| 安装并验证 APK | `app-testbench install .\app.apk --expected-package com.example.app` | `action: install` + `expected_*` |
| 启动 App | `app-testbench launch com.example.app` | `action: launch` |
| 启动指定 Activity | `app-testbench launch com.example.app --activity .MainActivity` | `action: launch` + `activity` |
| 打开网页或深链 | `app-testbench open "https://example.test/" --package com.example.app` | `action: open` |
| 关闭 App | `app-testbench close com.example.app` | `action: close` |
| 清空 App 数据 | `app-testbench clear-data com.example.app` | `action: clear_app_data` |
| 切横屏/竖屏 | `app-testbench orientation landscape` | `action: orientation` + `mode` |
| 点击坐标 | `app-testbench tap 540 1200` | `action: tap` |
| 按文字或描述点击 | 优先使用 flow | `action: tap_text`，支持 text / content-desc、exact / contains、index、timeout |
| 输入 ASCII 文本 | `app-testbench text "qa@example.test"` | `action: text` |
| 清空输入框 | 先点击输入框，再使用 flow | `action: clear_text` |
| 按返回或 Home | `app-testbench keyevent BACK` | `action: back` / `action: home` |
| 等待页面文字 | 使用 flow | `action: wait_for_text`，可开启 ANR 恢复 |
| 等待指定 Activity | 使用 flow | `action: wait_for_activity` |
| 断言文字存在/不存在 | 使用 flow | `action: assert_ui_contains` / `assert_ui_not_contains` |
| 断言日志包含关键字 | 使用 flow | `action: assert_logcat_contains` |
| 截图 | `app-testbench screenshot --output .\artifacts\home.png` | `action: screenshot` |
| 读取 UI 树 | `app-testbench dump-ui --output .\artifacts\ui.xml` | `action: dump_ui` |
| 收集最近 logcat | `app-testbench logcat --output .\artifacts\log.txt --lines 2000` | `action: logcat` |
| 映射本机测试服务 | `app-testbench reverse-port 18765 --local-port 18765` | `action: reverse_port` |
| 生成完整测试报告 | `app-testbench run .\flow.yaml --junit-xml .\junit.xml` | `run` 自动生成 |
| 给 CI 读取结果 | `app-testbench run .\flow.yaml --json` | `result.json` + JSON envelope |

完整字段、别名和边界见 [`docs/flow-reference.md`](docs/flow-reference.md)。

## 真实案例：不是“能点”，而是能证明

五个公开案例均来自真实 MuMu 运行，固定 APK 版本并校验 SHA256；截图来自实际 App 页面，不是生成图。

| 案例 | 覆盖的风险 | 实测结果 |
| --- | --- | --- |
| [Wikipedia 搜索、文章与冷启动持久化](examples/wikipedia-research-session/) | 网络 App、首次引导、动态搜索、WebView 文章、收藏、force-stop 后恢复 | **63/63 通过，113.563 秒** |
| [Firefox 浏览器状态、下载与标签页](examples/firefox-webapp-session/) | Cookie + LocalStorage、受控测试态、文件下载、双标签页、冷启动恢复 | **66/66 通过，143.016 秒** |
| [VLC 媒体播放、Activity 与 logcat](examples/vlc-media-playback/) | 原生播放器 Activity、byte-range MP4、真实解码帧、媒体日志、横竖屏 | **43/43 通过，50.579 秒** |
| [AnkiDroid 牌组、卡片与冷启动](examples/ankidroid-deck-persistence/) | 首次引导、系统对话框、卡片输入、数据库持久化、重启后内容断言 | **49/49 通过，75.203 秒** |
| [Markor 笔记保存、搜索与冷启动](examples/markor-note-persistence/) | 多页引导、编辑器输入、文件保存、精确搜索、重启后正文恢复 | **46/46 通过，80.203 秒** |

每个案例都有 PowerShell 准备脚本，会下载并校验固定 APK，使用案例自己的测试数据，并把 APK、原始截图、UI XML、logcat 和完整运行目录放在被忽略的 `runs/` 下。

```powershell
# 选择其中一个运行
.\examples\wikipedia-research-session\run.ps1
.\examples\firefox-webapp-session\run.ps1
.\examples\vlc-media-playback\run.ps1
.\examples\ankidroid-deck-persistence\run.ps1
.\examples\markor-note-persistence\run.ps1
```

截图、版本、证据边界和已知限制见 [`docs/cases.md`](docs/cases.md)。

## 为什么以 MuMu 为执行底座

Windows 上临时启动一个 Android 环境做演示并不难。难的是让同一条失败在一周后仍然具备可解释的实例、Android 镜像、ADB 通道和证据。

MuMu Player 负责成熟的实例管理、Android 运行环境和 ADB 连接；App TestBench 不重造这层运行时，而是补齐测试编排、动态等待、断言、失败诊断和报告交付。

| 做法 | 适合 | 主要问题 |
| --- | --- | --- |
| 人工点真机 | 最终验收、硬件能力 | 重复成本高，证据依赖人工整理 |
| 一段临时 ADB 脚本 | 单个动作 | 缺断言、等待、失败现场和统一结果 |
| 视觉模型逐屏点击 | 探索型自动化 | 环境、模型和每次决策难以复现 |
| AI 临时搭 Android 环境 | 快速演示 | 系统与工具链不稳定，出了问题难定位 |
| **App TestBench + MuMu** | 高频冒烟、回归、WebView/浏览器、可复现缺陷交付 | 首版聚焦 Windows + MuMu，硬件终验仍需真机 |

## 适用场景与合规边界

适合在**已获授权**的测试环境中使用：

- Web 端功能不完整、移动端独有，而组织允许在 Android App 上执行正常测试；
- Web 端自动化限制较多，团队需要回到组织批准的原生 App 测试环境或测试 API；
- 在隔离 MuMu 实例中通过正常 UI 登录专用测试账号，验证登录后的页面和权限；
- 验证 Cookie、LocalStorage、下载、标签页和冷启动后的测试态；
- 复现开发、测试和产品之间难以交接的步骤；
- 比较不同实例、Android 镜像、分辨率、App 版本或冷热启动状态。

这些场景的前提是：被测系统、账号、数据和设备都由你拥有或明确授权测试。App TestBench 不提供 cookie 窃取、token 导出、验证码破解、风控规避或访问控制绕过。若 Web 端限制属于产品安全设计，应使用组织批准的原生测试环境或测试接口，而不是把本工具当作绕过手段。

更多场景和权责边界见 [`docs/use-cases.md`](docs/use-cases.md)、[`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md) 和 [`DISCLAIMER.md`](DISCLAIMER.md)。

## 输出与 CI

`run` 会自动创建唯一运行目录。失败时尽量保留：

- 失败步骤和原始错误；
- 失败截图；
- UI 树；
- 最近 logcat；
- 已完成和跳过步骤及耗时；
- 一致的 `result.json`、HTML 和 JUnit 状态。

所有设备命令都支持 `--json`。`run --json` 失败时仍返回完整 `data`，并提供结构化 `error`；JSON 契约使用仓库内打包的 Draft 2020-12 schema。

## 已知限制

- 首版以 Windows + MuMu Player 为主；没有承诺所有 MuMu、Android、ADB、分辨率和语言组合都可用。
- 选择器和坐标通常针对固定 App、语言和 `720x1280` 校准；App 升级后需要维护 flow。
- 原生 `text` 只支持可打印 ASCII；中文输入尚未覆盖。
- 游戏、Canvas、自绘界面或不完整的 accessibility tree 可能无法通过 `uiautomator dump` 读取。
- VLC 案例不构成 DRM、HLS/DASH、字幕或音轨兼容性认证。
- 自动化通过不等于生产发布批准；物理设备、OEM 差异和生产账号仍需单独验收。
- 报告和日志可能包含测试环境信息，发布前必须脱敏。

## 文档

- [五个真实案例与截图](docs/cases.md)
- [Flow action 完整参考](docs/flow-reference.md)
- [架构说明](docs/architecture.md)
- [使用场景](docs/use-cases.md)
- [验证记录](docs/validation.md)
- [Agent 部署手册](docs/agent-deployment.md)
- [发布与维护](docs/publishing.md)
- [更新记录](CHANGELOG.md)

## 参与贡献

欢迎提交可复现的问题、flow 案例、文档修正和代码改进。提交前请阅读 [`CONTRIBUTING.md`](CONTRIBUTING.md)、[`SECURITY.md`](SECURITY.md) 和 [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)。不要在 issue、PR、截图或日志中提交真实账号、cookie、token、API key、私网地址或未脱敏的客户数据。

## 许可证与第三方声明

MIT。MuMu、ADB、Android 及测试 App 和媒体分别受其自身许可证与商标规则约束。详见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。
