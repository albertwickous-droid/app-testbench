# App TestBench

**简体中文** | [English](README.en.md) | [Agent](docs/agent-deployment.md)

![App TestBench：在 MuMu 上执行可重复的 Android 应用测试流程](assets/banner.png)

**用 MuMu 跑可重复的 Android App 测试；失败时保留截图、UI 树和日志。**

App TestBench 是一个面向 Windows 的 Android App 自动化测试命令行工具。它通过 `MuMuManager.exe` 和 `adb` 操作 MuMu Player，把安装、启动、点击、输入、等待、断言、截图、UI 树和 logcat 收集组织成可重复的 JSON/YAML flow，并生成自包含 HTML 报告、`result.json` 和可选 JUnit XML。

它不依赖视觉模型逐屏“猜着点”。每一步都由 flow 明确声明，是否通过由断言决定；失败时保留现场，供开发、测试和 CI 定位问题。

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)
![Platform](https://img.shields.io/badge/platform-Windows-0078D4.svg)
![Status](https://img.shields.io/badge/status-v0.1.1-0B7A75.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> 独立开源项目，与网易 / MuMu 官方无隶属关系。仅用于你有权测试的设备、应用和账号。

## v0.1.1

- 包版本和 CLI 版本为 `0.1.1`，已发布的 `v0.1.0` 标签保持不变。
- 两条真实 MuMu 案例已跑通：Fennec 本地 Web 会话 **71/71 步通过**，VLC HTTP 播放 **30/30 步通过**。
- 覆盖首次引导、系统提示、ADB reverse、异步等待、文本输入、搜索、详情、冷启动持久化、横竖屏、HTTP Range、音视频解码和日志证据。
- 失败 `run --json` 同时返回 `error` 与完整 `data`，退出码仍为 `1`，并通过公开的 `cli-v1.schema.json`。
- 工具无遥测、无云端上传、无账号体系。

## 真实案例

### Fennec：登录、异步搜索、详情与冷启动后会话恢复

![Fennec 搜索并打开真实浏览器页面](docs/assets/cases/fennec/search-result.png)

真实流程使用固定版本 Fennec F-Droid 打开本机 FieldDesk QA 页面，经 `adb reverse` 暴露测试站点。测试完成首次引导、翻译提示处理、登录、异步搜索结果、详情页、强制停止后的冷启动、`localStorage` 登录态/查询恢复和登出。

**结果：71/71 步通过，99.141 秒。** 覆盖真实浏览器 WebView、系统密码保存提示、动态等待、冷启动持久化和 UI 断言。

[复现说明](examples/fennec-local-web-session/README.md) · [案例详情与截图](docs/cases.md)

### VLC：HTTP 字节范围播放与 Android 解码证据

![VLC 播放 Sintel Trailer 并显示控制条](docs/assets/cases/vlc/playback-controls.png)

真实流程通过 `adb reverse` 访问固定 SHA256 的 MP4，使用独立的 Range 服务器返回 `206 Partial Content`，在 VLC 首次引导和播放教程后播放真实视频，并从 logcat 中确认 HTTP、demux、H.264/AAC 与 Android MediaCodec 路径。

**结果：30/30 步通过，40.547 秒。** 截图显示真实视频帧、标题和 `0:05 / 0:52` 时间轴，不是空页面或桌面截图。

[复现说明](examples/vlc-http-playback/README.md) · [案例详情与截图](docs/cases.md)

### 失败报告保留诊断现场

![失败 HTML 报告，路径和 serial 已脱敏](docs/assets/cases/evidence/report-failed.png)

失败 flow 的退出码为 `1`，JSON 中包含结构化 `error`，同时保留 `data`、失败截图、UI 树、logcat、HTML 和 JUnit。公开截图来自真实失败运行；本机路径和 ADB serial 在生成公开图前已替换。

## 为什么使用 MuMu

Windows 上临时启动一个 Android 环境做演示并不难，难的是让同一条失败在一周后仍能复现。MuMu 提供成熟的实例管理、Android 系统、ADB 通道和可配置虚拟设备，App TestBench 在这些基础能力上增加测试编排、断言、等待、证据和机器可读结果。

| 方式 | 适合场景 | 主要限制 |
| --- | --- | --- |
| 人工操作真机 | 最终验收、硬件相关功能 | 重复成本高，证据依赖人工整理 |
| 依赖视觉模型逐屏点击 | 快速探索、演示 | 环境、模型和每一步决策不易复现 |
| 一次性 ADB 脚本 | 单个动作或临时任务 | 步骤、断言、报告和失败现场不成体系 |
| App TestBench + MuMu | 高频冒烟、回归、App/WebView 测试、缺陷交付 | 首版聚焦 Windows + MuMu，仍需真机终验 |

App TestBench 把 MuMu 当作可靠的 Android 运行后端，而不是让测试工具临时拼一套非标准模拟器。坐标和定位仍由测试作者控制，工具负责可重复执行与证据交付。

## 适用场景（仅限已授权测试）

- **App-only / WebView 功能回归。** Web 端功能缺失、体验不一致，或测试环境对浏览器自动化限制较多时，如果被测系统、账号和数据属于你的组织，可使用原生 App 作为合法测试面。
- **专用测试账号登录态回归。** 在隔离 MuMu 实例中通过正常登录流程登录专用测试账号，再验证登录后页面、权限和业务流程。
- **浏览器与 WebView 状态持久化。** 验证登录态、查询条件、Cookie 生命周期和冷启动恢复，不导出或伪造 Cookie/token。
- **媒体、权限和系统提示。** 覆盖运行时权限、首次播放教程、横竖屏、HTTP Range、MediaCodec 和真实渲染帧。
- **实例、版本和启动状态兼容性。** 记录 App 是否依赖 MuMu 版本、Android 镜像、分辨率、包版本或冷/热启动状态。
- **小型团队冒烟与回归。** 不先搭建大平台，直接用 flow、HTML、JSON 和 JUnit 接入现有交付流程。
- **失败复现和缺陷交付。** 把失败截图、UI 树、logcat、耗时和错误放进同一个报告。

这些场景不包含绕过登录、验证码、反自动化、反爬、风控、限流、付费墙或访问控制。详细边界见 [`docs/use-cases.md`](docs/use-cases.md) 与 [`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md)。

## 一条 flow 如何执行

1. 解析 JSON/YAML，严格校验动作、字段、包名、URI、端口和类型。
2. 发现 `MuMuManager.exe`、`adb.exe`、目标实例和 ADB serial。
3. 可选等待 `sys.boot_completed`，再执行 setup。
4. 按顺序执行安装、启动、输入、等待、断言和证据收集。
5. 任一步失败即停止主流程，保留错误、截图、UI 树和 logcat；teardown 继续执行。
6. 生成自包含 HTML、`result.json`，可选生成 JUnit XML。

| 层 | 职责 |
| --- | --- |
| 工具发现 | MuMuManager、ADB、实例、端口和版本 |
| 设备操作 | install、launch、open、close、clear-data、orientation、reverse-port、tap、swipe、text、keyevent |
| 观察证据 | screenshot、dump-ui、logcat |
| 流程语义 | setup、steps、teardown、wait、wait_for_text、UI 断言 |
| 交付结果 | HTML、JSON、JUnit、退出码 |

## 快速开始

### 环境要求

- Windows 10/11
- Python 3.10+
- MuMu Player，至少一个已启动且开启 ADB 调试的实例
- `MuMuManager.exe` 和 `adb.exe` 可被发现，或通过参数/环境变量指定

常见 MuMuManager 位置：

```text
<MuMu root>\shell\MuMuManager.exe
<MuMu root>\nx_main\MuMuManager.exe
```

### 安装

```powershell
git clone https://github.com/albertwickous-droid/app-testbench.git
cd app-testbench
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
app-testbench --version
```

也可以从构建产物安装：

```powershell
python -m pip install .\dist\app_testbench-0.1.1-py3-none-any.whl
```

### 发现环境

```powershell
app-testbench doctor --json
```

如果自动发现失败，显式指定工具路径：

```powershell
$mumuPlayer = "<path to MuMuPlayer>"
app-testbench doctor `
  --mumumanager (Join-Path $mumuPlayer "nx_main\MuMuManager.exe") `
  --adb (Join-Path $mumuPlayer "nx_device\12.0\shell\adb.exe") `
  --json
```

### 运行真实案例

```powershell
.\examples\fennec-local-web-session\run.ps1
.\examples\vlc-http-playback\run.ps1
```

两个脚本都会下载并校验固定 APK，启动本地测试服务，执行 doctor 和 flow，保存 JUnit，并在结束时停止脚本自己启动的服务。APK、视频、原始截图、logcat 和运行目录都写入被 Git 忽略的 `runs/`。

## 基础命令

```powershell
# 安装、启动、打开 URI、关闭
app-testbench install .\app.apk --expected-package com.example.app
app-testbench launch com.example.app
app-testbench open "https://example.test/" --package com.example.app --mime-type text/html
app-testbench close com.example.app

# 设备状态
app-testbench clear-data com.example.app
app-testbench orientation landscape
app-testbench reverse-port 18765 --local-port 18765

# 交互
app-testbench tap 540 1200
app-testbench swipe 540 1600 540 500 --duration-ms 500
app-testbench text "qa@example.test"
app-testbench keyevent ENTER

# 证据
app-testbench screenshot --output .\artifacts\home.png
app-testbench dump-ui --output .\artifacts\home.xml
app-testbench logcat --output .\artifacts\logcat.txt --lines 2000
```

所有设备命令支持 `--json`。成功和失败都使用版本化 envelope，适合 CI 或 Agent 解析。

## JSON/YAML Flow

```yaml
version: 1
name: login-smoke
device:
  instance: 0
  package: com.example.app
  wait_for_boot: true
  boot_timeout: 60
report:
  title: Login smoke
  capture_screenshots: failures
  collect_logcat: true
  include_ui_xml: true
setup:
  - action: install
    apk: ${APP_APK}
    expected_package: com.example.app
    expected_version_code: 42
steps:
  - action: launch
  - action: wait_for_text
    text: Login
    timeout: 20
  - action: tap
    x: 540
    y: 1200
  - action: text
    text: qa@example.test
  - action: assert_ui_contains
    text: Welcome
  - action: screenshot
    label: welcome
teardown:
  - action: close
  - action: logcat
    label: final
    lines: 2000
```

```powershell
app-testbench validate .\app-testbench-flow.yaml --json
app-testbench run .\app-testbench-flow.yaml `
  --output .\runs `
  --junit-xml .\artifacts\junit.xml `
  --wait-for-boot --boot-timeout 60
```

完整动作与字段见 [`docs/flow-reference.md`](docs/flow-reference.md)。

## 输出与证据

一次运行生成：

```text
runs/<timestamp>-<flow-name>/
├── report.html
├── result.json
├── screenshots/
├── ui/
└── logs/
```

HTML 报告内嵌样式、脚本、截图和日志摘要，不需要 CDN 或外部服务。`result.json` 记录环境、步骤、耗时、错误和 artifact 相对路径；JUnit 每个 action 对应一个 testcase。

## Codex Skill

仓库包含 [`skills/app-testbench/SKILL.md`](skills/app-testbench/SKILL.md)。安装后，Codex 可以按固定步骤执行：

1. `doctor --json`
2. 安装 APK 并核对包名/版本
3. 根据截图和 UI 树编写或修正 flow
4. 运行成功/失败流程
5. 返回报告、JSON、JUnit 和原始证据路径

```powershell
app-testbench skill-path
Copy-Item -Recurse .\skills\app-testbench "$HOME\.codex\skills\" -Force
```

Agent 专用英文部署与发布手册：[`docs/agent-deployment.md`](docs/agent-deployment.md)。

## 错误码与 JSON 契约

| 退出码 | 含义 |
| --- | --- |
| `0` | 成功 |
| `1` | 执行失败，例如断言、ADB 或 MuMuManager 操作失败 |
| `2` | CLI 参数、flow 配置或必需工具错误 |
| `130` | 用户中断 |

失败 `run --json` 示例：

```json
{
  "schema_version": "1.0",
  "ok": false,
  "command": "run",
  "generated_at": "2026-11-16T02:35:17+08:00",
  "error": {
    "type": "step_failure",
    "message": "Flow step '...' failed: ...",
    "hint": "Visible text: ..."
  },
  "data": {
    "status": "failed"
  }
}
```

Schema 文件位于 `src/app_testbench/schemas/`。v0.1.1 未放宽 Schema；失败 envelope 通过回归测试和真实 MuMu 失败运行验证。

## 验证状态

逐项记录见 [`docs/validation.md`](docs/validation.md)。

- MuMu Player 6.8.8.0 / Android 12 / ADB 1.0.41。
- 1280×720，简体中文系统语言。
- Fennec 160.0.0：71 passed，0 failed，0 skipped，99.141 秒。
- VLC 3.7.2：30 passed，0 failed，0 skipped，40.547 秒。
- 失败契约：exit 1，Schema 通过，失败截图、UI 树、logcat、HTML、JUnit 均保留。
- 原始 APK、视频、完整运行目录、未筛选 logcat/UI XML 与虚拟环境不进入 Git。

## 安全与隐私

- 报告可能包含账号、聊天、订单、内部页面、token、URL 或设备标识，默认应视为敏感文件。
- 分享前检查 `runs/`、截图、UI XML 和 logcat。
- 项目没有遥测，不会上传 artifact。
- 不提交真实账号、生产 token、Cookie、个人 APK 或用户数据。
- 不测试未授权的设备、应用或账号。
- `install`、`clear-data`、`close`、`orientation` 和 `reverse-port` 会改变模拟器或 App 状态，应显式写入 flow。

漏洞报告方式见 [`SECURITY.md`](SECURITY.md)。

## 已知边界

- 首版目标平台是 **Windows + MuMu Player + ADB**；其他模拟器只复用了 ADB 动作，实例管理未验证。
- 没有 OCR 或图像模板匹配；坐标来自测试作者、截图或 UI 树。
- `text` 仅支持 printable ASCII；中文输入需要单独授权并验证 ADBKeyboard/剪贴板方案。
- MuMu 升级可能改变目录、端口或 MuMuManager 输出格式。
- `wait_for_text` 依赖 `uiautomator dump`；游戏引擎、自绘控件和无障碍信息不完整的页面可能无法用文本定位。
- 真实案例只证明文中记录的 App、版本、分辨率、语言和 MuMu 镜像；换环境需要重新校准。
- 物理设备仍是最终验收环境。

## 开发与门禁

```powershell
.\.venv\Scripts\Activate.ps1
python -m ruff format .
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python -m build
python -m twine check dist/*
```

CI 使用确定性 fake `adb` / `MuMuManager`，验证命令构造、flow、报告和 Schema；真实 MuMu 运行单独记录，不把 fake 测试伪装成 live 结果。

## 发布与宣传

- [`docs/publishing.md`](docs/publishing.md)
- [`docs/github-repository-setup.md`](docs/github-repository-setup.md)
- [`docs/releases/v0.1.1.md`](docs/releases/v0.1.1.md)
- [`docs/promotion.md`](docs/promotion.md)
- [`docs/launch-copy.md`](docs/launch-copy.md)
- [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md)

## 支持与贡献

- 使用、Bug 和功能请求：[`SUPPORT.md`](SUPPORT.md)
- 贡献流程：[`CONTRIBUTING.md`](CONTRIBUTING.md)
- 行为准则：[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
- 安全问题：[`SECURITY.md`](SECURITY.md)

## 法律、责任与使用边界

项目使用 **MIT License**。完整声明：

- [`LICENSE`](LICENSE)：MIT 权限、免责担保与责任限制
- [`DISCLAIMER.md`](DISCLAIMER.md)：免责声明、第三方关系与责任边界
- [`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md)：授权测试、误用边界与安全操作
- [`PRIVACY.md`](PRIVACY.md)：本地数据处理、敏感证据与保留责任
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)：第三方商标、依赖与非隶属声明
- [`SECURITY.md`](SECURITY.md)：安全边界与漏洞报告

软件按“现状”提供，不保证兼容所有 MuMu、Android 或 App 版本。使用者负责确认设备、账号、应用、数据和自动化行为的合法授权与合规性。

## License

MIT © 2026 App TestBench contributors

## Disclaimer

MuMu Player、Android、ADB、Python、GitHub、Mozilla、VLC、Sintel/Blender Foundation 及相关商标归各自权利人所有。App TestBench 是独立开源项目，不分发 MuMu 安装器、APK 或视频，不绕过应用安全控制，也不提供未经授权的账号或设备访问。