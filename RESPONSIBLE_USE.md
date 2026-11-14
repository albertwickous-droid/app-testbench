# 负责任使用声明 / Responsible Use Policy

## 1. 适用范围 / Scope

本文件说明 `app-testbench` 的预期用途和项目不支持的使用方式。它是安全与社区政策，不是额外许可证。

This document describes the intended uses and unsupported uses of `app-testbench`. It is a safety and community policy, not an additional license.

MIT License 授予的是版权许可，不授予访问任何设备、账号、网络、应用或数据的权限。即使技术上可以执行某个命令，也不代表你有权这样做。

The MIT License grants copyright permissions. It does not grant access rights to any device, account, network, application, or data. Technical capability does not imply authorization.

## 2. 预期用途 / Intended use

项目面向以下场景：

- 你拥有或获得明确授权的 Android 应用测试；
- App QA、回归测试、冒烟测试和交付验证；
- 本地模拟器自动化、流程演示和教学；
- 对合成、测试或已脱敏数据生成报告；
- 在受控环境中为 Codex 或其他工具提供结构化执行接口。

The project is intended for:

- Android application testing on devices you own or are authorized to test;
- app QA, regression testing, smoke testing, and release validation;
- local emulator automation, demonstrations, and education;
- reports generated from synthetic, test, or properly de-identified data;
- structured execution interfaces for Codex or other tools in controlled environments.

## 3. 必须获得授权 / Authorization is required

使用前必须确认：

- 你对目标设备、模拟器实例和账号拥有所有权或明确授权；
- 你有权安装、启动、关闭、输入、截图和采集目标应用日志；
- 你的测试范围、数据访问和自动化频率符合应用条款和组织政策；
- 你没有绕过访问控制、付费、地域、身份验证或其他限制。

Before use, confirm that:

- you own or are explicitly authorized to use the target device, emulator instance, and account;
- you are permitted to install, launch, close, input into, screenshot, and collect logs from the target application;
- your test scope, data access, and automation frequency comply with app terms and organizational policy;
- you are not circumventing access controls, payment, regional, identity, or other restrictions.

## 4. 不支持且不认可的使用 / Unsupported and unendorsed uses

项目不为此设计、不提供支持，也不代表维护者认可以下用途：

- 未授权访问设备、账号、企业系统或他人数据；
- 绕过登录、验证码、反作弊、风控、权限、付费墙或其他安全机制；
- 窃取凭据、cookie、token、聊天、订单、通讯录或其他敏感数据；
- 恶意软件、勒索软件、欺诈、刷量、垃圾信息、虚假注册或滥用平台资源；
- 跟踪、骚扰、监控或收集他人的私密信息；
- 破坏设备、应用、数据或第三方服务；
- 违反法律、应用条款、平台规则或组织安全政策的活动；
- 大规模无人监督操作，且没有授权、限速、停止机制和人工复核。

The project is not designed or supported for, and does not endorse:

- unauthorized access to devices, accounts, enterprise systems, or another person's data;
- bypassing login, CAPTCHA, anti-cheat, risk controls, permissions, paywalls, or other security mechanisms;
- stealing credentials, cookies, tokens, chats, orders, contacts, or other sensitive data;
- malware, ransomware, fraud, engagement manipulation, spam, fake registration, or platform abuse;
- stalking, harassment, surveillance, or collection of another person's private information;
- damaging devices, applications, data, or third-party services;
- activity that violates law, app terms, platform rules, or organizational security policy;
- large-scale unattended operation without authorization, rate limits, stop controls, and human review.

## 5. 安全操作责任 / Safe-operation responsibility

使用者应：

- 在生产账号或生产数据之外先做隔离测试；
- 对安装、关闭、卸载、覆盖和批量操作进行确认；
- 为无人值守任务设置超时、重试上限、失败停止和告警；
- 避免对第三方服务造成异常负载或滥用；
- 保留必要的审计记录，并定期清理敏感证据；
- 在发布截图、报告或日志前脱敏；
- 遵守最小权限原则，不使用管理员权限运行非必要操作。

Users should:

- test in isolation before using production accounts or data;
- confirm installation, shutdown, uninstall, overwrite, and bulk operations;
- add timeouts, retry limits, stop-on-failure behavior, and alerts for unattended jobs;
- avoid abnormal load or abuse of third-party services;
- retain necessary audit records and routinely remove sensitive evidence;
- redact screenshots, reports, and logs before sharing;
- follow least privilege and avoid administrator rights for operations that do not require them.

## 6. 不做安全绕过 / No security bypass

本项目不会提供、接受或维护以下功能：

- 绕过应用认证、授权、付费、地域或反作弊机制；
- 隐藏自动化痕迹以规避平台检测；
- 破解、注入、篡改第三方应用；
- 自动破解验证码或盗用账号；
- 规避速率限制或平台风控。

The project does not provide, accept, or maintain features that:

- bypass authentication, authorization, payment, regional, or anti-cheat mechanisms;
- hide automation to evade platform detection;
- crack, inject into, or tamper with third-party applications;
- solve CAPTCHAs for unauthorized access or hijack accounts;
- evade rate limits or platform risk controls.

## 7. 违规后果 / Consequences for misuse

维护者可以：

- 拒绝为明显违规的使用提供支持；
- 关闭或移除包含敏感数据、恶意代码或规避功能的 Issue/PR；
- 限制持续滥用社区资源或骚扰他人的参与者；
- 在必要时遵守 GitHub、法律或平台的安全要求。

Maintainers may:

- decline support for clearly abusive uses;
- close or remove issues and pull requests containing sensitive data, malicious code, or evasion features;
- restrict participants who repeatedly abuse community resources or harass others;
- comply with GitHub, legal, or platform safety requirements where necessary.

上述措施针对项目社区和支持渠道，不改变 MIT License 对已获得软件副本的授权。

These actions apply to the project community and support channels. They do not change the permissions granted by the MIT License for copies of the software already obtained.

## 8. 举报滥用或风险 / Reporting misuse or risk

如果你发现项目功能可能被用于绕过安全、泄露数据或造成现实伤害，请不要公开粘贴敏感证据。通过仓库的 GitHub Issue 提交最小化、脱敏的描述，或对安全问题使用 Private Vulnerability Reporting。

If you believe a feature could enable security bypass, data exposure, or real-world harm, do not post sensitive evidence publicly. Open a minimized, redacted GitHub Issue, or use Private Vulnerability Reporting for security matters.

## 9. 相关文件 / Related documents

- [`LICENSE`](LICENSE)：MIT 许可与责任限制 / MIT license and liability limitation
- [`DISCLAIMER.md`](DISCLAIMER.md)：免责声明与责任边界 / disclaimer and responsibility
- [`PRIVACY.md`](PRIVACY.md)：本地数据处理 / local data handling
- [`SECURITY.md`](SECURITY.md)：漏洞报告与安全边界 / vulnerability reporting
