# 贡献指南 / Contributing

感谢参与 / Thanks for contributing.

## 开发环境 / Development setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -q
```

项目支持 Python 3.10+，但 v0.1 的主要运行环境是 Windows 10/11、MuMu Player 和 ADB。

Python 3.10+ is supported. The primary runtime for v0.1 is Windows 10/11 with MuMu Player and ADB.

## 提交前检查 / Before a pull request

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python -m build
python -m twine check dist/*
```

或运行 / Or run:

```powershell
.\scripts\check.ps1
```

## 适合贡献的范围 / Good scope

- 真实 MuMu 版本差异和兼容性证据 / real MuMu version differences with evidence
- 更安全的 ADB 行为和更清晰的诊断 / safer ADB behavior and diagnostics
- 语义明确、带测试的 flow action / flow actions with clear semantics and tests
- 报告可读性、可访问性和稳定性 / report readability, accessibility, and reliability
- 文档、示例、打包和 CI 改进 / docs, examples, packaging, and CI

大型子系统请先开 issue 讨论。v0.1 刻意不包含 OCR、图像识别、通用 RPA、账号自动化和安全绕过。

Discuss large subsystems in an issue first. v0.1 deliberately excludes OCR, image recognition, general RPA, account automation, and security bypasses.

## 代码规则 / Code rules

- Python 3.10+，公共代码使用类型标注 / use type hints for public code
- 不使用 `shell=True` 拼接主机命令 / no host-shell construction with `shell=True`
- 外部进程调用保持在 `ProcessRunner` / adapter 后面 / keep process calls behind adapters
- 行为变化必须增加测试 / add tests for behavior changes
- 报告必须自包含并正确转义 / reports must be self-contained and escaped
- 不新增遥测或静默上传 / no telemetry or silent upload
- 保持严格 flow 校验，不静默接受拼写错误 / keep strict flow validation

## 测试与真实设备 / Tests and live devices

默认测试使用假 `adb` 和 `MuMuManager`，不需要安装模拟器。涉及真实设备行为时，在 PR 中记录：

- 测试的 MuMu 版本
- Windows 版本
- 是否实际执行了 install/launch/input/report
- 哪些行为仍只由假后端覆盖

The default suite uses fake `adb` and `MuMuManager`. For device behavior, document the tested MuMu version, Windows version, which operations were exercised live, and what remains covered only by fakes.

## 隐私要求 / Privacy requirements

- 不提交 APK、keystore、cookie、`.env`、token、私钥或证书。
- 不提交真实账号截图、logcat、UI 树或业务数据。
- 示例使用 `com.example.app`、`qa@example.com` 等明显占位值。
- 发现凭据时先轮换，再清理历史。

Do not commit APKs, keystores, cookies, `.env` files, tokens, private keys, or certificates. Do not include real screenshots, logcat, UI trees, or business data. Use obvious placeholders. Rotate exposed credentials before cleaning history.

## 提交信息 / Commit messages

推荐 Conventional Commits：

```text
feat: add ...
fix: correct ...
docs: explain ...
test: cover ...
chore: update ...
```

## 贡献许可与权利声明 / Contribution license and rights

除非你在提交时明确另行说明，提交到本项目的代码、文档、测试、示例和素材将按仓库根目录 [`LICENSE`](LICENSE) 中的 **MIT License** 授权。

Unless you explicitly state otherwise when submitting, code, documentation, tests, examples, and assets contributed to this project are licensed under the **MIT License** in [`LICENSE`](LICENSE).

提交贡献即表示你确认：

- 你有权提交该内容，且不会侵犯他人的版权、商标、专利、商业秘密或隐私；
- 第三方代码、素材或文档已获得兼容许可证和必要授权；
- 贡献中不包含客户机密、内部源码、真实账号、token、cookie 或个人数据；
- 你不会提交恶意代码、凭据窃取、未授权访问或绕过安全机制的功能。

By submitting a contribution, you confirm that:

- you have the right to submit the content and it does not infringe copyright, trademark, patent, trade-secret, or privacy rights;
- third-party code, assets, or documentation has a compatible license and any required permission;
- the contribution contains no customer confidential information, internal source code, real accounts, tokens, cookies, or personal data;
- you will not submit malware, credential theft, unauthorized access, or security-bypass functionality.

项目当前不要求单独的 CLA。维护者可以拒绝来源不明、权利不清或违反 [`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md) 的贡献。

The project does not currently require a separate CLA. Maintainers may reject contributions with unclear provenance, unclear rights, or conflicts with [`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md).

## Pull request

- 描述问题、行为变化和兼容性影响。
- 列出执行的检查。
- 说明真实设备验证情况。
- 不要在 PR 中粘贴敏感日志或截图。
- 保持变更范围集中，避免无关格式化。

Describe the problem, behavior change, and compatibility impact. List verification steps and live-device coverage. Do not paste sensitive logs or screenshots. Keep changes focused.

## 安全问题 / Security

不要公开提交漏洞。遵循 [SECURITY.md](SECURITY.md)。

Do not report vulnerabilities publicly. Follow [SECURITY.md](SECURITY.md).
