# 验证记录 / Validation Record

本页记录 App TestBench v0.1.1 在发布候选提交上的实际验证结果。结论只覆盖列出的环境、版本和案例；没有执行的项目不会被写成“应该可用”。

This page records the actual validation performed for the App TestBench v0.1.1 release candidate. Results apply only to the environments, versions, and cases listed here. Checks that were not executed are not described as expected to work.

## 验证日期 / Date

2026-11-15（Asia/Shanghai）

## 自动化门禁 / Automated gate

| 检查 | 结果 |
| --- | --- |
| 完整 pytest | **113 passed** |
| Ruff lint | passed |
| Ruff format check | 62 files already formatted |
| wheel + sdist build | `app_testbench-0.1.1-py3-none-any.whl`、`app_testbench-0.1.1.tar.gz` 构建成功 |
| `twine check` | wheel 与 sdist 均 PASSED |
| 公开截图测试 | 7 张公开 PNG 存在，尺寸符合 1280×720 或 1440×1100 |

不包含真实 MuMu 的结果不会被 CI 伪造。CI 继续使用确定性的假 `adb` / `MuMuManager` 后端验证命令构造、流程、报告和 Schema；真实案例单独在 MuMu 上执行并记录如下。

Live MuMu results are never fabricated by CI. CI uses deterministic fake `adb` and `MuMuManager` backends to verify command construction, flows, reports, and schemas. Live cases are executed separately on MuMu and recorded below.

## 干净环境 wheel 安装 / Clean wheel installation

创建新的 Python 3.11 虚拟环境，仅安装最终构建的 wheel，并使用清华 PyPI 镜像安装声明的 PyYAML 依赖。最终 wheel 已在真实 MuMu 上执行 Settings 流程和失败契约流程。

A fresh Python 3.11 virtual environment was created with only the final wheel plus its declared PyYAML dependency from the Tsinghua PyPI mirror. The final wheel was then used for live MuMu Settings and failure-contract runs.

| 检查 | 实际结果 |
| --- | --- |
| `app-testbench --version` | `app-testbench 0.1.1` |
| `app-testbench doctor --json` | `ok=true`，9 pass / 0 warn / 0 fail |
| `app-testbench skill-path` | 输出文件存在 |
| `app-testbench init` | 生成 `app-testbench-flow.yaml` |
| `app-testbench validate` | 新生成 flow 和 Markor 真实 flow 均通过 |
| 用 wheel 执行真实流程 | Android Settings flow **23/23 passed** |

## 真实 MuMu 环境 / Live MuMu environment

| 项目 | 环境 |
| --- | --- |
| 操作系统 | Windows 10.0.26100 |
| Python | 3.11.8 |
| MuMu Player | 6.8.8.0 |
| Android | 12 |
| ADB | 1.0.41 |
| MuMu 实例 | 0 |
| ADB serial | 由 MuMuManager 自动解析；不公开具体主机地址 |
| 显示 | 1280×720 |
| 系统语言 | 简体中文 |

## 案例 1：Markor 笔记持久化 / Markor note persistence

固定 APK：

```text
Package: net.gsantner.markor
Version: 2026.10.0
VersionCode: 164
Source: F-Droid official repository (with SHA256-pinned trusted mirrors)
Size: 11,849,016 bytes
SHA256: c29412e02d03e4f0511746a1bcef48c6b73fc1f70c1024fbf04903b0b3f4c485
```

执行结果：

```text
Flow status: passed
Steps: 47 passed, 0 failed, 0 skipped
Duration: 48.796 seconds
Screenshots: 5 PNG, each 1280x720
UI trees: action artifacts plus labeled final UI tree
JUnit: 47 tests, 0 failures, 0 errors
HTML report: 1,024,368 bytes
Embedded PNG files in HTML: 5
External scripts/stylesheets/imports: 0
```

覆盖内容：

1. 从受信来源下载固定 APK，并核对固定大小和 SHA256。
2. `adb install -g` 后核对包名、versionCode、versionName。
3. 清理 Markor App 数据，设置测试所需 app-op。
4. 完成首次启动引导，处理版本说明弹窗。
5. 创建笔记、聚焦编辑器、输入 ASCII 正文。
6. 保存前断言正文出现在 UI。
7. 保存、强制停止、冷启动。
8. 通过文件搜索重新打开笔记。
9. 断言正文在冷启动后仍然存在。
10. 收集截图、UI 树、logcat、JSON、HTML、JUnit。

公开证据：

- [`docs/cases.md`](cases.md)
- [`examples/markor-note-persistence/`](../examples/markor-note-persistence/)
- [`docs/assets/cases/markor/`](assets/cases/markor/)

## 案例 2：Android Settings 导航与滚动 / Android Settings navigation and scroll

执行结果：

```text
Flow status: passed
Steps: 23 passed, 0 failed, 0 skipped
Duration: 26.750 seconds
JUnit: 23 tests, 0 failures, 0 errors
HTML report: 678,746 bytes
Embedded PNG files in HTML: 3
External scripts/stylesheets/imports: 0
```

覆盖内容：

1. 启动 MuMu 镜像自带的 AOSP Settings。
2. 将 Android 恢复的上次滚动位置显式复位。
3. 进入“网络和互联网”，等待并断言页面文本。
4. 保存截图和 UI 树。
5. 返回首页，确认返回栈后的内容。
6. 连续滚动到系统区域，等待并断言“关于手机”入口。
7. 关闭 App，收集 logcat、JSON、HTML、JUnit。

这条案例同时保留了一份真实失败报告：第一次 flow 直接假设 Settings 从首页顶部打开，但 Android 恢复了上次的滚动位置。失败报告包含错误步骤、可见文本、失败截图、UI 树、logcat、HTML 和 JUnit。修复没有放宽断言，而是先归一化起始状态。

This case also retains a real failed report. The first flow assumed Settings opened at the top, but Android restored the previous scroll position. The report contains the failed step, visible text, failure screenshot, UI tree, logcat, HTML, and JUnit. The fix normalizes the initial state rather than weakening the assertion.

公开证据：

- [`examples/settings-network-scroll/`](../examples/settings-network-scroll/)
- [`docs/assets/cases/settings/`](assets/cases/settings/)

## 失败 JSON 契约 / Failed JSON contract

### v0.1.0 的问题 / v0.1.0 problem

真实失败运行输出为：

```json
{
  "ok": false,
  "data": {
    "status": "failed"
  }
}
```

退出码是 `1`，但 `cli-v1.schema.json` 在 `ok=false` 时要求存在 `error` 对象，因此该 envelope 无法通过公开 Schema。

The exit code was `1`, but `cli-v1.schema.json` requires an `error` object when `ok=false`, so the envelope did not satisfy the published schema.

### v0.1.1 的结果 / v0.1.1 result

真实失败流程现在输出：

```json
{
  "ok": false,
  "error": {
    "type": "step_failure",
    "message": "Flow step 'Fail on a deliberately absent assertion' failed: UI text was not found: APP_TESTBENCH_EXPECTED_MISSING_TEXT",
    "hint": "Visible text: ..."
  },
  "data": {
    "status": "failed"
  }
}
```

验证结果：

```text
Process exit code: 1
CLI envelope vs packaged cli-v1.schema.json: PASS
result.json vs packaged result-v1.schema.json: PASS
Error type: step_failure
Successful pre-failure steps retained: 3
Failed steps: 1
Failure screenshot: present
Failure UI tree: present
Final logcat: present
HTML report: 364,827 bytes, self-contained
JUnit: 4 tests, 1 failure, 0 errors
```

回归测试 `test_failed_run_json_matches_cli_schema` 会执行失败 flow，并直接用打包后的 `cli-v1.schema.json` 校验真实 `main([...])` 输出。Schema 没有被放宽。

The regression test `test_failed_run_json_matches_cli_schema` executes a failed flow and validates the actual `main([...])` output against the packaged `cli-v1.schema.json`. The schema was not relaxed.

## HTML 与截图检查 / HTML and screenshot checks

- 成功与失败报告都能离线打开。
- HTML 内包含 `data:image/png;base64,...` 截图，不依赖 CDN。
- 检测到的外部 script、stylesheet 和 CSS import 数量均为 0。
- 公开截图来自真实运行，不是 AI 生成或手绘模拟。
- 原始 APK、完整运行目录、原始 logcat、UI XML 和未筛选报告保留在被 `.gitignore` 排除的 `runs/` 中。

- Passed and failed reports open offline.
- HTML embeds screenshots as `data:image/png;base64,...` and does not depend on a CDN.
- External script, stylesheet, and CSS-import counts were all zero.
- Public screenshots come from live runs, not AI generation or hand-drawn mockups.
- Raw APKs, complete run directories, logcat, UI XML, and unselected reports remain under the ignored `runs/` directory.

## 未覆盖范围 / Not covered

- 没有验证所有 MuMu Player、Android、ADB、Windows、分辨率或语言组合。
- Markor 和 Settings 的坐标及中文文本依赖当前 1280×720 / 简体中文镜像。
- `text` 仍只支持可打印 ASCII。
- 没有 OCR 或图像模板匹配；WebView、游戏引擎和自绘界面可能无法通过 UI 树稳定定位。
- Wikipedia 做过真实安装和首次启动调查，但 Wikimedia 端点在该实例中网络超时，因此没有列为成功案例。
- 物理设备仍应作为最终验收环境。

- Not every MuMu Player, Android, ADB, Windows, display, or language combination was tested.
- Markor and Settings coordinates and Chinese text depend on the current 1280×720 Simplified Chinese image.
- Native `text` remains printable-ASCII only.
- No OCR or image-template matching is provided; WebViews, game engines, and custom-rendered surfaces may not expose stable text through the UI hierarchy.
- Wikipedia was installed and launched during investigation, but Wikimedia endpoints timed out from the test instance, so it is not presented as a successful case.
- Physical devices remain the final acceptance environment.
