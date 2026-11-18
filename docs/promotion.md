# 宣传与冷启动计划 / Promotion Playbook

目标不是“发一条链接就等 Star”，而是让 Android 开发、QA 和 Agent 工具用户快速判断三件事：

1. 这解决的是不是我的问题？
2. 它和普通 ADB 脚本、视觉点击、临时模拟器有什么不同？
3. 我现在能不能复现一个案例并看到真实证据？

## 1. 定位 / Positioning

**产品类别**：Windows 上的 Android App 自动化测试执行层。

**运行底座**：MuMu Player。成熟实例管理、Android 镜像和 ADB 连接由 MuMu 提供。

**差异点**：

- flow 明确、断言明确，不靠模型逐屏猜；
- 失败保留截图、UI 树、logcat、耗时和 HTML；
- JSON/YAML、`result.json`、JUnit 可直接进 CI；
- 三个真实案例分别覆盖网络 App、浏览器和原生媒体；
- Agent 可以编写和维护 flow，但不能伪造通过结果。

## 2. 首发渠道 / Launch channels

### GitHub

- About description 使用 `docs/launch-copy.md` 中的一句话。
- topics 使用 10–15 个准确标签，不堆无关热词。
- Release 标题：`v0.1.1 — Live Android app cases on MuMu`。
- Release 首屏先放三个案例、真实截图和修复内容，再放安装与限制。
- 置顶 Issue/Discussion：`Which authorized workflow should be the next live case?`

### 中文技术社区

优先级：

1. V2EX `分享创造`
2. 掘金/知乎专栏
3. 即刻、微博（短帖 + 三张证据图）
4. Android/测试微信群，仅在群规允许且不刷屏时分享

中文帖切入点：

- “录屏不是测试报告”
- “MuMu + YAML 的可复现 Android 回归”
- “浏览器 Cookie/下载/标签页怎么进自动化证据链”
- “VLC 这种 UI 树很少的 App 怎么做确定性断言”

### English communities

优先级：

1. Reddit `r/androiddev` 或 `r/QualityAssurance`（遵守各版规则，只发一次）
2. Hacker News `Show HN`
3. dev.to / Medium 技术文章
4. GitHub Discussions、相关开源项目 Discussion（先看规则）
5. X/Twitter、Mastodon、LinkedIn（短帖 + GIF/截图）

Hacker News 标题建议：

```text
Show HN: App TestBench – Repeatable Android tests on MuMu with failure evidence
```

不要购买 Star、刷投票、批量私信或伪装用户评价。短期数字没有意义，错误受众会带来无效 Issue 和维护成本。

## 3. 7 天发布节奏 / Seven-day cadence

### D0：GitHub Release

- 发布 `v0.1.1`。
- 上传 `docs/releases/v0.1.1.md`。
- 检查社交预览、README 首屏、三条案例链接和截图。
- 发中文短帖与 English Show HN 帖，不同时在所有社区轰炸。

### D1：Wikipedia 案例拆解

主题：

> 真实网络 App 的搜索、WebView、收藏和冷启动，如何在一个 flow 里留下证据？

内容：动态等待、英文结果选择、收藏持久化、失败边界。

### D2：Firefox 案例拆解

主题：

> 浏览器自动化不要只验证“页面打开了”：Cookie、LocalStorage、下载、标签页和冷启动恢复。

重点说明本地 fixture 无密码字段，公开案例不含真实凭据。

### D3：VLC 案例拆解

主题：

> 当 UI 树读不到视频内容时，如何用 Activity + 截图 + logcat 做确定性断言？

展示 `wait_for_activity` 和 `assert_logcat_contains`。

### D4：失败报告

主题：

> 一次失败应该带什么回到开发手里？

展示失败截图、UI 树、logcat、JUnit 和 `ok=false + error + data` 契约。

### D5：MuMu 运行时选择

主题：

> 为什么不把测试可靠性建立在临时模拟器或视觉模型上？

强调 MuMu 的成熟运行时和 App TestBench 的执行层职责，不暗示官方背书。

### D6：征集下一案例

问题：

> 下一个公开案例应该选聊天、地图、相机、输入法、电商还是跨版本兼容性？

要求提案包含：授权方式、无敏感账号方案、固定 APK、预期断言和失败面。

## 4. 内容模板 / Content templates

### 技术文章结构

1. 一个具体失败：只有录屏、复现不了。
2. 约束：Windows、MuMu、真实 App、无生产凭据。
3. flow 设计：setup、steps、teardown、断言。
4. 真实运行的截图和结果。
5. 失败时保留什么。
6. 已知限制和下一步。

### 社区回复规则

- 先回答问题，再放链接；不要让每条回复都变成广告。
- 与“能不能绕过验证码/风控”相关的问题，明确拒绝并解释合规替代方案。
- 对“为什么不用 Appium/Espresso”回答：App TestBench 是 Windows + MuMu + 外部 App/Agent 驱动的一层，不替代单元测试、Espresso 或大型设备云。
- 对“MuMu 稳定吗”回答：当前只声明记录过的 MuMu/Android 版本和三个 live case，不声明所有版本兼容。

## 5. 观察指标 / Metrics

首周只看：

- README → clone 的转化；
- 案例 README 访问；
- 成功运行 Issue/反馈；
- 真实 bug 报告；
- 外部复现数量；
- Star 的二次增长，而不是单日峰值。

建立简单表格：

| Date | Channel | Post | Views | Clones | Cases run | Issues | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |

不要用“Star 数”替代产品验证。

## 6. 30 天路线候选 / Thirty-day candidates

由维护者决定是否加入，不在本次发布中承诺：

- ADBKeyboard 中文输入；
- `assert_logcat_matches` 正则/标签过滤；
- flow retry 与失败重跑策略；
- 截图相似度/区域断言；
- 多实例并行与设备池；
- MCP server / Agent tool wrapper；
- 更多真实案例：聊天、地图、相机、输入法、跨 Android 版本；
- GitHub Actions 中的 fake backend 与 live MuMu runner 分层。

## 7. 发布检查 / Launch checklist

- [ ] `v0.1.0` tag/Release 未变化
- [ ] CI 绿
- [ ] README 三种入口可用
- [ ] 三张案例首图不是欢迎页或空页面
- [ ] Release 图片 URL 使用 `v0.1.1` tag
- [ ] 没有 APK、MP4、runs、logcat、UI XML、本机路径、serial、cookie、token、API key
- [ ] 所有公开截图在 `SHA256SUMS`
- [ ] 中文与 English 文案数字一致
- [ ] 明确 MIT、无隶属关系、仅授权测试
- [ ] 不宣传绕过验证码、反爬、风控或访问控制
- [ ] 发布后核对 remote tag、Release、CI 和仓库首页
