# 宣传与冷启动方案 / Promotion & Launch Playbook

本文面向 `app-testbench` v0.1.0 首次公开。目标不是“刷一波 stars”，而是让真正做 Android 测试、模拟器自动化和 Agent 工具的人看见项目、跑通一次，并留下可验证的反馈。

This playbook is for the first public launch of `app-testbench` v0.1.0. The goal is not a short burst of stars. The goal is to reach Android QA, emulator automation, and agent-tooling users, help them complete a first run, and collect verifiable feedback.

## 1. 一句话定位 / Positioning

**中文钩子 / Chinese hook**

> **AI 可以写测试，但测试环境不能靠猜。**

**中文价值主张 / Chinese value proposition**

> **成熟 MuMu 运行时，可重复 App 测试，失败保留原始证据。**

**中文定位 / Chinese positioning**

> `app-testbench` 把成熟 MuMu 运行时、确定性测试流程和可交付证据封装成 App 自动化测试工具。

**English hook**

> **AI can write the test. It should not guess the test environment.**

**English value proposition**

> **A mature MuMu runtime. Repeatable app tests. Evidence you can hand off.**

**English positioning**

> `app-testbench` turns MuMu Player into a scriptable, assertable Android automation layer that produces evidence-rich reports.

不要把它宣传成“万能 RPA”“自动操作任何 App”或“绕过检测”。这会吸引错误用户，也会制造无法兑现的预期。

Do not market it as a universal RPA platform, a tool that operates any app, or a way to bypass detection. Those claims attract the wrong audience and create expectations the project cannot safely satisfy.

## 2. 目标用户 / Target audiences

| 优先级 / Priority | 用户 / Audience | 他们关心什么 / Pain |
| --- | --- | --- |
| 1 | Android QA / 测试工程师 | 回归流程、失败证据、截图、UI、logcat |
| 2 | 小型 App 团队 / 独立开发者 | 不想搭大型测试平台，只要能跑和出报告 |
| 3 | MuMu / 模拟器自动化用户 | ADB 命令零散，实例与端口难定位 |
| 4 | Codex / Agent 工具用户 | 希望 Agent 有稳定 CLI 和结构化 JSON |
| 5 | 自动化学习者 | 想看一个真实、可读、可复用的执行层项目 |

## 3. 可信卖点 / Credible proof points

只使用 README、测试和发行说明能够证明的内容：

- MuMuManager + ADB 统一封装
- `doctor` 自动发现与实例检查
- 安装、启动、关闭、点击、滑动、输入、截图、UI 树、logcat
- JSON/YAML 流程、断言、等待、setup/teardown
- 失败时保留诊断证据
- 自包含 HTML 报告嵌入截图和日志
- 所有命令支持 `--json`
- 本地优先、无遥测、不上传报告
- 内置 Codex skill
- Windows/Linux CI 测试矩阵、打包和 `twine check`

避免宣称“支持所有 MuMu 版本”“可用于所有 App”“真实设备全部验证通过”，除非 Release 中明确记录了相应证据。

## 3.1 核心差异化 / Core differentiator

**中文：AI 可以写测试，但测试环境不能靠猜。**

项目不是“让 AI 临时搭一个安卓环境，再用视觉模型点几下”的演示工具。默认运行时选择成熟的 MuMu Player，执行层使用显式 ADB 命令、JSON/YAML 流程和 UI 断言；AI / Codex 负责辅助编写、解释和总结，真正决定 pass/fail 的是断言、截图、UI 树和 logcat。

**English: AI can write the test. It should not guess the test environment.**

The project is not an AI demo that instantiates an ad-hoc Android environment and taps through screenshots. MuMu Player is the mature default runtime; explicit ADB commands, JSON/YAML flows, and UI assertions drive execution. AI can assist with authoring and triage, while assertions and raw artifacts remain the source of truth.

| 方案 / Approach | 优势 / Strength | 边界 / Limit |
| --- | --- | --- |
| 人工真机 / Manual device | 最真实 / Most realistic | 重复成本高，证据靠人工 / Expensive and manual evidence |
| AI 临时环境或纯视觉点击 / Ad-hoc AI environment | 演示快 / Fast demo | 环境和判决不稳定 / Nondeterministic runtime and verdict |
| 一次性 ADB 脚本 / One-off ADB scripts | 自动化成本低 / Cheap automation | 缺少结构和证据 / Weak structure and evidence |
| `app-testbench` + MuMu | 成熟运行时、确定性流程、完整证据 / Mature runtime, deterministic flows, evidence | 首版 Windows + MuMu，真机仍需终验 / Windows + MuMu first, device verification still required |

营销时重点讲“运行时选择”和“证据链”，不要点名嘲讽具体竞品。真机仍然必要，本项目不是要替代最终真机验收。

## 4. 转化漏斗 / Conversion funnel

每个入口都按这五步设计：

1. **看见 / See:** banner、社交预览图、报告预览图。
2. **理解 / Understand:** 15 秒内看懂“给谁用、解决什么、怎么跑”。
3. **尝试 / Try:** README 快速开始不超过 5 条命令。
4. **信任 / Trust:** 真实边界、CI、安全政策、无遥测、MIT License。
5. **反馈 / Contribute:** Issues、Discussions、Feature request、真实兼容性报告。

GitHub 首屏应该回答：

- 这是什么？
- 为什么不是一堆 ADB 脚本？
- 我在 Windows 上怎么在 5 分钟内跑一次？
- 跑完能得到什么？
- 有哪些限制和隐私风险？

## 5. 30 天发布节奏 / 30-day launch cadence

| 时间 | 动作 | 目标 |
| --- | --- | --- |
| D-7 | README、About、topics、social preview、Release notes 定稿 | 页面能独立完成解释 |
| D-5 | 在干净 Windows 环境完成一次真实 MuMu smoke test | 记录版本和结果，不夸大 |
| D-3 | 录制 30–60 秒 demo；截 3 张合成/脱敏图 | 准备可视化素材 |
| D-2 | 找 2–3 位可信用户内测，只收可复现反馈 | 提前发现首次体验问题 |
| D-1 | 建立 Private→Public 发布流程、Issue labels、Discussions | 避免公开后手忙脚乱 |
| D0 | 切换 Public、发布 `v0.1.0` Release、发首批 2–3 个渠道 | 获得第一批真实访问 |
| D+1 | 回复所有技术问题；补 FAQ；修正安装阻碍 | 提高首次跑通率 |
| D+3 | 发技术长文：AI 可以写测试，但测试环境不能靠猜 | 吸引高质量受众 |
| D+7 | 发布第一次兼容性/反馈小结 | 建立可信度和持续维护信号 |
| D+14 | 发布 demo GIF/video 或新增示例 flow | 二次传播 |
| D+30 | 发布 Roadmap / 贡献者召集 / 使用案例 | 把一次性流量变成社区 |

不要在一天内把所有渠道刷满相同文案。每个社区使用不同角度，至少间隔数小时，并遵守各社区规则。

## 6. 渠道策略 / Channel strategy

| 渠道 / Channel | 适合内容 / Angle | 注意 / Rule |
| --- | --- | --- |
| GitHub Release | 功能、边界、验证、下载、文档入口 | 先 draft 审核再发布 |
| GitHub Discussions | “你希望下个版本支持什么” | 维护者要能持续回复 |
| V2EX 分享创造 | 独立项目、开发过程、实测边界 | 不硬广，不重复灌水 |
| 掘金 | 架构、流程 DSL、HTML 证据报告实现 | 技术长文优先 |
| 知乎 | “AI 可以写测试，但环境不能靠猜”“如何给 Agent 做执行层” | 用工程对比切入，不点名竞品 |
| B站 | 45 秒从 APK 到 HTML 报告 | 录屏要清晰、字幕化 |
| 小红书 | 简洁工作流、桌面自动化视觉卡片 | 避免技术黑话堆砌 |
| X | 短线程 + GIF + repo link | 一条只说一个问题 |
| Reddit | r/androiddev、r/QualityAssurance、r/softwaretesting | 严格先读版规，避免纯 self-promo |
| Hacker News | Show HN | 标题朴素、直接给 repo 和限制 |
| LinkedIn | QA 团队自动化、证据链 | 少用夸张营销语 |
| dev.to / 博客 | 教程和工程复盘 | 可把 README 拆成系列 |
| MuMu / Android 自动化社区 | 具体兼容性、实例管理、ADB 端口 | 不做未授权或绕过类宣传 |

### 渠道优先级 / Channel priority

首周建议只做：

1. GitHub Release + Discussions
2. V2EX 或掘金二选一
3. X 或 B站二选一
4. 一个英文开发者社区

先把一个渠道的反馈处理好，再扩到更多平台。铺得广但无人回复，比少发两个渠道更伤项目信誉。

## 7. 内容支柱 / Content pillars

长期内容保持三类，不要每天只发“求 star”：

### A. 演示 / Demos

- APK 安装到报告生成全过程
- 失败步骤如何自动保留截图和 logcat
- `doctor --json` 如何帮助 Agent 决策
- 同一 flow 如何切换实例

### B. 工程深挖 / Engineering deep dives

- 为什么外部命令用参数数组而不是 `shell=True`
- flow schema 为什么要严格校验
- HTML 报告为什么必须自包含
- JSON 输出如何让 CLI 更好被 Agent 调用
- 假后端测试如何覆盖真实命令形状

### C. 证据与兼容性 / Evidence and compatibility

- 哪些 MuMu 版本实际测试过
- 哪个 Android/WebView 场景无法 dump 文本
- 一次真实 bug 的根因、修复和回归测试
- 每周/每月 Release notes 和限制更新

### 11 个可持续选题 / 11 content ideas

1. AI 可以写测试，但为什么测试环境不能靠猜
2. 从一堆 ADB 命令到一个可断言的 Android flow
3. 为什么你的模拟器脚本失败后没有证据
4. 给 Codex 一个稳定的 Android 执行层
5. `doctor --json` 的自动发现设计
6. HTML 测试报告如何做到完全离线
7. 失败时自动截图 + 抓 logcat 的实现细节
8. 一次 MuMu 版本差异导致的 bug
9. 如何给 Android 自动化写 fake backend 测试
10. 50 行 YAML 做一个登录回归
11. v0.2.0 最值得加的 5 个能力

## 8. 素材清单 / Asset checklist

- [x] `assets/banner.svg`
- [x] `assets/social-preview.png`，1280×640
- [x] `assets/report-preview.png`，合成报告示意
- [ ] 30–60 秒 demo GIF 或 MP4
- [ ] 3 张截图：doctor、flow、report（必须是合成或脱敏数据）
- [ ] GitHub Release notes
- [ ] 各渠道文案：见 `docs/launch-copy.md`
- [ ] 真实 MuMu 版本的 smoke test 记录
- [ ] FAQ / Troubleshooting 首版

截图和视频必须使用虚构包名、示例账号和合成 App 界面。不要出现真实公司、客户、账号、聊天、订单或设备序列号。

## 9. 45 秒 Demo 分镜 / 45-second demo storyboard

| 时间 | 画面 | 旁白/字幕 |
| --- | --- | --- |
| 0–3s | AI 临时点击画面 / 散落 ADB 命令 | “能跑一次，不代表能回归。” |
| 4–9s | `app-testbench doctor --json` | “成熟的 MuMu 运行时，先检查环境。” |
| 10–16s | YAML flow | “安装、启动、等待、点击、断言，写在流程里。” |
| 17–27s | `app-testbench run flow.yaml` | “每步记录耗时、输出、截图和错误。” |
| 28–36s | `report.html` | “最后得到一个离线 HTML 证据包。” |
| 37–43s | 展示失败截图 + logcat | “失败也保留现场，而不是只剩一行报错。” |
| 44–45s | repo CTA | “app-testbench，链接在简介。” |

录屏使用 1280×720 或 1920×1080，字号至少 16px，命令逐行出现，不要加速到看不清。

## 10. 数据指标 / Metrics

北极星指标不是 stars，而是：

> **一个陌生用户是否能在 10 分钟内完成第一次有效运行，并愿意留下真实反馈。**

| 时间 | 指标 |
| --- | --- |
| D+1 | repo views、clone 数、首次 issue、安装失败点 |
| D+7 | stars、release downloads、成功运行反馈、文档跳出点 |
| D+14 | 外部 issue/PR、真实兼容性报告、讨论回复率 |
| D+30 | 复访、二次使用、贡献者、真正提出的功能需求 |

GitHub traffic 数据可能有延迟。Star 增长只能作为传播信号，不能代替“真实使用”。

## 11. 宣传底线 / Promotion ethics

- 不购买 stars、不刷评论、不批量私信。
- 不在不相关社区反复贴链接。
- 不伪造 live test、用户数、性能数据或客户案例。
- 不公开真实 App 截图、私有日志、用户账号或公司内部包名。
- 不宣称“自动绕过风控/检测/登录限制”。
- 使用第三方商标时明确说明无隶属关系。
- 自荐时说明你是维护者，不伪装成普通用户。
- 如果社区要求 self-promo 比例，严格遵守。
- 收到负面反馈时先复现问题，不把批评当攻击。

## 12. 发布日执行清单 / Launch-day checklist

### 公开前 / Before public

- [ ] Private repo 的 Actions 全绿
- [ ] GitHub About、topics、social preview 已配置
- [ ] README 首屏和快速开始已校对
- [ ] Release notes 和资产已审核
- [ ] Issues、Private Vulnerability Reporting、Secret Scanning 已开启
- [ ] 所有截图/视频确认为合成或脱敏
- [ ] 所有宣传文案与真实能力一致

### 公开后 / After public

- [ ] 发布 Release
- [ ] 发 GitHub Discussions 欢迎贴
- [ ] 发布 2–3 个定制渠道文案
- [ ] 24 小时内回复技术问题
- [ ] 把重复问题写进 FAQ
- [ ] 记录漏掉的平台、安装失败和功能请求
- [ ] D+7 发布反馈小结，不只发“求 star”

## 13. 成功标准 / Success criteria

首月成功不是“必须上千 star”，而是满足以下任意三条：

- 有至少 5 个陌生用户完成首次运行
- 收到至少 2 个可复现的真实 MuMu 兼容性报告
- 有外部 issue 或 PR
- 安装文档导致的失败显著减少
- 形成 2 个以上可复用的示例 flow
- 有明确的下个版本优先级，而不是靠想象扩功能
