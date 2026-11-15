# 发布方案 / GitHub Publishing Guide

本文是 `app-testbench` v0.1.1 的增量发布操作方案。当前目标版本为 **v0.1.1**；`v0.1.0` 已经公开，必须保留原 tag，不重写已发布历史。

This is the incremental publishing runbook for App TestBench v0.1.1. The target version is **v0.1.1**. `v0.1.0` is already public; keep its tag unchanged and do not rewrite published history.

> 仓库 owner 已确认：`albertwickous-droid`。不要在没有最终检查的情况下执行 `tag` 或发布。
>
> The confirmed repository owner is `albertwickous-droid`. Do not run `tag` or any release action before the final review.

> Agent 执行入口：如果你是由 Agent 执行的部署任务，先按 [`agent-deployment.md`](agent-deployment.md) 操作。
>
> Agent entry point: if an agent is executing the deployment, follow [`agent-deployment.md`](agent-deployment.md) first.

## 0. 当前发布路径：v0.1.1 / Current path: v0.1.1

`v0.1.0` 已经公开并保留原 tag。v0.1.1 是增量补丁版本，不得重新初始化仓库、改写已发布历史或移动 `v0.1.0`。

`v0.1.0` is already public and its tag must remain unchanged. v0.1.1 is an incremental patch release. Do not reinitialize the repository, rewrite published history, or move `v0.1.0`.

1. 从最新 `main` 创建 `release/v0.1.1`，保留并分类工作区已有改动。
2. 更新版本、CHANGELOG、真实案例、验证记录和 release notes。
3. 运行完整测试、构建、`twine check`、真实 MuMu 流程和敏感信息审计。
4. 按逻辑拆分 commit，推送 release 分支并等待 GitHub Actions。
5. 合并到 `main`，确认远端 `main` 与本地一致。
6. 创建并推送新的 annotated tag `v0.1.1`；绝不移动 `v0.1.0`。
7. 检查 Release workflow 生成的 draft、wheel、sdist、`SHA256SUMS.txt` 和双语说明，再决定是否公开 Release。
8. 按 [`promotion.md`](promotion.md) 和 [`launch-copy.md`](launch-copy.md) 使用真实案例截图做后续宣传。

1. Create `release/v0.1.1` from the latest `main` and classify any existing worktree changes.
2. Update versions, CHANGELOG, live cases, validation, and release notes.
3. Run the full test/build gate, `twine check`, live MuMu flows, and the sensitive-content audit.
4. Commit in logical slices, push the release branch, and wait for GitHub Actions.
5. Merge to `main` and verify that remote and local `main` match.
6. Create and push a new annotated `v0.1.1` tag; never move `v0.1.0`.
7. Review the draft Release, wheel, sdist, `SHA256SUMS.txt`, and bilingual notes before publishing the Release.
8. Use the real case evidence in [`promotion.md`](promotion.md) and [`launch-copy.md`](launch-copy.md) for subsequent promotion.

## 1. 发布定位 / Release positioning

**中文**

- v0.1.1 的外层钩子是“AI 可以写测试，但测试环境不能靠猜”，内层定位是“基于成熟 MuMu 运行时、可重复、可留证据的 App 自动化测试工具”，不是通用 RPA 平台。
- 首版明确支持 Windows、MuMu Player 和 ADB。
- 自动化测试使用确定性的假后端；CI 通过不等于所有 MuMu 版本都完成真实集成验证。
- 仓库不包含遥测、账号体系、云端服务或用户数据上传。
- 代码采用 MIT License，作者统一写作 `app-testbench contributors`，不公开个人身份信息。

**English**

- The outer hook for v0.1.1 is “AI can write the test; it should not guess the test environment.” The precise positioning is a repeatable, evidence-rich app testing tool built on the mature MuMu runtime, not a general-purpose RPA platform.
- The supported baseline is Windows, MuMu Player, and ADB.
- Automated tests use deterministic fake backends. CI success does not claim live compatibility with every MuMu release.
- The project has no telemetry, account system, cloud service, or artifact upload.
- The code is MIT licensed. Copyright is attributed to `app-testbench contributors`, without personal identity details.

## 2. 公开与私有边界 / Public vs. private boundary

| 内容 / Content | GitHub 公开 / Public | 说明 / Rule |
| --- | --- | --- |
| `src/`, `tests/`, `examples/`, `skills/` | 是 / Yes | 核心代码、测试、示例与 Codex skill |
| `docs/`, README, policies | 是 / Yes | 不含个人身份、真实账号或本机路径 |
| `.github/workflows/`, templates | 是 / Yes | Release 只创建草稿；PyPI 必须手动触发 |
| 通用维护自动化 | 是 / Yes | 必须先移除姓名、用户名和绝对路径 |
| `assets/banner.svg`, social preview | 是 / Yes | 不得包含个人或账号数据 |
| `runs/`, `reports/`, `artifacts/` | 否 / No | 可能包含真实截图、UI、logcat 和设备信息 |
| APK、AAB、XAPK、模拟器镜像 | 否 / No | 体积、许可证和隐私风险 |
| `.env`, cookies, auth headers, tokens | 否 / No | 任何形式都不能提交 |
| `.venv/`, caches, `dist/`, build output | 否 / No | 可由工具重新生成 |
| 经筛选和脱敏的真实案例截图 | 是 / Yes | 只允许 `docs/assets/cases/` 中用于复现说明的少量图片 |
| 原始运行截图、账号、订单、聊天 | 否 / No | raw screenshots、完整 UI、日志和运行目录必须留在 ignored 路径 |
| 个人 Codex 配置、MCP 配置、历史日志 | 否 / No | 与项目运行无关，可能包含密钥和身份信息 |
| 简历、自我介绍、私人邮箱、学号 | 否 / No | 使用项目级贡献者署名 |

## 3. 绝对不能发布的内容 / Never publish

- Cookies、`Set-Cookie`、Authorization header、Bearer token、JWT。
- API keys、provider tokens、GitHub PAT、云厂商密钥、私钥、证书、keystore。
- `.env`、`*.local.yaml`、`auth.json`、浏览器配置和 Codex/MCP 用户配置。
- Windows 用户名、个人主目录、本机绝对项目路径、机器名、内网 IP、端口转发凭据。
- 真实用户账号、手机号、邮箱、地址、订单、聊天、支付信息、设备序列号。
- 真实业务 App 的未公开截图、日志、包名、服务端地址和内部测试数据。
- 第三方 APK、企业源码、未授权素材或来源不明的品牌图形。

允许出现的安全占位符包括 `com.example.app`、`qa@example.com`、`<PROJECT_ROOT>`、`<GITHUB_OWNER>` 和 `example-password`。这些值必须明显是虚构内容。

Safe placeholders include `com.example.app`, `qa@example.com`, `<PROJECT_ROOT>`, `<GITHUB_OWNER>`, and `example-password`. They must be obviously synthetic.

## 4. 发布前敏感信息审计 / Pre-publication audit

在仓库根目录运行。输出中的 `secret`, `token`, `password` 可能只是安全文档或变量名，需要逐条判断；但真实值必须删除。

Run from the repository root. Matches containing words such as `secret`, `token`, or `password` may be policy text or variable names; inspect each match. Actual values must be removed.

```powershell
$patterns = @(
  [regex]::Escape($env:USERNAME),
  [regex]::Escape($HOME),
  [regex]::Escape((Get-Location).Path),
  'cookie',
  'set-cookie',
  'Authorization:',
  'Bearer',
  'api_key',
  'api-key',
  'apikey',
  'access_token',
  'refresh_token',
  'secret',
  'credential',
  'password',
  'passwd',
  'oc_sk_',
  'ghp_',
  'github_pat_',
  'sk-',
  'AKIA',
  'eyJ',
  'BEGIN [A-Z ]*PRIVATE KEY'
)

$files = Get-ChildItem -Recurse -File | Where-Object {
  $_.FullName -notmatch '\\.git\\|\\.venv\\|\\node_modules\\|\\dist\\|\\runs\\|\\.pytest_cache\\|\\.ruff_cache\\|\\__pycache__\\|\\build\\'
}

foreach ($pattern in $patterns) {
  $matches = $files | Select-String -Pattern $pattern -AllMatches -ErrorAction SilentlyContinue
  if ($matches) {
    Write-Output "`n## $pattern"
    $matches | ForEach-Object { "$($_.Path):$($_.LineNumber): $($_.Line.Trim())" }
  }
}
```

可选工具 / Optional scanners:

```powershell
gitleaks detect --no-git --source .
git status --ignored --short
git add -n .
```

最终检查 / Final staging review:

```powershell
.\scripts\check.ps1
git status --short
git diff --cached --stat
git diff --cached
```

`git add -n .` 只预览，不写入暂存区。确认 `runs/`、APK、截图、日志、虚拟环境、构建产物和本地配置均显示为 `ignored`。

`git add -n .` is a dry run and does not stage files. Confirm that `runs/`, APKs, screenshots, logs, virtual environments, build outputs, and local configuration are all ignored.

## 5. 版本和元数据 / Version and metadata

本版本固定为 `0.1.1`。发布前确认以下内容一致：

This release is fixed at `0.1.1`. Verify these values match:

- `pyproject.toml` → `[project].version`
- `src/app_testbench/__init__.py` → `__version__`
- `CHANGELOG.md` → `[0.1.1]`
- Git tag → `v0.1.1`

建议 GitHub About：

Suggested GitHub About:

```text
Scriptable Android automation and evidence-rich HTML reports for NetEase MuMu Player. CLI, JSON/YAML flows, screenshots, UI dumps, logcat, and Codex skill support. Independent project, not affiliated with NetEase.
```

中文 About 可作为 README 的首段；GitHub 顶部 About 建议保留英文，便于国际用户理解。

The Chinese positioning remains in the primary README; keep the GitHub About field in English for broader discoverability.

GitHub owner 已确认，面向用户的地址已经统一为 `albertwickous-droid/app-testbench`，包括：

The GitHub owner is confirmed; user-facing links are now standardized to `albertwickous-droid/app-testbench`, including:

- `README.md`
- `README.en.md`
- `docs/releases/v0.1.1.md`

建议同时给 `pyproject.toml` 增加项目链接：

Also add project links to `pyproject.toml`:

```toml
[project.urls]
Homepage = "https://github.com/albertwickous-droid/app-testbench"
Repository = "https://github.com/albertwickous-droid/app-testbench"
Issues = "https://github.com/albertwickous-droid/app-testbench/issues"
Changelog = "https://github.com/albertwickous-droid/app-testbench/blob/main/CHANGELOG.md"
```

建议 topics：

Suggested topics:

```text
android
adb
mumu
mumu-player
emulator
android-automation
test-automation
qa
testing
python
cli
json
yaml
html-report
codex-skill
```

推荐的仓库信息：

Recommended repository metadata:

- Repository name: `app-testbench`
- Release title: `v0.1.1 — Real Cases and Contract Fix / 真实案例与契约修复`
- Social preview: `assets/social-preview.png`，1280×640
- License: MIT
- Default branch: `main`
- Issues: enabled
- Discussions: optional; enable only when maintainers can respond
- Wiki / Projects: off for v0.1.1 unless actively used

具体点击路径和分支规则见 [`docs/github-repository-setup.md`](github-repository-setup.md)。

See [`docs/github-repository-setup.md`](github-repository-setup.md) for exact repository settings and branch rules.

## 6. 首次推送 / Initial push

推荐先创建 **Private** 仓库，把首次提交推送上去，检查 GitHub 渲染、Actions、Secret Scanning 和文件列表，再切换为 Public。这样可以避免敏感文件在公开后被缓存或抓取。

Create the repository as **Private** first, push the initial commit, then inspect rendered Markdown, Actions, secret scanning, and the file list. Switch it to Public only after the review passes. This reduces the chance of public caching or scraping of an accidental disclosure.

首次提交前先配置 **仓库级** Git 身份，避免私人邮箱进入公开历史：

Configure a **repository-local** Git identity before the first commit so a private email does not enter public history:

```powershell
git config user.name "YOUR_PUBLIC_HANDLE"
git config user.email "YOUR_GITHUB_ID+YOUR_USERNAME@users.noreply.github.com"
```

两个值都替换成你的 GitHub 公开用户名和 GitHub 提供的 noreply 邮箱。不要使用公司邮箱、学校邮箱或私人邮箱。GitHub 的 Settings → Emails → Keep my email addresses private 应保持开启。

Replace both placeholders with your public GitHub handle and the noreply address shown by GitHub. Do not use a work, school, or personal email. Keep **Settings → Emails → Keep my email addresses private** enabled.

以下命令需要你明确确认后执行：

Run these commands only after explicit confirmation:

```powershell
git add .
git diff --cached --stat
git diff --cached
git commit -m "feat: initial public app-testbench release"
git branch -M main
git remote add origin https://github.com/albertwickous-droid/app-testbench.git
git push -u origin main
```

首次提交前检查 / Before the first commit:

- [ ] 工作区只包含预期文件 / Only intended files are present.
- [ ] 没有个人信息、本机路径、cookie、token、密钥或真实日志 / No personal data, local paths, cookies, tokens, keys, or real logs.
- [ ] `README.md` 与 `README.en.md` 都能正常渲染 / Both README files render correctly.
- [ ] CI 工作流语法有效 / Workflow YAML is valid.
- [ ] `scripts/check.ps1` 通过 / The local verification script passes.
- [ ] Logo、截图和图标没有第三方版权风险 / Branding and visuals have no third-party rights risk.

## 7. GitHub CI 与规则 / CI and repository rules

首次推送后完成：

After the first push:

1. 等待 `.github/workflows/ci.yml` 在 Windows 和 Linux、Python 3.10–3.12 全部通过。
2. 在 Rulesets 中保护 `main`：
   - require a pull request before merging；
   - require status checks to pass；
   - block force pushes；
   - block branch deletion；
   - 单人维护阶段允许管理员紧急绕过，增加第二位维护者后再要求审批。
3. 开启 Dependabot alerts、Dependabot security updates 和 secret scanning push protection。
4. 开启 Private vulnerability reporting。
5. 建议启用 CodeQL default setup。
6. Actions 默认 token 权限设为 read-only；Release job 单独声明 `contents: write`。
7. 创建 `pypi` environment，并设置 required reviewers（如需要）。

## 8. Tag、GitHub Release 与 PyPI

### 8.1 GitHub Release

打 tag 前先确认 `main` 的 CI 为绿色，并完成发布清单。

Before tagging, confirm `main` CI is green and the release checklist is complete.

```powershell
git switch main
git pull --ff-only
git status --short
git tag -a v0.1.1 -m "app-testbench v0.1.1"
git push origin v0.1.1
```

tag 触发 `.github/workflows/release.yml` 后会：

The tag triggers `.github/workflows/release.yml`, which will:

1. 重新运行 lint、format 和 tests；
2. 构建 sdist/wheel 并执行 `twine check`；
3. 生成 `SHA256SUMS.txt`；
4. 创建 **draft** GitHub Release 并附加构建产物。

进入 GitHub Releases，用 [`docs/releases/v0.1.1.md`](releases/v0.1.1.md) 的双语内容替换或补充自动生成说明，确认资产和校验和后发布。草稿模式可以防止配置错误直接公开。

Open GitHub Releases, use [`docs/releases/v0.1.1.md`](releases/v0.1.1.md) to finalize the bilingual notes, verify assets and checksums, then publish. Draft mode prevents an accidental public release.

### 8.2 PyPI（可选，独立手动步骤） / PyPI (optional, manual)

PyPI 不经由 tag 自动发布。`.github/workflows/publish-pypi.yml` 只能通过 `workflow_dispatch` 手动触发，并且需要输入 `PUBLISH` 确认。

PyPI is never published by a tag. `.github/workflows/publish-pypi.yml` is manual-only and requires the operator to type `PUBLISH`.

发布前 / Before publishing:

1. 检查包名 `/pypi/app-testbench/json`；若已被占用，不要强行覆盖，先决定新包名。
2. 在 PyPI 配置 Trusted Publisher：
   - Owner: `albertwickous-droid`
   - Repository: `app-testbench`
   - Workflow: `.github/workflows/publish-pypi.yml`
   - Environment: `pypi`
3. 在 GitHub 创建 `pypi` environment。
4. 使用 tag `v0.1.1` 运行 workflow，确认输入 `PUBLISH`。
5. 等待 environment review 和 PyPI 上传成功。

### 8.3 发布后验证 / Post-release verification

```powershell
$venv = Join-Path $env:TEMP "app-testbench-smoke"
py -3.11 -m venv $venv
& "$venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
python -m pip install app-testbench
app-testbench --version
app-testbench --help
app-testbench skill-path
app-testbench doctor --json
```

如果尚未发布 PyPI，则改用干净虚拟环境安装 wheel：

If PyPI is not part of this release, install the wheel in a clean environment instead:

```powershell
python -m pip install .\dist\app_testbench-0.1.1-py3-none-any.whl
```

同时验证 / Also verify:

- GitHub Release 的三个资产：wheel、sdist、`SHA256SUMS.txt`；
- Release 页面与 README 链接有效；
- Actions、Dependabot、secret scanning 无异常；
- 真实 MuMu 主机上的 `doctor`、`instance list`、一个最小 flow 和 HTML 报告；
- 将真实环境版本和限制写回 release notes，但不提交真实截图或账号数据。

## 9. 泄露或回滚 / Disclosure and rollback

- **发现真实密钥：** 先吊销/轮换，再清理仓库。删除文件不等于安全，公开仓库可能已被缓存。
- **首次公开前发现：** 停止 push，清理暂存区并从工作树删除敏感文件。
- **已 push 后才泄漏：** 立即将仓库设为 private（如可行）、轮换密钥、评估历史重写；必要时删除并重建仓库。
- **GitHub Release 出错：** 编辑说明、转回 draft 或标记 pre-release；不要静默覆盖已发布的 tag。
- **PyPI 版本错误：** PyPI 文件不能原地替换；使用 `yank`，然后发布新的 patch 版本。
- **安全漏洞：** 使用 GitHub Private Vulnerability Reporting，修复后按协调披露流程发布 patch。

- **Real secret found:** revoke/rotate first, then clean the repository. Deleting a file is not enough; public content may already be cached.
- **Before first public push:** stop, clean the index and working tree, then re-audit.
- **Already pushed:** make the repository private if possible, rotate credentials, assess history rewriting, and recreate the repository if necessary.
- **Bad GitHub Release:** edit notes, return it to draft, or mark it as a pre-release. Never silently move a published tag.
- **Bad PyPI version:** yanked files cannot be replaced. Yank the release and publish a patch version.
- **Security issue:** use GitHub Private Vulnerability Reporting and follow coordinated disclosure.

## 10. 发布产物清单 / Publication artifacts

- [`README.md`](../README.md) / [`README.en.md`](../README.en.md)：双语项目首页
- [`docs/github-repository-setup.md`](github-repository-setup.md)：GitHub 设置与 About/topics
- [`docs/releases/v0.1.1.md`](releases/v0.1.1.md)：v0.1.1 双语发行说明
- [`docs/promotion.md`](promotion.md)：30 天冷启动与渠道策略
- [`docs/launch-copy.md`](launch-copy.md)：可复制的双语发布文案
- [`assets/report-preview.png`](../assets/report-preview.png)：HTML 报告合成预览
- [`DISCLAIMER.md`](../DISCLAIMER.md)：免责声明与责任边界
- [`RESPONSIBLE_USE.md`](../RESPONSIBLE_USE.md)：授权使用与滥用边界
- [`PRIVACY.md`](../PRIVACY.md)：本地数据与隐私
- [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md)：第三方商标与依赖
- [`SUPPORT.md`](../SUPPORT.md)：问题、功能请求和安全问题的入口
- [`SECURITY.md`](../SECURITY.md)：私密漏洞报告与隐私边界
- [`CONTRIBUTING.md`](../CONTRIBUTING.md)：双语贡献指南
- [`RELEASE_CHECKLIST.md`](../RELEASE_CHECKLIST.md)：最终发布门禁
- [`CHANGELOG.md`](../CHANGELOG.md)：版本变更记录
- `.github/release.yml`：GitHub 自动分类发布说明
