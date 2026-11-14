# 安全策略 / Security Policy

## 报告漏洞 / Reporting a vulnerability

请**不要**为安全问题创建公开 issue。

Do **not** open a public issue for a vulnerability.

请使用本仓库 GitHub Security 页面中的 **Private Vulnerability Reporting**。如果该项尚未启用，请先联系维护者建立私密渠道，不要把利用细节发到公开讨论区。

Use **Private Vulnerability Reporting** from this repository's GitHub Security page. If it is not enabled yet, contact the maintainers privately first; do not post exploitation details publicly.

报告中请包含 / Include:

- 受影响版本 / affected version
- 复现步骤 / reproduction steps
- 影响与攻击前提 / impact and preconditions
- 是否需要恶意 flow、APK、本地二进制或报告文件 / whether a malicious flow, APK, local binary, or report is required
- 已知缓解方式 / suggested mitigation
- 脱敏后的日志或最小样本 / redacted logs or a minimal sample

## 支持版本 / Supported versions

| Version | Supported |
| --- | --- |
| `0.1.x` | Yes / 是 |
| `< 0.1` | No / 否 |

安全修复会优先进入最新的 `0.1.x` 版本；发布 patch 后再更新本表。

Security fixes target the latest `0.1.x` release. Update this table after each patch release.

## 适用范围 / In scope
- 命令注入或参数注入 / command or argument injection
- HTML/report 渲染不安全 / unsafe HTML or report rendering
- 路径穿越、覆盖用户文件 / path traversal or unexpected file overwrite
- 截图、日志、token、设备数据的意外泄露 / unintended disclosure of screenshots, logs, tokens, or device data
- 相对本地 MuMu/ADB 进程的权限提升 / privilege escalation relative to local MuMu/ADB processes
- 打包、依赖或 CI 供应链问题 / packaging, dependency, or CI supply-chain weaknesses
- Secret scanning 发现真实凭据 / real credentials exposed to secret scanning

## 不适用范围 / Out of scope

- MuMu、ADB、Android 或第三方应用自身的漏洞 / vulnerabilities in MuMu, ADB, Android, or third-party applications
- 未授权的设备或账号访问 / unauthorized device or account access
- 社会工程 / social engineering
- 仅由故意畸形的第三方二进制造成的拒绝服务 / denial of service caused solely by intentionally malformed third-party binaries
- 用户主动运行恶意 APK 或恶意 flow 产生的后果 / consequences of intentionally running a malicious APK or flow

## 安全边界 / Security boundaries

- 外部命令通过参数数组调用，不使用 `shell=True` 拼接主机命令。
- ADB 文本输入会处理 Android shell 字符，但原生 `input text` 仍有平台限制。
- 报告对用户提供的文本进行 HTML 转义，且不加载外部资源。
- 项目没有遥测，不上传报告或设备数据。
- 报告是本地敏感证据，不是加密容器或访问控制边界。

## 数据警告 / Data warning

`runs/`、截图、UI XML 和 logcat 可能包含账号、聊天、订单、个人资料、设备标识、URL 或 token。把它们视为机密证据，不要提交到 Git，也不要直接粘贴到 issue。

`runs/`, screenshots, UI XML, and logcat may contain accounts, chats, orders, personal data, device identifiers, URLs, or tokens. Treat them as confidential evidence. Do not commit them or paste them into issues.

## 协调披露 / Coordinated disclosure

维护者会先确认影响、准备修复与回归测试，再与报告者协调公开时间。请给维护者合理的修复窗口，不要在修复发布前公开利用细节。

Maintainers will validate impact, prepare a fix and regression coverage, and coordinate disclosure timing with the reporter. Allow a reasonable remediation window before publishing exploitation details.

## 凭据泄露处理 / Credential exposure

如果发现真实凭据：先吊销或轮换，再清理仓库和历史。公开仓库内容可能已经被缓存或抓取，单纯删除文件不等于安全。

If a real credential is exposed, revoke or rotate it first, then clean the repository and its history. Public content may already be cached or scraped; deleting a file alone is not sufficient.
## 相关权责文件 / Related responsibility documents

- [`DISCLAIMER.md`](DISCLAIMER.md)：免责声明与责任边界 / disclaimer and responsibility
- [`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md)：授权测试与滥用边界 / authorized testing and misuse boundaries
- [`PRIVACY.md`](PRIVACY.md)：本地数据与敏感证据处理 / local data and sensitive evidence
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)：第三方商标与依赖 / third-party trademarks and dependencies
