# App TestBench

**简体中文** | [English](README.en.md) | [Agent](docs/agent-deployment.md)

![App TestBench：在 MuMu 上执行可重复的 Android App 测试](assets/banner.png)

**别让一次回归失败只剩一句“复现不了”。**

App TestBench 用 MuMu Player 执行可重复的 Android App 测试。一条 JSON/YAML flow 串起安装、启动、点击、输入、等待、断言、截图、UI 树与 logcat；结束时生成自包含 HTML、`result.json` 和可选 JUnit XML。失败会保留现场，而不是把证据散落在聊天记录、录屏和临时目录里。

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)
![Platform](https://img.shields.io/badge/platform-Windows-0078D4.svg)
![Status](https://img.shields.io/badge/status-v0.1.1-0B7A75.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> 独立开源项目，与网易 / MuMu 官方无隶属关系。只测试你拥有或明确获授权测试的应用、账号、设备和数据。

## 它不是“模拟器遥控器”

App TestBench 的交付物不是一组零散 ADB 命令，而是一条可重复执行的测试流程和一份可交接的结果：

- **步骤由 flow 明确定义**：不依赖视觉模型逐屏临时猜下一步。
- **通过/失败由断言决定**：Activity、UI 文本、logcat 或下载文件内容都可以成为判断依据。
- **失败时自动保留证据**：失败截图、UI 树、logcat、耗时、错误和 HTML。
- **结果可进 CI**：退出码、版本化 JSON envelope、`result.json` 和 JUnit。
- **可以被 Agent 调用**：仓库自带 Codex skill，Agent 负责写和修 flow，真实执行仍由确定性 runner 完成。

## 为什么把 MuMu 放在执行底座

Windows 上临时启动一个 Android 环境做演示并不难。难的是让同一条失败在一周后仍有相同实例、Android 镜像、ADB 通道和可复现证据。

MuMu Player 已经负责成熟的实例管理、Android 运行环境和 ADB 连接。App TestBench 不重造这层，也不把可靠性押在临时拼出来的模拟器或视觉模型上；它补的是测试编排、动态等待、断言、失败诊断和报告交付。

| 做法 | 适合 | 主要问题 |
| --- | --- | --- |
| 人工点真机 | 最终验收、硬件能力 | 重复成本高，证据依赖人工整理 |
| 一段临时 ADB 脚本 | 单个动作 | 缺断言、等待、失败现场和统一结果 |
| 视觉模型逐屏点击 | 探索型自动化 | 环境、模型和每次决策难以复现 |
| AI 临时搭 Android 环境 | 快速演示 | 系统与工具链不稳定，出了问题难定位 |
| **App TestBench + MuMu** | 高频冒烟、回归、App/WebView、可复现缺陷交付 | 首版聚焦 Windows + MuMu，硬件终验仍需真机 |

## v0.1.1：三个真实案例

下面的结果都来自实际 MuMu 运行。截图来自 App 页面，不是生成图；APK 固定版本和 SHA256，运行脚本可重新下载并验证。

| 案例 | 验证的风险 | 结果 |
| --- | --- | --- |
| [Wikipedia 搜索、文章与冷启动持久化](examples/wikipedia-research-session/) | 网络 App、首次引导、动态搜索、WebView、收藏、force-stop 后恢复 | **63/63 通过，113.563 秒** |
| [Firefox 浏览器状态、下载与标签页](examples/firefox-webapp-session/) | Cookie + LocalStorage、受控登录态、文件下载、双标签页、冷启动恢复 | **66/66 通过，143.016 秒** |
| [VLC 媒体播放、Activity 与 logcat](examples/vlc-media-playback/) | 原生播放器 Activity、byte-range MP4、真实解码帧、codec/AudioTrack 日志、横竖屏 | **43/43 通过，50.579 秒** |

### Wikipedia：真实网络内容与收藏恢复

![Wikipedia Ada Lovelace 文章页](docs/assets/cases/wikipedia/article.png)

流程完成首次引导，切换到英文内容，搜索 `Ada Lovelace`，打开真实文章 WebView，创建 `QA Reading List` 并保存文章；随后强制停止、冷启动 App，再验证文章和描述仍在收藏中。它覆盖了真实网络内容、动态等待和跨冷启动的本地状态。

[运行说明](examples/wikipedia-research-session/README.md) · [证据链](docs/cases.md#1-wikipedia-search-article-and-cold-start-persistence--搜索文章与冷启动持久化)

### Firefox：浏览器状态不止是“页面打开”

![Fennec 授权后的订单页](docs/assets/cases/firefox/orders.png)

本地 QA fixture 不包含密码字段，只用合成身份 `qa-runner` 验证 Cookie 与 LocalStorage 同时生效。流程还下载案例专属文件并由宿主机重新读取校验，创建第二个标签页，最后 force-stop 并冷启动验证登录态与标签页恢复。

[运行说明](examples/firefox-webapp-session/README.md) · [证据链](docs/cases.md#2-firefox-fennec-browser-state-download-and-tabs--浏览器状态下载与标签页)

### VLC：UI 树之外也能断言

![VLC 横屏播放 Sintel Trailer](docs/assets/cases/vlc/landscape.png)

VLC 案例从本地 byte-range HTTP 服务播放真实 MP4，等待 `VideoPlayerActivity` 进入前台，并分别断言 libVLC 打开媒体输入和 Android `android_audiotrack` 模块初始化。它证明这个执行层不仅会“找字点击”，也能验证原生 Activity、解码画面、底层日志和方向切换。

[运行说明](examples/vlc-media-playback/README.md) · [证据链](docs/cases.md#3-vlc-real-media-activity-and-logcat--真实媒体activity与logcat)

### 失败时，报告保留现场

![失败 HTML 报告：失败步骤、截图、UI 树、logcat 与耗时集中在一页](docs/assets/cases/evidence/report-failed.png)

上面是真实失败运行生成的 HTML 报告。失败步骤、错误摘要、前后步骤、截图、UI 树、logcat 和耗时都在同一份结果里；发布版本把本机路径和测试 ADB serial 脱敏后再展示。

完整截图、固定版本、已知限制和失败报告见 [`docs/cases.md`](docs/cases.md)。

## 适用场景（仅限已授权测试）

- **网页端功能不全、App 才是实际产品路径**：桌面 Web 没有完整入口，或移动端行为与浏览器不一致时，在组织批准的 MuMu 测试实例和专用账号上验证原生 App 流程。
- **需要保留登录态，但不能碰真实用户会话**：通过正常 UI 登录专用测试账号，再验证登录后的页面、权限、查询和业务流程。测试工具不会替你绕过认证，也不导出、复制或伪造 Cookie/token。
- **浏览器 / WebView 行为**：Cookie、LocalStorage、下载、标签页、翻译提示、冷启动恢复、异步加载和移动端布局。
- **原生 Activity 与媒体**：检查播放器、相机、系统 Intent 跳转、解码器初始化、音视频输出和横竖屏切换。
- **回归与缺陷交付**：把“点到这一步失败了”变成带截图、UI 树、logcat、耗时和错误信息的可复现报告。
- **小团队冒烟**：不想先搭大平台，只想把最关键的用户路径稳定跑起来并接入 CI。
- **Agent 辅助编写**：让 Codex/AI 写 flow、读失败、修选择器；通过与否仍由断言和原始证据决定。

**边界**：不用于绕过登录、验证码、反自动化、反爬、风控、限流、付费墙、地域限制或其他访问控制。网页端限制属于产品或安全设计时，应使用组织批准的原生测试环境、测试账号或测试 API，而不是把本项目当作绕过工具。

## 安装

环境要求：

- Windows 10/11
- Python 3.10+
- MuMu Player，至少一个已启动并开启 ADB 调试的实例

```powershell
git clone https://github.com/albertwickous-droid/app-testbench.git
cd app-testbench
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
app-testbench --version
app-testbench doctor --json
```

如果自动发现失败，显式传入工具路径：

```powershell
$mumuRoot = "<your MuMu root>"
app-testbench doctor `
  --mumumanager (Join-Path $mumuRoot "nx_main\MuMuManager.exe") `
  --adb (Join-Path $mumuRoot "nx_device\12.0\shell\adb.exe") `
  --json
```

`doctor` 会检查 MuMuManager、ADB、MuMu 版本、实例状态和 ADB 连接。它只诊断，不自动启动或关闭模拟器。

## 运行真实案例

```powershell
.\examples\wikipedia-research-session\run.ps1
.\examples\firefox-webapp-session\run.ps1
.\examples\vlc-media-playback\run.ps1
```

每个脚本都会从可信来源下载固定 APK 并校验 SHA256，然后执行 `doctor`、flow 和 JUnit 输出。APK、MP4、原始截图、UI XML、logcat、HTML 运行目录都在被 Git 忽略的 `runs/` 下，不会进入公开仓库。

## 一个最小 flow

```yaml
version: 1
name: settings-smoke
device:
  instance: 0
  package: com.example.app
  wait_for_boot: true
  boot_timeout: 60
report:
  title: Settings smoke test
  clear_logcat: true
  include_ui_xml: true
setup:
  - action: install
    apk: ${APP_APK}
    expected_package: com.example.app
steps:
  - action: launch
  - action: wait_for_text
    text: Settings
    timeout: 30
  - action: tap_text
    text: About
    match: exact
  - action: wait_for_activity
    activity: com.example.app/.AboutActivity
    timeout: 10
  - action: screenshot
    label: about
  - action: dump_ui
    label: about
  - action: assert_logcat_contains
    text: AboutActivity
    lines: 5000
teardown:
  - action: close
  - action: logcat
    label: final
    lines: 3000
```

```powershell
app-testbench validate .\flow.yaml --json
app-testbench run .\flow.yaml `
  --output .\runs `
  --junit-xml .\artifacts\junit.xml `
  --wait-for-boot
```

`wait_for_activity` 适合确认 WebView、播放器、相机或深链跳转是否真的进入预期原生组件；`assert_logcat_contains` 用于 UI 树看不到、但可以从日志确认的子系统行为。

## 常用 CLI

```powershell
# 安装、启动、打开 URI、关闭
app-testbench install .\app.apk --expected-package com.example.app
app-testbench launch com.example.app
app-testbench open "https://example.test/" --package com.example.app --mime-type text/html
app-testbench close com.example.app

# 设备与状态
app-testbench doctor --json
app-testbench instance list --json
app-testbench clear-data com.example.app
app-testbench orientation landscape
app-testbench reverse-port 18765 --local-port 18765

# 基本操作
app-testbench tap 540 1200
app-testbench swipe 540 1600 540 500 --duration-ms 500
app-testbench text "qa@example.test"
app-testbench keyevent ENTER

# 观察与证据
app-testbench screenshot --output .\artifacts\home.png
app-testbench dump-ui --output .\artifacts\home.xml
app-testbench logcat --output .\artifacts\logcat.txt --lines 3000
```

所有设备命令都支持 `--json`。成功和失败使用版本化 envelope；失败 `run --json` 退出码为 `1`，同时返回结构化 `error` 和完整 `data`。

## 输出与证据

```text
runs/<timestamp>-<flow-name>/
├── report.html       # 自包含，截图以 data URI 内嵌
├── result.json       # 版本化机器可读结果
├── screenshots/
├── ui/
└── logs/
```

失败运行时，runner 会尽量保留：

- 失败步骤和错误信息；
- 失败截图；
- UI 树；
- 最近 logcat；
- 失败前已完成步骤、耗时和跳过步骤；
- `result.json`、HTML 和 JUnit 中的一致状态。

HTML 不加载 CDN、外部脚本或外部样式。报告可离线打开和归档。

## Codex Skill 与 Agent 使用

仓库包含 [`skills/app-testbench/SKILL.md`](skills/app-testbench/SKILL.md)。安装后，Codex 或兼容 Agent 可以按固定步骤执行：

1. `doctor --json` 检查 MuMu、ADB 和实例。
2. 安装 APK 并核对包名、版本和 SHA256。
3. 用真实截图和 UI 树编写或修正 flow。
4. 运行成功、失败流程并读取 `result.json`。
5. 交付 HTML、JUnit 和原始证据路径。

如果由 Agent 部署或复现本项目，直接阅读 [Agent runbook](docs/agent-deployment.md)。页面按执行顺序写明权限边界、环境检查、案例运行、发布验证和清理要求。

## v0.1.1 修复

- 修复失败 `run --json` envelope：`ok=false` 时同时包含结构化 `error` 和完整 `data`，退出码保持 `1`。
- 回归测试直接使用打包后的 `cli-v1.schema.json` 校验失败输出，没有放宽 Schema。
- 新增 `wait_for_activity`：按 Activity component 轮询并保留最后观察值。
- 新增 `assert_logcat_contains`：在 UI 树看不到的状态之外，用 logcat 做确定性断言。
- `tap_text`、`clear_text`、`wait_for_text.recover_anr`、`open`、`reverse-port`、`orientation` 等能力继续保留。
- 三个公开案例替换为此前的简单持久化案例，覆盖网络 App、浏览器和原生媒体三条不同工程链路。

完整验证结果见 [`docs/validation.md`](docs/validation.md)，变更记录见 [`CHANGELOG.md`](CHANGELOG.md)。

## 已知限制

- 首版聚焦 Windows + MuMu Player；不承诺所有 MuMu、Android、ADB、分辨率或语言组合。
- 选择器和坐标仍针对固定 App、语言和 `720x1280` 校准；App 升级后需要维护 flow。
- native `text` 输入目前只支持可打印 ASCII；中文输入需要后续 IME/ADBKeyboard 方案。
- `uiautomator dump` 无法读取的游戏、自绘画布或不完整无障碍树需要额外方案。
- 媒体案例不是 DRM、HLS/DASH、字幕或音轨切换的兼容性认证。
- 自动化通过不等于生产发布通过；物理设备和真实账号仍需要另行验收。

## 权责与安全

- [Responsible Use](RESPONSIBLE_USE.md)
- [Disclaimer](DISCLAIMER.md)
- [Privacy](PRIVACY.md)
- [Security](SECURITY.md)
- [Third-Party Notices](THIRD_PARTY_NOTICES.md)

项目无遥测、无云端上传、无账号体系。你的截图、日志、APK 和账号数据是否敏感，由你的测试场景决定；公开前必须自行脱敏。

## 文档

- [真实案例与截图](docs/cases.md)
- [Flow 动作参考](docs/flow-reference.md)
- [架构](docs/architecture.md)
- [使用场景](docs/use-cases.md)
- [验证记录](docs/validation.md)
- [发布与推广文案](docs/launch-copy.md)
- [GitHub 仓库设置](docs/github-repository-setup.md)
- [发布流程](docs/publishing.md)

## License

MIT。第三方 App、MuMu、ADB、Android 和测试素材的许可与商标归各自权利人所有，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
