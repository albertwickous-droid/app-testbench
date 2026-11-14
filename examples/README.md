# 示例 / Examples

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
