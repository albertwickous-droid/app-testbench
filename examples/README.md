# 示例 / Examples

这里的示例分成两类：可直接在真实 MuMu/Android 环境复现的案例，以及使用虚构包名的模板。

The examples fall into two groups: reproducible cases for a live MuMu/Android environment, and templates that use intentionally fictional package names.

## 真实案例 / Real cases

- `markor-note-persistence/`：从官方 F-Droid 下载并校验固定 APK，创建笔记，保存，冷启动，搜索并重新打开，断言正文持久化。真实运行 47/47 步通过 / downloads and verifies a pinned F-Droid APK, then verifies note persistence across a cold launch; 47/47 live steps passed.
- `settings-network-scroll/`：在 MuMu 自带 Android Settings 中验证滚动位置复位、嵌套导航、返回栈和长列表滚动。真实运行 23/23 步通过 / verifies restored-state normalization, nested navigation, back-stack behavior, and long scrolling in the bundled Android Settings app; 23/23 live steps passed.

完整运行结果、截图和限制见 [`../docs/cases.md`](../docs/cases.md)。

See [`../docs/cases.md`](../docs/cases.md) for live results, screenshots, and limits.

```powershell
.\examples\markor-note-persistence\run.ps1
app-testbench run .\examples\settings-network-scroll\flow.yaml --output .\runs\examples\settings-network-scroll --wait-for-boot
```

## 模板 / Templates

这些流程只使用虚构的包名、凭据和 APK 路径。请替换成你有权测试的应用、坐标和构建。

These flows use fictional package names, credentials, and APK paths. Replace them with an application, coordinates, and build that you are authorized to test.

```powershell
app-testbench validate .\examples\smoke.yaml
app-testbench run .\examples\smoke.yaml --output .\runs
```

- `smoke.yaml`：最短的启动、UI、截图和报告流程 / shortest launch, UI, screenshot, and report flow
- `smoke.json`：等价的 JSON 结构 / equivalent JSON shape
- `login-search.yaml`：包含文本输入、等待、截图和 teardown 的较大流程 / larger flow with text input, waits, screenshots, and teardown

`validate` 只检查 schema，不要求 `app.apk` 存在。`run` 需要真实 APK 路径、可用的 MuMu 实例和 ADB。

`validate` checks the schema only and does not require `app.apk` to exist. `run` requires a real APK path, a working MuMu instance, and ADB.

示例中的 `qa@example.com` 和 `example-password` 是明显占位值，不是可用账号。

The values `qa@example.com` and `example-password` are obvious placeholders, not working credentials.
