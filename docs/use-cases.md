# 使用场景 / Use Cases

App TestBench 只用于**你已获授权的 App、账号、设备和环境**。它提供的是合规的 App 测试执行能力，不授予任何访问权限，也不用于绕过第三方保护。

App TestBench is intended for apps, accounts, devices, and environments **you are authorized to test**. It provides legitimate app-test execution and does not grant access rights or permission to bypass third-party protections.

> 本项目不用于绕过登录、验证码、反自动化、反爬、风控、限流、付费墙、地域限制或其他访问控制。
>
> This project is not for bypassing login, CAPTCHA, anti-automation, anti-scraping, risk controls, rate limits, paywalls, regional restrictions, or other access controls.

## 1. Web 端功能不全或限制较多时，验证原生 App / Validate the native app when the web surface is incomplete or constrained

有些产品只在 Android App 提供完整能力，或 Web 与移动端行为不同。如果你的组织拥有被测系统、测试账号和数据，并且测试计划允许在原生 App 上执行，你可以用 App TestBench 验证安装、登录、页面跳转、业务流程和失败证据。

When some product capabilities exist only in the Android app, or web and mobile behavior differs, and your organization owns the system, test account, and data, App TestBench can validate the native app path: install, login, navigation, business flow, and failure evidence.

Web 端对自动化限制较多时，正确的做法是使用组织批准的原生 App 测试环境、专用账号或测试 API，而不是绕过控制。App TestBench 提供正常 UI 操作、等待和证据，不提供 cookie 窃取、token 导出、验证码破解或风控规避。

When a web surface places stricter limits on automation, use an organization-approved native-app test environment, dedicated account, or test API rather than bypassing controls. App TestBench provides normal UI operations, waits, and evidence; it does not steal cookies, export tokens, solve CAPTCHAs, or evade risk controls.

**边界 / Boundary**

- 仅测试你拥有或获授权测试的系统、App、账号和数据。
- Web 端限制属于产品/安全设计时，不把本项目作为绕过工具。
- Only test systems, apps, accounts, and data that you own or are authorized to test.
- Do not use this project as a bypass when web restrictions are part of a product or security design.

## 2. 专用测试账号的登录态回归 / Authenticated regression with dedicated test accounts

在隔离 MuMu 实例中通过正常 UI 流程登录专用测试账号，再运行后续 flow 验证登录后的页面、权限、查询状态和业务流程。登录态属于该测试实例，不应从真实用户浏览器复制。

Sign in to a dedicated test account through the normal UI on an isolated MuMu instance, then run later flows that verify authenticated pages, permissions, query state, and business behavior. The session belongs to the test instance and must not be copied from a real user's browser.

当前公开案例不使用真实账号，因此不会要求提交或保存任何登录凭据。组织需要做认证回归时，应在隔离实例中通过正常 UI 登录专用测试账号，再由后续 flow 验证登录后的页面和权限；不要把真实用户会话复制到测试环境。

The public cases do not use real accounts and require no committed or saved login credentials. For authenticated regression, sign in to a dedicated test account through the normal UI on an isolated instance, then verify the authenticated pages and permissions in later flows; do not copy a real user session into the test environment.

**边界 / Boundary**

- 仅使用组织提供的专用测试账号和测试数据。
- 不导出、共享或伪造 Cookie、token、会话或设备凭据。
- Use only organization-owned test accounts and test data.
- Do not export, share, or forge cookies, tokens, sessions, or device credentials.

## 3. 浏览器 / WebView 状态与冷启动 / Browser and WebView state across cold starts

适合验证移动 WebView、浏览器、输入法、翻译面板、页面异步加载、Cookie/LocalStorage、下载、标签页、登录态持久化和查询条件恢复。v0.1.1 的 Firefox 案例使用本地 QA fixture，覆盖 Cookie + LocalStorage、文件下载、双标签页和冷启动恢复；Wikipedia 案例覆盖真实网络搜索和 WebView 文章。

Use this for mobile WebViews, browsers, IME/translation panels, asynchronous page loading, Cookie/LocalStorage, downloads, tabs, login persistence, and restored query state. The v0.1.1 Firefox case covers Cookie + LocalStorage, file download, two tabs, and cold-start restore against a local QA fixture; the Wikipedia case covers live search and a WebView article.

**边界 / Boundary**

- 关键文本必须能通过 UI 树或截图定位；canvas 或自绘 WebView 可能需要额外方案。
- Key text must be locatable through the UI tree or screenshots; canvas or custom-rendered WebViews may require another approach.

## 4. 媒体、权限、横竖屏和系统 UI / Media, permissions, orientation, and system UI

VLC 案例覆盖原生播放器 Activity、HTTP byte-range、真实解码帧、libVLC 媒体输入、Android AudioTrack 和横竖屏切换；Wikipedia 与 Firefox 案例覆盖首次引导、系统提示、WebView 和浏览器页面。媒体证据同时使用 `wait_for_activity`、截图、UI 树与 `assert_logcat_contains`。

The VLC case covers the native player Activity, HTTP byte range, decoded frames, the libVLC media input, Android AudioTrack, and orientation changes. The Wikipedia and Firefox cases cover onboarding, system prompts, WebView content, and browser pages. Media evidence combines `wait_for_activity`, screenshots, UI trees, and `assert_logcat_contains`.

**边界 / Boundary**

- v0.1.1 的 VLC 案例不覆盖 DRM、自适应码率、字幕或音轨切换。
- 解码器和布局会随 MuMu/Android 镜像变化，必须记录实际环境。
- The v0.1.1 VLC case does not cover DRM, adaptive streaming, subtitles, or audio-track switching.
- Decoder names and layout vary by the MuMu/Android image; record the actual environment.

## 5. 不同实例、版本和启动状态下的兼容性验证 / Compatibility checks across instances, versions, and boot states

通过实例选择、包版本校验、启动等待、横竖屏和 ADB 设备选择，记录 App 行为是否依赖 MuMu 版本、Android 镜像、分辨率、包版本或冷/热启动。

Use instance selection, package-version verification, boot readiness, orientation, and ADB device selection to determine whether behavior depends on MuMu, the Android image, resolution, app build, or cold/warm launch.

**边界 / Boundary**

- 环境必须来自你有权控制的测试设备或实例。
- 当前版本不承诺支持所有 MuMu/Android 组合；必须记录实际测试范围。
- Environments must be test devices or instances you control.
- The current release does not claim support for every MuMu/Android combination; record the tested scope.

## 6. 小型团队的冒烟和回归 / Smoke and regression for small teams

不想先搭建大型测试平台时，可以用 JSON/YAML 描述关键用户路径，按需选择 MuMu 实例，生成包含步骤、耗时、截图、UI 树、logcat 和错误的 HTML/JSON/JUnit。

Teams that do not need a large test platform can describe critical journeys in JSON/YAML, run them on a selected MuMu instance, and produce HTML/JSON/JUnit with steps, timings, screenshots, UI trees, logcat, and errors.

## 7. 失败复现和缺陷交付 / Failure reproduction and defect handoff

当手动反馈只有“点到这里失败了”时，可以用一条可重复 flow 复现问题，并把失败截图、UI 树、日志、错误和耗时附在同一个报告中，减少开发、测试和产品之间的信息丢失。

When a manual report only says "it failed here," a repeatable flow can reproduce the issue and attach the failure screenshot, UI hierarchy, logs, error, and timings to one report, reducing information loss across QA, development, and product.

## 8. AI / Codex 辅助编写，确定性证据负责判决 / AI-assisted authoring with deterministic verdicts

AI 或 Codex 可以帮助编写 flow、解释失败和归纳报告，但测试是否通过由显式断言和保存的原始证据决定。AI 提升编写和分析效率，不负责伪造通过结果。

AI or Codex can draft flows, explain failures, and summarize reports, but pass/fail is determined by explicit assertions and preserved raw evidence. AI improves authoring and analysis; it does not decide or fabricate a passing result.

## 不适合的用途 / Unsupported uses

- 未授权访问设备、账号、企业系统或他人数据。
- 绕过登录、验证码、反自动化、反爬、风控、限流、付费墙或地域限制。
- 大规模抓取、刷量、虚假注册、垃圾信息、账号养殖或欺诈。
- 导出、共享或伪造 Cookie、token、会话或设备凭据。
- 跟踪、骚扰、监控或收集他人的私密信息。
- Unauthorized access to devices, accounts, enterprise systems, or other people's data.
- Bypassing login, CAPTCHA, anti-automation, anti-scraping, risk controls, rate limits, paywalls, or regional restrictions.
- Large-scale scraping, inflation, fake registration, spam, account farming, or fraud.
- Exporting, sharing, or forging cookies, tokens, sessions, or device credentials.
- Tracking, harassment, surveillance, or collection of other people's private information.

## 相关文件 / Related documents

- [`RESPONSIBLE_USE.md`](../RESPONSIBLE_USE.md)
- [`DISCLAIMER.md`](../DISCLAIMER.md)
- [`PRIVACY.md`](../PRIVACY.md)
- [`SECURITY.md`](../SECURITY.md)
- [`cases.md`](cases.md)