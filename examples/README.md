# 示例 / Examples

这里只放可复现的真实 MuMu 案例。每个案例都会下载并校验固定开源 APK，所有运行产物写入被 Git 忽略的 `runs/`。

This directory contains reproducible live MuMu cases only. Each case downloads and verifies a pinned open-source APK, and all run artifacts are written under ignored `runs/` storage.

## 真实案例 / Live cases

- `ankidroid-deck-persistence/`：AnkiDroid 首次引导、创建牌组、填写问答卡片、冷启动和持久化验证。真实运行 **49/49 passed**。
- `markor-note-persistence/`：Markor 多页引导、创建 Markdown 笔记、保存、冷启动、文件搜索和正文恢复。真实运行 **46/46 passed**。

```powershell
.\examples\ankidroid-deck-persistence\run.ps1
.\examples\markor-note-persistence\run.ps1
```

AnkiDroid 脚本只清理本案例拥有的数据；Markor 默认在结束后删除 `app-testbench-*.md` 并卸载 Markor。两个脚本都会核对 APK 的包名、版本和 SHA256，运行 flow，并生成 JUnit。

The AnkiDroid script resets only case-owned state. Markor removes its `app-testbench-*.md` files and uninstalls the app by default. Both scripts verify APK identity and SHA256, run the flow, and produce JUnit output.

完整截图、结果和限制见 [`../docs/cases.md`](../docs/cases.md)。

See [`../docs/cases.md`](../docs/cases.md) for screenshots, observed results, and known limits.
