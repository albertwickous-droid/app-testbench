# 支持 / Support

## 先看文档 / Read first

- [中文 README](README.md)
- [English README](README.en.md)
- [Flow reference](docs/flow-reference.md)
- [Architecture](docs/architecture.md)
- [Troubleshooting and limits](README.md#已知边界)
- [Security policy](SECURITY.md)
- [Responsible use](RESPONSIBLE_USE.md)
- [Privacy and data handling](PRIVACY.md)
- [Disclaimer](DISCLAIMER.md)

请先运行 / Start with:

```powershell
app-testbench --version
app-testbench doctor --json
app-testbench instance list --json
```

提交问题时附上版本、Windows/Python 版本、MuMu 版本、命令、预期结果和脱敏后的错误信息。不要附 cookie、token、账号截图、完整 logcat 或真实业务数据。

Include the version, Windows/Python version, MuMu version, command, expected behavior, and redacted error details. Never include cookies, tokens, account screenshots, full logcat, or real business data.

## 使用问题 / Usage questions

如果仓库启用了 Discussions，优先在 Q&A 分类提问；否则使用 bug template 并明确标记为“usage question”。使用问题请尽量提供最小复现。

If Discussions are enabled, use Q&A. Otherwise use the bug template and state that it is a usage question. Provide the smallest possible reproduction.

## Bug 报告 / Bug reports

使用 GitHub bug report form，并包含：

- `app-testbench --version`
- Windows 和 Python 版本
- MuMu Player 版本
- `doctor --json` 的脱敏输出
- 触发问题的 CLI 命令或最小 flow
- 结构化错误 `result.json` 的脱敏片段
- 已尝试的排查方式

Do not attach APKs, keystores, emulator images, private screenshots, or unredacted logs. If evidence is essential, describe the relevant UI text or recreate it with synthetic data.

## 功能请求 / Feature requests

说明问题、使用场景、现有替代方案和对 DSL/CLI 的影响。首版刻意保持“小而完整的执行层”，大平台、OCR、视觉识别、账号自动化和安全绕过不在默认范围内。

Describe the problem, use case, current workaround, and impact on the DSL/CLI. v0.1 deliberately stays a small execution layer. General RPA platforms, OCR/vision matching, account automation, and security bypasses are outside the default scope.

## 安全漏洞 / Security vulnerabilities

不要公开提交 issue。使用 GitHub **Private Vulnerability Reporting**，按 [SECURITY.md](SECURITY.md) 提供复现和影响说明。

Do not open a public issue. Use GitHub **Private Vulnerability Reporting** and follow [SECURITY.md](SECURITY.md).

## 响应说明 / Response expectations

这是一个由贡献者维护的开源项目，不承诺商业 SLA。维护者会优先处理可复现的回归、安全问题和有明确使用价值的范围内改进。

This is a contributor-maintained open-source project with no commercial SLA. Reproducible regressions, security reports, and scoped improvements with clear value are prioritized.

## 隐私 / Privacy

报告、截图、UI XML 和 logcat 可能包含敏感数据。分享前请自行脱敏；不要依赖维护者替你清理真实凭据。

Reports, screenshots, UI XML, and logcat may contain sensitive data. Redact before sharing. Do not rely on maintainers to remove real credentials.

## 使用权责 / Usage responsibility

本项目只面向你有权测试的设备、应用和账号，不提供未授权访问、绕过登录/验证码/反作弊或规避平台风控的支持。使用前请阅读 [RESPONSIBLE_USE.md](RESPONSIBLE_USE.md) 和 [DISCLAIMER.md](DISCLAIMER.md)。

The project is intended only for devices, applications, and accounts you are authorized to test. It does not support unauthorized access, bypassing login/CAPTCHA/anti-cheat controls, or evading platform risk controls. Read [RESPONSIBLE_USE.md](RESPONSIBLE_USE.md) and [DISCLAIMER.md](DISCLAIMER.md) before use.
