# 宣传与发布方案 / Promotion & Launch Playbook

本文用于 `app-testbench` v0.1.1。重点不是堆功能，而是用两条可复现的真实 App 案例说明：它能把 MuMu 从“手动点按的模拟器”变成可断言、可留证、可交给 CI 或 Agent 的 Android 测试执行层。

This playbook covers the v0.1.1 launch of `app-testbench`. The point is not a longer feature list. It is to show, with two reproducible live app cases, that the project turns MuMu from a manually operated emulator into an assertable Android test execution layer with evidence that CI and agents can consume.

## 1. 一句话定位 / Positioning

**中文钩子**

> **AI 可以写测试，但测试环境不能靠猜。**

**中文价值主张**

> 用成熟 MuMu 运行时跑可重复的 Android App 测试。每一步有断言，失败有截图、UI 树和 logcat，结束时生成离线 HTML 报告。

**中文传播句**

> **真 App、真冷启动、真断言。不是让 AI 临时拼一个看起来能跑的安卓环境。**

**English hook**

> **AI can write the test. It should not guess the test environment.**

**English value proposition**

> Run repeatable Android app tests on the mature MuMu runtime. Every step is explicit, failures retain screenshots, UI trees, logcat, and the run ends with an offline HTML report.

**English launch line**

> **Real apps, real cold starts, real assertions. Not an improvised Android environment that only looks convincing in a demo.**

项目与网易 / MuMu 官方无隶属关系。宣传时始终说明这一点。

The project is independent from NetEase / MuMu. State that clearly in launch material.

## 2. 可信卖点 / Credible proof points

只使用仓库、Release 和实际运行能直接证明的内容：

- Windows 上统一封装 `MuMuManager.exe` 与 ADB。
- `doctor` 检查 MuMu、ADB、实例和启动状态。
- JSON/YAML flow 覆盖安装、启动、关闭、点击、文本/content-desc 选择器、输入、滑动、等待、断言和清理。
- 失败时保留步骤状态、截图、UI 树、logcat、HTML、JSON 和 JUnit。
- HTML 报告可离线打开，截图以 data URI 内嵌。
- 所有 CLI 命令提供机器可读 JSON；失败 envelope 通过公开 Schema。
- 本地优先，无遥测，不上传运行证据。
- 真实案例：AnkiDroid 牌组与卡片冷启动持久化，**49/49** 步通过。
- 真实案例：Markor 笔记保存、检索与冷启动持久化，**46/46** 步通过。
- 一份真实失败契约报告，证明失败时仍保留诊断现场。

Use only claims that the repository, release, and real runs can directly support:

- One Windows CLI around `MuMuManager.exe` and ADB.
- `doctor` checks MuMu, ADB, instance state, and boot readiness.
- JSON/YAML flows cover install, launch, close, taps, text/content-desc selectors, input, swipes, waits, assertions, and cleanup.
- Failed runs retain step status, screenshots, UI trees, logcat, HTML, JSON, and JUnit.
- HTML reports open offline and embed screenshots as data URIs.
- Every CLI command offers machine-readable JSON; the failure envelope matches the published Schema.
- Local-first operation with no telemetry or artifact upload.
- Live case: AnkiDroid deck and card persistence across a cold start, **49/49** steps passed.
- Live case: Markor note save, search, and persistence across a cold start, **46/46** steps passed.
- A real intentional-failure report proves diagnostics survive a failed run.

不要宣称“支持所有模拟器”“适配所有 MuMu 版本”“任何 App 都能跑”“生产级零失败”，也不要暗示项目能绕过登录、验证码、反爬、风控或访问控制。

Do not claim universal emulator support, compatibility with every MuMu release, that any app will work, or production-grade zero-failure operation. Never imply that the project bypasses login, CAPTCHA, anti-scraping, risk controls, or access controls.

## 3. 为什么不是“AI 临时搭个安卓环境” / Why it is not an improvised AI Android environment

| 方案 / Approach | 优点 / Strength | 关键缺口 / Critical gap |
| --- | --- | --- |
| 人工真机 / Manual device testing | 最接近最终用户 / Closest to final hardware | 重复成本高，证据靠人工整理 / Expensive and manually documented |
| AI 临时环境 + 截图点击 / Ad-hoc environment plus screenshot clicking | 演示快 / Fast demo | 环境、定位、判决和复现条件不稳定 / Runtime, targeting, verdicts, and reproduction drift |
| 一次性 ADB 脚本 / One-off ADB scripts | 自动化门槛低 / Low automation effort | 缺少步骤语义、等待、断言和统一证据 / No durable step model, waits, assertions, or evidence package |
| **App TestBench + MuMu** | **成熟运行后端 + 显式流程 + 可交付证据 / Mature runtime + explicit flows + handoff-ready evidence** | **首版聚焦 Windows + MuMu，真机仍是最终验收 / v0.1.1 is Windows + MuMu scoped; physical devices remain final acceptance** |

MuMu 负责成熟、可管理、可重复启动的 Android 运行环境；App TestBench 负责测试语义、断言、证据和机器可读结果。AI 可以帮忙写 flow、分析失败和整理结论，但不负责替测试“猜通过”。

MuMu supplies a mature, manageable Android runtime. App TestBench adds test semantics, assertions, evidence, and machine-readable results. AI may help author flows and analyze failures, but it does not decide that a test passed.

## 4. 目标用户 / Target audiences

| Priority | Audience | Concrete pain |
| --- | --- | --- |
| 1 | Android QA / 测试工程师 | 回归脚本分散；失败只有一行报错；证据要靠手工收集 |
| 2 | 小型 App 团队 / 独立开发者 | 不想先搭大型测试平台，只需要能重复跑关键路径 |
| 3 | 需要 App 端测试的 Web/后端团队 | Web 端功能不全或自动化限制多，但组织授权在原生 App 环境做测试 |
| 4 | MuMu / 模拟器自动化用户 | ADB、实例、端口和生命周期由多个工具拼在一起 |
| 5 | Codex / Agent 工具用户 | 需要稳定 CLI、JSON Schema 和可检查的 artifact |

第 3 类场景必须明确写成“组织拥有系统、测试账号和数据，并允许在原生 App 上测试”。不要把它包装成绕过 Web 安全机制的方法。

For the third audience, state explicitly that the organization owns the system, test accounts, and data, and permits native-app testing. Do not frame it as a way around web security controls.

## 5. 发布素材 / Release assets

公开资产只使用以下真实截图：

- `docs/assets/cases/ankidroid/card-filled.png`：真实卡片表单输入。
- `docs/assets/cases/ankidroid/persistence.png`：冷启动后仍有 `TestBench` 与待复习卡片。
- `docs/assets/cases/ankidroid/saved-card.png`：重新打开后仍能看到正反面内容。
- `docs/assets/cases/markor/note-persisted.png`：冷启动后文件仍在列表。
- `docs/assets/cases/markor/note-search.png`：按精确文件名搜索到测试笔记。
- `docs/assets/cases/markor/note-reopened.png`：重新打开后正文仍存在。
- `docs/assets/cases/evidence/report-failed.png`：真实失败报告，路径和 serial 已脱敏。

不要用 AI 生成图替代 App 页面。不要公开完整 APK、原始运行目录、未筛选 logcat/UI XML、账号页、Cookie、token、私有包名或本机路径。`SHA256SUMS` 是公开截图的校验清单。

Use only the seven live screenshots listed above. Do not replace app pages with generated images. Do not publish APKs, complete run directories, unfiltered logcat/UI XML, account pages, cookies, tokens, private package names, or local paths. `SHA256SUMS` is the checksum manifest for the public image set.

## 6. GitHub 发布顺序 / GitHub launch sequence

1. 在 Private 仓库跑完整 CI 和本地 release gate。
2. 检查 `README.md`、`README.en.md`、`docs/cases.md`、`docs/validation.md` 和 Release notes 的数字一致。
3. 创建并推送新的 v0.1.1 commit/tag；不修改 v0.1.0。
4. 核对 GitHub Release 资产：wheel、sdist、`SHA256SUMS`。
5. 检查 About、topics、Issues、Discussions、Private Vulnerability Reporting 和 Secret Scanning。
6. 浏览器逐张检查公开截图与 Release 页面。
7. 确认仓库无 Secrets 告警后，再切换 Public。
8. 发布 Release，再把链接投放到技术社区。

Do not switch the repository public until CI, evidence, privacy review, and repository settings are complete.

## 7. 渠道建议 / Channel plan

| Channel | Best angle | Notes |
| --- | --- | --- |
| GitHub Release | 新版本、真实验证、Schema 修复 | 作为唯一权威入口 |
| V2EX 分享创造 | “AI 可以写测试，但环境不能靠猜” | 明示维护者身份，不刷屏 |
| 知乎 / 掘金 | 工程复盘：为什么 MuMu + 显式断言 + 证据 | 用真实截图和失败报告，不写万能 RPA |
| Reddit `r/androiddev` / `r/QualityAssurance` / `r/softwaretesting` | reproducible Android app testing, retained evidence | 先读版规；避免硬广 |
| Hacker News Show HN | Windows + MuMu + ADB execution layer | 标题直接说明平台边界，避免“AI”空话 |
| LinkedIn | 小团队的回归测试与 failure handoff | 说明独立项目和维护者身份 |

不要购买 stars、刷评论、批量私信或伪装成第三方推荐。社区反馈优先收集版本、环境、失败步骤和可复现信息。

Do not buy stars, post fake reviews, send bulk DMs, or disguise maintainer posts as third-party endorsements. Ask for MuMu/Windows version, failing step, and reproduction details.

## 8. 30 秒演示分镜 / 30-second demo

| Time | Shot | Caption |
| --- | --- | --- |
| 0–3s | MuMu 中打开 AnkiDroid | “先在成熟 Android 运行时里跑真 App。” |
| 4–8s | `doctor --json` | “MuMu、ADB、实例和启动状态先检查。” |
| 9–15s | `flow.yaml` 的创建卡片步骤 | “安装、输入、等待、断言都写在 flow 里。” |
| 16–21s | `run` 过程与冷启动 | “强停后重新打开，继续验证真实状态。” |
| 22–26s | `persistence.png` + `saved-card.png` | “49/49 步通过，重启后内容仍在。” |
| 27–30s | 失败报告截图 | “失败也保留截图、UI 树和 logcat。链接在简介。” |

录屏必须来自真实运行，不能拼接一段生成式界面来冒充 App 或测试结果。

## 9. 发布日检查 / Launch-day checklist

- [ ] Private 仓库 CI 全绿。
- [ ] wheel/sdist、`twine check`、CLI Schema、HTML、JUnit 和截图检查全部通过。
- [ ] 干净环境安装 wheel，并真实跑通至少一条公开案例。
- [ ] AnkiDroid 与 Markor 固定 APK 的版本和 SHA256 与文档一致。
- [ ] 公开截图无账号、Cookie、token、IP、serial、本机路径或个人信息。
- [ ] GitHub About、topics、social preview、Issues 和 security settings 已配置。
- [ ] Release notes、README 和宣传文案中的数字完全一致。
- [ ] 模拟器实例、应用和临时进程已按计划清理。
- [ ] 公开发布后 24 小时内回复可复现问题。

## 10. 成功指标 / Success metrics

首要指标不是 stars，而是“陌生用户能否在 10 分钟内完成一次有效运行并留下可复现反馈”。

Track whether a new user can complete a meaningful first run within ten minutes and leave reproducible feedback. Stars are a distribution signal, not proof of usefulness.

关注：repo views、clone 数、Release 下载、首次 issue、安装失败点、真实 MuMu 兼容性报告、外部 PR、二次使用和重复问题是否进入 FAQ。

## 11. 宣传底线 / Non-negotiable claims

- 不宣称“支持任何 App / 任何模拟器 / 所有 MuMu 版本”。
- 不宣称“自动绕过登录、验证码、反爬、风控或访问控制”。
- 不把 fake-backend CI 写成真实 MuMu 验证。
- 不伪造用户数、客户案例、性能或零失败率。
- 不使用真实客户截图或个人账号页面做宣传。
- 不在不相关社区反复贴链接。
