# Agent 部署手册 / Agent Deployment Runbook

> If you are an agent, follow this runbook to deploy App TestBench.
>
> 如果你是执行部署任务的 Agent：请按以下步骤部署 App TestBench。不要重新设计产品，不要跳过验证，也不要自行切换仓库可见性、创建 tag、发布 GitHub Release 或 PyPI 包。

## 1. 任务目标

把当前仓库安全地发布到：

- Owner：`albertwickous-droid`
- Repository：`app-testbench`
- 初始可见性：**Private**
- 默认分支：`main`

第一阶段只要求完成：

1. 本地检查通过。
2. 首次 push 成功。
3. Private 仓库的 CI 通过。
4. GitHub 的 About、topics、安全功能和仓库策略配置完成。

切 Public、打 `v0.1.0` tag、发布 Release、触发 PyPI 都必须获得仓库所有者明确确认。

## 2. 先读这些文件

按顺序读取：

1. `README.md`
2. `AGENTS.md`
3. `docs/publishing.md`
4. `docs/github-repository-setup.md`
5. `RELEASE_CHECKLIST.md`
6. `docs/use-cases.md`
7. `SECURITY.md`
8. `PRIVACY.md`
9. `RESPONSIBLE_USE.md`

发生冲突时，以更保守、更少暴露数据、更少改变外部状态的做法为准。

## 3. 不可跳过的规则

- 不向聊天、命令行参数、提交、Issue 或日志中写入 token、密码、cookie、私钥或 GitHub 凭据。
- 不提交 `runs/`、真实截图、真实 logcat、APK、账号数据、`.env`、本机 Codex 配置或个人介绍。
- 不执行 `git push --force`，不改写已有公开历史。
- 不使用 `shell=True`，不为了部署临时修改产品代码或扩大依赖。
- CI 失败时修复并重新运行，不通过跳过检查、删除测试或降低断言来“通过”。
- 未获得明确许可，不把 Private 仓库切成 Public。
- 未完成真实 MuMu 冒烟测试时，不声称所有 MuMu/App 环境已验证。
- Git tag、GitHub Release 和 PyPI 发布是三个独立动作，不能假设其中一个会自动完成另外两个。
- 遇到真实密钥泄露，先停止发布并提醒所有者轮换凭据；不要只删除文件后继续。

## 4. 部署前检查

在仓库根目录运行：

```powershell
git status --short
git log -3 --oneline --decorate
git remote -v
git config user.name
git config user.email
```

预期：

- 工作区为空。若不是，先确认改动来源，不要擅自丢弃。
- 当前分支是 `main`。
- remote 指向 `https://github.com/albertwickous-droid/app-testbench.git`。
- commit 使用项目身份，不包含私人邮箱。

运行完整门禁：

```powershell
.\scripts\check.ps1 -SkipInstall
git diff --check
```

门禁必须包含：

- Ruff 检查通过。
- 格式检查通过。
- 全部测试通过。
- wheel 与 sdist 构建成功。
- `twine check` 通过。

检查 Git 跟踪文件中是否有不应发布的内容：

```powershell
git ls-files | Select-String -Pattern '(^|/)(\.env|runs|reports|artifacts|dist|build)(/|$)|\.(apk|aab|xapk|log|pem|key|p12|pfx)$|(^|/)(cookies\.(txt|json)|auth\.json|secrets\.)'
```

该命令应无输出。若命中，停止 push，逐个确认文件来源和敏感性。

## 5. 创建 GitHub 仓库

先检查远程仓库是否存在：

```powershell
git ls-remote --heads origin main
```

如果返回 404、认证失败或提示仓库不存在：

1. 请仓库所有者创建空仓库。
2. Owner 选择 `albertwickous-droid`。
3. 名称填写 `app-testbench`。
4. 可见性选择 **Private**。
5. 不勾选 README、`.gitignore` 或 License。
6. 不要向 Agent 提供 GitHub 密码或 token；使用 Git Credential Manager 或浏览器登录。

仓库创建后再次运行 `git ls-remote --heads origin main`。空仓库返回空结果属于正常现象。

## 6. 推送主分支

```powershell
git push -u origin main
git ls-remote --heads origin main
git status --short
```

要求：

- push 使用普通 `git push`，不使用 force。
- `origin/main` 的 commit 应与本地 `HEAD` 一致。
- push 后确认 GitHub 默认分支为 `main`。

如果认证失败，优先打开浏览器完成 GitHub 登录。不要把凭据粘贴到终端输出或聊天中。

## 7. 等待 CI

如果 `gh` 已安装并完成认证：

```powershell
gh auth status
gh run list --limit 5
gh run watch <RUN_ID> --exit-status
```

如果没有 `gh`，打开仓库的 **Actions** 页面，等待 `CI` workflow 完成。

必须通过后再继续：

- Windows Python 3.10、3.11、3.12
- Ubuntu Python 3.10、3.11、3.12
- 打包构建与安装检查

CI 失败时：

1. 读取失败 job 的完整日志。
2. 在本地复现并修复。
3. 重新运行门禁。
4. commit 并 push。
5. 再次等待 CI 全绿。

不要通过关闭 matrix、跳过测试或忽略错误来绕过失败。

## 8. 配置 Private 仓库

在 GitHub 仓库设置中完成：

### About

- Description：`Repeatable Android app testing on MuMu Player with JSON/YAML flows and evidence-rich HTML reports.`
- Website：暂不填写，除非已有正式主页。
- Topics：
  `android`, `app-testing`, `adb`, `mumu`, `android-automation`, `qa`, `regression-testing`, `python`, `cli`, `html-report`
- Social preview：上传 `assets/social-preview.png`

### Code security and analysis

开启：

- Dependabot alerts
- Dependabot security updates
- Secret scanning
- Secret scanning push protection
- Private vulnerability reporting
- CodeQL default setup for Python

### General

- Default branch：`main`
- Releases：允许，但先保持 Draft
- Automatically delete head branches：按维护习惯开启

### Actions

- Workflow permissions：默认只读
- 只给 release job 授予 `contents: write`
- 只给 PyPI job 授予 `id-token: write`
- Release workflow 只能创建 Draft，不能自动公开
- PyPI workflow 必须手动触发

### Rulesets

为 `main` 配置：

- 禁止删除分支
- 禁止 force push
- 要求 CI 状态检查
- 单人维护阶段允许管理员 bypass
- 有第二名维护者后再要求 PR approval

为 `v*` 配置：

- 只允许维护者创建和删除
- 已发布 tag 不允许移动

## 9. 切换 Public 前的硬门槛

只有同时满足以下条件，才向仓库所有者请求公开许可：

- `main` 已 push。
- 所有 CI job 通过。
- Secret scanning 和 push protection 已开启。
- 仓库中没有个人介绍、私人邮箱、真实账号、cookie、token、APK、真实截图或 logcat。
- `LICENSE`、`SECURITY.md`、`PRIVACY.md`、`RESPONSIBLE_USE.md` 和 `DISCLAIMER.md` 均可正常访问。
- README 首屏能说明用途、支持范围和限制。
- 仓库所有者明确确认可以切 Public。

得到明确确认后再切换。不要因为“CI 已通过”自行公开。

## 10. Release 与 PyPI 门槛

### GitHub Release

创建 `v0.1.0` tag 前确认：

- 仓库所有者明确批准。
- 真实 MuMu 冒烟测试已完成并记录 MuMu 版本、Windows 版本、Python 版本和测试结果。
- Release notes 没有把 fake-backend 测试写成真实设备验证。

获得批准后：

```powershell
git tag -a v0.1.0 -m "App TestBench v0.1.0"
git push origin v0.1.0
```

Release workflow 只应生成 Draft。检查 wheel、sdist、SHA256 和 Release notes 后再手动发布。

### PyPI

PyPI 不与 Git tag 自动联动。只有仓库所有者明确要求时才触发 `publish-pypi.yml`，并确认：

- PyPI Trusted Publishing 已配置相同 owner/repository/workflow/environment。
- `pypi` environment 已配置。
- 包名 `app-testbench` 和目标版本已再次确认。
- 发布后验证 `pip install app-testbench` 和 CLI 入口。

## 11. 停止条件

出现以下任一情况时停止并报告，不继续做外部状态变更：

- 仓库仍返回 404，或当前登录账号没有目标仓库权限。
- 工作区有来源不明的改动。
- 完整门禁失败。
- 发现真实密钥、cookie、token、私钥或个人信息。
- CI 未全绿。
- 真实 MuMu 测试尚未完成，却被要求宣称已兼容。
- 所有者没有明确确认 Public、tag、Release 或 PyPI。
- 需要 force push、改写公开历史或关闭安全检查才能继续。

## 12. 完成后的报告格式

Agent 完成后只报告可验证事实：

```text
Repository:
Default branch:
Latest commit:
Remote:
Visibility:
Checks:
CI:
Tag:
GitHub Release:
PyPI:
Live MuMu smoke test:
Outstanding risks:
```

不要把“本地检查通过”写成“真实设备已验证”，也不要把“Draft Release 已生成”写成“已经正式发布”。
