# 隐私与数据处理说明 / Privacy and Data Handling

## 1. 文件性质 / Scope

本文件说明 `app-testbench` 软件在本地处理哪些数据、数据保存在哪里，以及用户应如何保护测试证据。它针对本地开源软件，不是面向云端账号服务的通用隐私政策。

This document explains what data the `app-testbench` software handles locally, where that data is stored, and how users should protect test evidence. It applies to local open-source software, not to a cloud account service.

项目没有由维护者运营的账号系统、遥测服务或报告上传后端。

The maintainers do not operate an account system, telemetry service, or report-upload backend for this project.

## 2. 核心原则 / Core principles

- **本地优先：** 软件在用户控制的机器上运行。
- **无遥测：** 软件不会主动发送使用统计、崩溃分析、设备信息或报告。
- **不上传证据：** 截图、UI 树、logcat、HTML 报告和 `result.json` 默认只写入本地。
- **最小依赖：** 运行时 Python 依赖为 PyYAML；MuMuManager、ADB 和 MuMu Player 由用户自行安装和控制。
- **用户控制：** 输出位置、流程内容、日志采集和保留周期由用户决定。

- **Local-first:** the software runs on a machine controlled by the user.
- **No telemetry:** the software does not proactively send usage analytics, crash analytics, device information, or reports.
- **No evidence upload:** screenshots, UI trees, logcat, HTML reports, and `result.json` are written locally by default.
- **Minimal dependencies:** the runtime Python dependency is PyYAML; MuMuManager, ADB, and MuMu Player are installed and controlled by the user.
- **User control:** users choose output paths, flow content, log collection, and retention periods.

## 3. 软件可能处理的数据 / Data the software may process

根据用户命令和 flow，软件可能在本地处理：

- 设备与实例标识、ADB serial、端口和工具路径；
- APK 路径、包名、Activity 名称和 flow 配置；
- 点击、滑动、文本输入和按键内容；
- 截图、UI XML、节点文本和 `content-desc`；
- logcat 中的应用日志、URL、设备信息或异常堆栈；
- 命令输出、耗时、错误信息和 HTML/JSON 报告；
- 环境变量中用于 flow 插值的值。

Depending on commands and flows, the software may process locally:

- device and instance identifiers, ADB serials, ports, and tool paths;
- APK paths, package names, activity names, and flow configuration;
- tap, swipe, text input, and key events;
- screenshots, UI XML, node text, and `content-desc` values;
- application logcat entries, URLs, device information, or stack traces;
- command output, timings, errors, and HTML/JSON reports;
- environment-variable values used for flow interpolation.

这些数据可能包含个人信息、账号标识、聊天、订单、医疗信息、企业内部信息、token 或其他敏感内容。

This data may contain personal information, account identifiers, chats, orders, medical information, internal business data, tokens, or other sensitive content.

## 4. 本地保存位置 / Local storage

默认运行目录通常是：

```text
runs/<timestamp>-<flow-name>/
```

其中可能包含：

- `report.html`
- `result.json`
- `screenshots/`
- `ui/`
- `logs/`

用户可以通过 `--output` 或命令行参数改变输出位置。仓库中的 `runs/`、`reports/`、`artifacts/`、`.env` 和本地配置默认被 `.gitignore` 排除。

Users can change output locations with `--output` or command-line options. The repository ignores `runs/`, `reports/`, `artifacts/`, `.env`, and local configuration by default.

## 5. 网络活动 / Network activity

`app-testbench` 本身不包含遥测或报告上传代码。以下活动可能产生网络连接，但由用户或其他工具触发：

- `pip install` 从 PyPI 或镜像下载依赖；
- GitHub 页面、Release 下载、Issue 和徽章图片；
- 用户自己的 flow、脚本或外部工具访问网络；
- MuMu Player、ADB、Android 系统或第三方 App 自身的联网行为。

`app-testbench` itself contains no telemetry or report-upload code. The following may create network connections when initiated by users or other tools:

- `pip install` downloading dependencies from PyPI or mirrors;
- GitHub pages, release downloads, issues, and badge images;
- user-authored flows, scripts, or external tools that access the network;
- network behavior of MuMu Player, ADB, Android, or third-party applications.

README 中的 shields.io 徽章由外部服务提供。查看这些图片时，相关请求受该服务及 GitHub 的条款和隐私政策约束。

Shields.io badges in the README are served by an external provider. Requests for those images are governed by that provider's and GitHub's terms and privacy policies.

## 6. GitHub 交互 / GitHub interactions

在 GitHub 提交 Issue、PR、Discussion 或安全报告时，你提供的内容由 GitHub 处理。不要提交：

- token、cookie、Authorization header 或私钥；
- 真实账号截图、聊天、订单或客户数据；
- 未脱敏 logcat、UI 树或报告；
- 企业内部包名、服务地址或设备序列号；
- 他人的个人信息。

When submitting issues, pull requests, discussions, or security reports on GitHub, the content you provide is processed by GitHub. Do not submit:

- tokens, cookies, authorization headers, or private keys;
- real account screenshots, chats, orders, or customer data;
- unredacted logcat, UI trees, or reports;
- internal package names, service addresses, or device serials;
- another person's personal information.

## 7. 用户的数据保护责任 / User data-protection responsibility

使用者应自行评估并落实：

- 数据最小化：只采集完成测试所需的最少证据；
- 脱敏：在分享前移除账号、token、地址、设备标识和业务数据；
- 访问控制：限制 `runs/` 和报告目录的读取权限；
- 加密与备份：对需要长期保存的敏感证据使用加密存储；
- 保留期限：设置自动清理周期，避免无限期保留日志和截图；
- 合规评估：根据所在地法律、行业规则和公司政策判断是否允许处理相关数据。

Users should assess and implement:

- data minimization: collect only the evidence needed for the test;
- redaction: remove accounts, tokens, addresses, device identifiers, and business data before sharing;
- access control: restrict access to `runs/` and report directories;
- encryption and backups: use encrypted storage for sensitive evidence retained long term;
- retention limits: schedule cleanup instead of retaining logs and screenshots indefinitely;
- compliance review: determine whether applicable law, industry rules, and company policy permit the processing.

项目不保证满足任何特定司法辖区的 GDPR、个人信息保护法、行业监管或企业合规要求。组织使用前应自行完成合规评估。

The project does not guarantee compliance with GDPR, personal-information laws, industry regulation, or organizational policy in any jurisdiction. Organizations must perform their own compliance review.

## 8. 删除与保留 / Deletion and retention

软件不会在维护者控制的服务器上保留你的报告。你需要自行删除本地 `runs/`、截图、日志或备份。删除本地文件不会自动删除你已上传到 GitHub、聊天工具、云盘或其他系统的副本。

The software does not retain reports on maintainer-controlled servers. You must delete local `runs/`, screenshots, logs, or backups yourself. Deleting local files does not remove copies you uploaded to GitHub, chat tools, cloud storage, or other systems.

如果误提交真实凭据，应先吊销或轮换，再清理仓库历史；仅删除文件不足以消除公开暴露风险。

If a real credential is committed by mistake, revoke or rotate it first, then clean repository history. Deleting the file alone is not enough to remove public exposure risk.

## 9. 安全事件 / Security incidents

发现数据泄露、token 暴露、报告越权访问或隐私设计问题时：

- 不要公开粘贴真实数据；
- 通过 GitHub Private Vulnerability Reporting 联系维护者；
- 提供最小化、脱敏的复现信息；
- 先轮换凭据，再评估是否需要清理历史或通知受影响方。

For data exposure, token disclosure, unauthorized report access, or privacy-design issues:

- do not paste real data publicly;
- use GitHub Private Vulnerability Reporting;
- provide minimized, redacted reproduction details;
- rotate credentials first, then assess history cleanup or notification obligations.

## 10. 相关文件 / Related documents

- [`DISCLAIMER.md`](DISCLAIMER.md)
- [`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md)
- [`SECURITY.md`](SECURITY.md)
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)
