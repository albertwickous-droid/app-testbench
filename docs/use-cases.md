# 使用场景 / Use Cases

App TestBench 面向**你有权测试的 App、账号、设备和环境**。本文描述的是合规的 App 自动化测试场景，不构成访问授权，也不允许绕过第三方保护机制。

App TestBench is intended for apps, accounts, devices, and environments **you are authorized to test**. These are legitimate app automation scenarios. They do not grant access rights or permission to bypass third-party protections.

> 本项目不用于绕过登录、验证码、反自动化、反爬、风控、限流、付费墙、地域限制或其他访问控制。
>
> This project is not for bypassing login, CAPTCHA, anti-automation, anti-scraping, risk controls, rate limits, paywalls, regional restrictions, or other access controls.

## 1. Web 端功能不全，需要验证原生 App 流程

When the web surface is incomplete, validate the authorized native-app flow

产品的一部分能力只在 Android App 中提供，或 Web 端功能、交互和移动端存在差异时，可以在获得授权的测试环境中通过 App TestBench 验证原生 App 的安装、启动、页面跳转、文本断言和失败证据。

When some product capabilities exist only in the Android app, or the web and mobile experiences differ, App TestBench can validate the native app path in an authorized test environment: install, launch, navigation, text assertions, and failure evidence.

**边界 / Boundary**

- 网页端因组织权限、产品设计或业务规则而不提供某项能力时，应通过合法测试账号、测试数据或测试接口验证 App。
- 不得把本项目描述为绕过网页访问控制、反自动化或反爬机制的方法。
- When the web surface intentionally restricts a capability, use a legitimate test account, test data, or test API to validate the app.
- Do not present this project as a way to bypass web access controls, anti-automation, or anti-scraping protections.

## 2. 已授权测试账号的登录态回归

Authenticated regression with dedicated test accounts

测试人员可以先在隔离的 MuMu 实例中通过正常登录流程登录专用测试账号，再在后续 flow 中验证登录后的页面、权限和业务流程。登录态属于该测试实例，不应从真实用户浏览器或其他未授权环境复制。

For an isolated MuMu instance, testers may sign in to a dedicated test account through the normal login flow, then run later flows that verify authenticated pages, permissions, and business behavior. The session belongs to that test instance; it must not be copied from a real user's browser or any unauthorized environment.

**边界 / Boundary**

- 仅使用组织提供的专用测试账号和测试数据。
- 不内置 Cookie 窃取、token 导出、会话伪造、验证码破解或登录绕过。
- 不在共享账号、生产账号或他人账号上复用登录态。
- Use only organization-owned test accounts and test data.
- No cookie theft, token export, session forgery, CAPTCHA solving, or login bypass.
- Do not reuse sessions on shared, production, or other people's accounts.

## 3. 不同实例、版本和启动状态下的兼容性验证

Compatibility checks across instances, versions, and boot states

通过 MuMu 实例选择、包版本校验、启动等待和 ADB 设备选择，记录不同测试环境下的 App 行为。适合验证回归问题是否与实例、Android 镜像、屏幕尺寸、安装版本或启动状态有关。

Use MuMu instance selection, package-version checks, boot-readiness waits, and ADB device selection to record app behavior across test environments. This helps determine whether a regression depends on an instance, Android image, screen size, installed version, or boot state.

**边界 / Boundary**

- 环境差异必须来自你有权控制的测试设备或实例。
- 当前版本不承诺支持所有 MuMu、Android 或设备配置；实际测试结果必须记录。
- Environment differences must come from test devices or instances you control.
- The current release does not claim support for every MuMu, Android, or device configuration; record live test coverage explicitly.

## 4. 小型团队的冒烟测试和回归测试

Smoke and regression testing for small teams

不想先搭建大型测试平台时，可以用 JSON/YAML 描述关键用户路径，按需选择 MuMu 实例运行，并生成包含步骤状态、耗时、截图、UI 树、logcat 和错误信息的离线报告。

Teams that do not need a full test platform can describe critical user journeys in JSON/YAML, run them against a selected MuMu instance, and produce an offline report containing step status, timing, screenshots, UI hierarchy, logcat, and errors.

## 5. 失败复现和缺陷交付

Failure reproduction and defect handoff

当手动反馈只有“点到这里失败了”时，可以用一条可重复 flow 复现问题，并把失败截图、UI 树、日志和步骤耗时附在同一个报告中，减少开发、测试和产品之间的信息丢失。

When a manual bug report only says “it failed here,” a repeatable flow can reproduce the issue and attach the failing screenshot, UI hierarchy, logs, and step timings to one report, reducing information loss between QA, developers, and product teams.

## 6. AI / Codex 辅助编写，确定性证据负责判决

AI-assisted authoring with deterministic verdicts

AI 或 Codex 可以帮助生成 flow 草稿、解释失败和归纳报告，但测试是否通过由显式断言和保存的原始证据决定。这样可以把 AI 的效率用于编写和分析，而不是把运行环境和最终判决交给不可重复的模型行为。

AI or Codex can help draft flows, explain failures, and summarize reports, but pass/fail is determined by explicit assertions and preserved raw evidence. AI improves authoring and analysis; it is not the runtime or the final judge.

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
