# 验证记录 / Validation Record

本页记录 App TestBench v0.1.0 在当前发布候选版本上的实际验证结果。测试结论只覆盖列出的环境与范围。

This page records the actual validation performed for the App TestBench v0.1.0 release candidate. Results apply only to the environments and scope listed here.

## 验证日期 / Date

2026-11-15（Asia/Shanghai）

## 自动化测试 / Automated checks

| 检查 | 结果 |
| --- | --- |
| 本地完整门禁 | 108 passed；Ruff、格式检查、构建和 `twine check` 通过 |
| GitHub Actions `CI` | Windows 与 Ubuntu 的 Python 3.10、3.11、3.12 全部通过；`Build package` 通过 |
| 代码基线 | `6105f3387c295e32f5df0abc2fd2b72f77b17a7f` |
| 干净虚拟环境安装 | wheel 安装成功 |
| CLI 冒烟 | `--version`、`--help`、`skill-path`、`init --format json` 通过 |

GitHub Actions run：

```text
https://github.com/albertwickous-droid/app-testbench/actions/runs/43629188207
```

## 真实 MuMu 冒烟测试 / Live MuMu smoke test

| 项目 | 环境 |
| --- | --- |
| 操作系统 | Windows 10.0.26100 |
| Python | 3.11.8 |
| MuMu Player | 6.8.8.0 |
| Android | 12.0 |
| ADB | 1.0.41 |
| MuMu 实例 | 0，端口 `16384` |
| 被测 App | Android 系统设置 `com.android.settings` |

执行内容：

1. 启动 MuMu 实例并等待 Android 启动完成。
2. 运行 `doctor`，9 项检查全部通过。
3. 启动 Android 系统设置。
4. 等待界面渲染。
5. 断言 UI 中存在文本“网络和互联网”。
6. 截取一张 1280×720 PNG。
7. 保存包含 48 个节点的 UI 树。
8. 收集 500 行 logcat。
9. 关闭系统设置并停止 MuMu 实例。
10. 生成 HTML、JSON 和 JUnit 报告。

结果：

```text
Flow status: passed
Steps: 7 passed, 0 failed, 0 skipped
Duration: 12.579 seconds
Screenshot: 1280x720 PNG
UI hierarchy: 48 nodes
JUnit: 7 tests, 0 failures, 0 errors
HTML report: 2,255,459 bytes
Embedded PNG images: 7
External scripts/stylesheets: 0
```

HTML 中出现的日志 URL 来自 Android 系统 logcat 文本，不是页面依赖；报告没有加载外部脚本、样式表或字体。

URLs appearing in the HTML came from Android logcat text, not page dependencies. The report loads no external scripts, stylesheets, or fonts.

## 未覆盖范围 / Not covered

- 没有使用真实业务 App、真实用户账号或生产数据。
- 没有在真实 MuMu 环境中执行 APK 安装；安装、包名和版本核验由自动化测试中的假 ADB 后端覆盖。
- 没有验证所有 MuMu Player、Android 镜像、分辨率或 Windows 版本。
- UI 树的可读文本取决于 App 的 Android View 实现；WebView、游戏引擎和自绘界面可能无法提供稳定文本。
- 物理设备仍应作为最终验收环境。

- No real business app, user account, or production data was used.
- APK installation was not exercised against the live MuMu instance; install, package identity, and version checks are covered by deterministic fake ADB tests.
- Not every MuMu Player release, Android image, resolution, or Windows version was tested.
- UI hierarchy readability depends on the app's Android View implementation; WebViews, game engines, and custom-rendered surfaces may not expose stable text.
- Physical devices remain the final acceptance environment.

## 复现方式 / Reproduction

```powershell
.\scripts\check.ps1 -SkipInstall
app-testbench doctor --json
app-testbench instance start 0 --wait 120 --json
app-testbench launch com.android.settings --json
app-testbench screenshot --output .\runs\smoke\settings.png --json
app-testbench dump-ui --output .\runs\smoke\settings.xml --json
app-testbench instance stop 0 --json
```

完整 flow、HTML 报告和 logcat 属于本地运行证据，默认由 `.gitignore` 排除，不进入公开仓库。
Full flow artifacts, HTML reports, and logcat are local run evidence and are excluded from the public repository by default.
