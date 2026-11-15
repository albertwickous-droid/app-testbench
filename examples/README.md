# 示例 / Examples

这里的示例分为可复现的真实 MuMu 案例与虚构包名模板。真实案例会下载并校验固定开源 APK；模板不包含真实应用或凭据。

The examples include reproducible live MuMu cases and templates with fictional package names. Live cases download and verify pinned open-source APKs; templates contain no real app or credentials.

## 真实案例 / Live cases

- `fennec-local-web-session/`：真实 Fennec 浏览器完成首次引导、登录、异步搜索、详情、冷启动和 `localStorage` 持久化。真实运行 **71/71 passed**。
- `vlc-http-playback/`：真实 VLC 通过 ADB-reversed Range 服务器播放 H.264/AAC MP4，并验证首次教程、横屏、播放控件和 MediaCodec logcat 证据。真实运行 **30/30 passed**。

```powershell
.\examples\fennec-local-web-session\run.ps1
.\examples\vlc-http-playback\run.ps1
```

这两个脚本会从官方 F-Droid 下载并校验 APK，将二进制写入 `runs/case-assets/`，运行 doctor、flow 和 JUnit，并在结束时只停止自己启动的本地服务。完整说明、结果和限制见 [`../docs/cases.md`](../docs/cases.md)。

The scripts download and verify APKs from the official F-Droid repository, keep binaries under `runs/case-assets/`, run doctor, the flow, and JUnit, and stop only the local services they started. See [`../docs/cases.md`](../docs/cases.md) for complete evidence and limits.

## 模板 / Templates

这些 flow 使用虚构包名、凭据和 APK 路径。请替换为你已获授权测试的应用、坐标和构建。

These flows use fictional package names, credentials, and APK paths. Replace them with an application, coordinates, and build you are authorized to test.

```powershell
app-testbench validate .\examples\smoke.yaml
app-testbench run .\examples\smoke.yaml --output .\runs
```

- `smoke.yaml`：最短的启动、UI、截图和报告 flow
- `smoke.json`：等价的 JSON 结构
- `login-search.yaml`：包含文本输入、等待、截图和 teardown 的较大 flow

`qa@example.com` 和 `example-password` 是显而易见的占位值，不是可用账号。

`qa@example.com` and `example-password` are obvious placeholders, not working credentials.