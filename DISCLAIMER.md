# 免责声明与责任边界 / Disclaimer and Responsibility

## 1. 文件目的 / Purpose

本文件说明 `app-testbench` 的使用风险、责任边界和项目立场。它帮助用户理解项目能做什么、不能保证什么，以及使用自动化操作设备或应用时由谁承担责任。

This document explains the risks, responsibility boundaries, and project position of `app-testbench`. It helps users understand what the project does, what it cannot guarantee, and who is responsible when automating devices or applications.

本文件是项目风险说明，不构成法律意见。组织用户应根据所在地法律、应用条款、数据保护要求和内部政策咨询法务或合规人员。

This is a project risk notice, not legal advice. Organizations should consult legal or compliance professionals about applicable law, app terms, data-protection requirements, and internal policy.

## 2. 与 MIT License 的关系 / Relationship to the MIT License

`app-testbench` 按仓库根目录的 [`LICENSE`](LICENSE) 以 MIT License 发布。MIT License 已包含软件“按原样”提供、不附担保以及责任限制条款。

`app-testbench` is distributed under the MIT License in [`LICENSE`](LICENSE). The MIT License contains the software's “as is” warranty disclaimer and limitation of liability.

本文件及其他项目政策用于解释安全预期和实际操作责任，**不修改、不缩减也不替代 MIT License 授予的权利**。如果本文件与 `LICENSE` 在许可权利或法律责任上存在冲突，以 `LICENSE` 为准。

This document and other project policies explain safety expectations and practical responsibility. They **do not modify, reduce, or replace rights granted by the MIT License**. If this document conflicts with `LICENSE` regarding licensed rights or legal liability, `LICENSE` controls.

## 3. 独立项目与商标 / Independent project and trademarks

`app-testbench` 是独立开源项目，与网易、MuMu Player、Google、Android、Python、GitHub、OpenAI 或其他第三方不存在隶属、授权、赞助或官方背书关系。

`app-testbench` is an independent open-source project. It is not affiliated with, authorized by, sponsored by, or endorsed by NetEase, MuMu Player, Google, Android, Python, GitHub, OpenAI, or any other third party.

第三方名称和商标仅用于识别兼容对象、文件格式或工具。相关权利归各自所有者。详见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。

Third-party names and trademarks are used only to identify compatible targets, file formats, or tools. All rights belong to their respective owners. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## 4. 不提供担保 / No warranty

在适用法律允许的最大范围内，项目按“现状”和“可用”状态提供。维护者和贡献者不保证：

- 适用于特定目的或特定 App；
- 与任何 MuMu、Android、Windows 或 ADB 版本兼容；
- 无错误、不中断或不会产生误操作；
- 能识别所有 UI 变化、坐标偏差、弹窗、验证码或异常状态；
- 报告、截图、日志或结构化结果完整、准确或适合作为唯一决策依据；
- 修复时间、响应时间或长期维护承诺。

To the maximum extent permitted by applicable law, the project is provided “as is” and “as available.” Maintainers and contributors do not guarantee:

- fitness for a particular purpose or application;
- compatibility with any MuMu, Android, Windows, or ADB version;
- error-free, uninterrupted, or side-effect-free operation;
- detection of every UI change, coordinate mismatch, dialog, CAPTCHA, or abnormal state;
- that reports, screenshots, logs, or structured results are complete, accurate, or suitable as the sole basis for a decision;
- any response time, fix time, or long-term maintenance commitment.

## 5. 用户责任 / User responsibility

使用者应自行负责：

- 确认对设备、模拟器、应用、账号、数据和测试环境拥有合法授权；
- 遵守所在地法律、应用服务条款、软件许可、隐私要求和组织政策；
- 在执行安装、关闭、卸载、输入、点击、滑动或批量操作前做好备份并确认影响；
- 审查 flow、坐标、包名、APK 来源和外部工具路径；
- 保护截图、UI 树、logcat、报告和设备标识等敏感证据；
- 在无人值守运行前设置边界、超时、失败停止和人工复核机制；
- 评估自动化对账号、数据、业务流程和第三方服务造成的影响。

Users are responsible for:

- confirming legal authorization for devices, emulators, applications, accounts, data, and test environments;
- complying with applicable law, app terms, software licenses, privacy requirements, and organizational policy;
- backing up and understanding the impact before install, close, uninstall, input, tap, swipe, or bulk operations;
- reviewing flows, coordinates, package names, APK sources, and external tool paths;
- protecting screenshots, UI trees, logcat, reports, and device identifiers;
- adding limits, timeouts, stop-on-failure behavior, and human review before unattended execution;
- assessing the impact of automation on accounts, data, business processes, and third-party services.

## 6. 报告和证据不构成事实保证 / Reports are not proof of all facts

HTML 报告和 `result.json` 记录的是工具在执行时刻观察到的有限结果，不等于对 App 质量、账号安全、业务正确性或完整用户流程的认证。

The HTML report and `result.json` record limited observations at execution time. They are not certification of application quality, account security, business correctness, or complete user journeys.

截图可能遗漏瞬时状态，UI dump 可能无法读取 WebView、游戏或自绘界面，logcat 可能被截断或包含无关内容。重要结论应结合人工复核、独立测试和其他证据。

Screenshots may miss transient states. UI dumps may not expose WebView, game, or custom-rendered content. Logcat may be truncated or contain unrelated data. Important conclusions should be verified with human review, independent testing, and other evidence.

## 7. 第三方软件和外部服务 / Third-party software and services

项目依赖用户自行安装和控制的 MuMu Player、ADB、Android 工具链、Python 包和操作系统。第三方组件的错误、漏洞、许可变更、数据实践或服务中断不属于本项目能够控制的范围。

The project relies on user-installed and user-controlled MuMu Player, ADB, Android tooling, Python packages, and operating systems. The project cannot control third-party errors, vulnerabilities, license changes, data practices, or service interruptions.

README 中的徽章、外部链接或第三方文档可能由其他服务提供；访问这些服务时应遵守其条款和隐私政策。

Badges, external links, or third-party documentation in the README may be served by other providers. Their terms and privacy policies apply when accessed.

## 8. 无专业建议 / No professional advice

项目文档、示例、Issue 回复和 Release notes 只提供工程信息，不构成法律、合规、安全认证、财务、医疗或其他专业建议。

Project documentation, examples, issue replies, and release notes provide engineering information only. They are not legal, compliance, security-certification, financial, medical, or other professional advice.

## 9. 责任限制 / Limitation of liability

在适用法律允许的范围内，因使用或无法使用本项目而产生的间接、附带、特殊、惩罚性或后果性损失，由使用者自行承担。MIT License 中的责任限制条款适用于本项目。

To the extent permitted by applicable law, users bear the risk of indirect, incidental, special, punitive, or consequential losses arising from use or inability to use the project. The limitation of liability in the MIT License applies.

## 10. 政策更新 / Policy updates

项目可能随功能、依赖和风险变化更新本文件。发布版本中的声明以该版本仓库内容为准。发现安全、隐私或权责问题时，请通过 GitHub Issue 或 Private Vulnerability Reporting 联系维护者；不要在公开渠道粘贴敏感数据。

These notices may be updated as features, dependencies, and risks change. The repository content at a released version governs that version. Report security, privacy, or responsibility concerns through GitHub Issues or Private Vulnerability Reporting; do not post sensitive data publicly.
