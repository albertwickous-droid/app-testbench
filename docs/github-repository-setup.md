# GitHub 仓库设置 / Repository Setup

本页用于首次公开 `app-testbench` 时逐项配置 GitHub。仓库 owner 已确认：`albertwickous-droid`。

Use this checklist for the first public `app-testbench` repository. The confirmed repository owner is `albertwickous-droid`.

## 1. 创建仓库 / Create the repository

推荐先在 GitHub 创建空的 **Private** 仓库：

Create an empty **Private** repository first:

- Repository name: `app-testbench`
- Description: use the About text below
- Initialize with README: **off**
- Add `.gitignore`: **none**
- License: **none** (the repository already contains `LICENSE`)

推送并检查后再切换为 Public。不要在 GitHub 网页端额外生成 README、license 或初始提交，否则本地首次推送需要先合并无关历史。

Switch to Public after the first push and review. Do not generate a README, license, or initial commit in the GitHub UI, because that creates unrelated history before the local first push.

## 2. About

推荐英文简介 / Recommended English description:

```text
Run repeatable Android app tests on a mature MuMu Player runtime. Explicit JSON/YAML flows, UI assertions, screenshots, UI dumps, logcat, and self-contained HTML reports. AI can assist; evidence decides. Windows-first, local-only, MIT. Independent project, not affiliated with NetEase.
```

中文说明保留在 README 开头，不建议同时塞入 About 字段。

Keep the Chinese positioning at the top of the README rather than duplicating it in the About field.

## 3. Topics

逐行添加 / Add each topic:

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

## 4. Features

首版建议 / Recommended for v0.1.0:

| Feature | Setting |
| --- | --- |
| Issues | On |
| Discussions | Optional; only if maintainers can respond |
| Projects | Off unless actively used |
| Wiki | Off; use `docs/` as the source of truth |
| Sponsorships | Off unless configured |
| Preserve this repository | Optional; enable after the project has meaningful community value |

## 5. Social preview

使用仓库中的合成预览图：

Use the synthetic preview from the repository:

- File: `assets/social-preview.png`
- Size: 1280 × 640
- Content: product name, command surface, flow/report abstraction
- No real app screenshots, account names, device identifiers, or local paths

在 **Settings → General → Social preview** 上传。若需要更新，优先修改 `assets/social-preview.svg` 后重新导出 PNG，避免只有一个不可维护的位图。

Upload it under **Settings → General → Social preview**. If it changes, edit `assets/social-preview.svg` first and export a new PNG so the source remains maintainable.

## 6. Merge settings

**Settings → General → Pull Requests**

- Allow merge commits: off
- Allow squash merging: on
- Allow rebase merging: on
- Default commit message: pull request title
- Automatically delete head branches: on

**Settings → General → Releases**

- Enable releases
- Keep releases as drafts until notes and assets are reviewed

## 7. Rulesets / Branch protection

在 **Settings → Rules → Rulesets** 创建 `main` branch ruleset：

Create a `main` branch ruleset under **Settings → Rules → Rulesets**:

- Target: default branch
- Require a pull request before merging
- Require status checks:
  - `Test windows-latest / Python 3.10`
  - `Test windows-latest / Python 3.11`
  - `Test windows-latest / Python 3.12`
  - `Test ubuntu-latest / Python 3.10`
  - `Test ubuntu-latest / Python 3.11`
  - `Test ubuntu-latest / Python 3.12`
  - `Build package`
- Block force pushes
- Block deletions
- Allow administrator bypass only while the project has a single maintainer
- Add a required approval only after there is a second active maintainer

再创建一个 tag ruleset：

Create a tag ruleset as well:

- Target: `v*`
- Restrict creation/update/deletion to maintainers
- Never move a published version tag

## 8. Labels used by release notes

Create or keep these labels so `.github/release.yml` can group generated release notes:

| Label | Purpose |
| --- | --- |
| `bug` | Confirmed defect |
| `enhancement` | Scoped feature or improvement |
| `documentation` | Documentation-only change |
| `ci` | GitHub Actions and automation |
| `packaging` | Package metadata or distribution |
| `security` | Security hardening or disclosure-safe fix |
| `dependencies` | Dependabot or dependency update |
| `chore` | Maintenance |
| `refactor` | Internal restructuring |
| `test` | Test-only change |
| `skip-changelog` | Exclude from generated release notes |


## 9. Actions

**Settings → Actions → General**

- Actions permissions: allow the repositories and actions needed by CI
- Workflow permissions: read repository contents by default
- Allow GitHub Actions to create and approve pull requests: off unless intentionally needed
- Require approval for first-time contributors: on

必需 actions / Required actions:

- `actions/checkout`
- `actions/setup-python`
- `actions/upload-artifact`
- `actions/download-artifact`
- `softprops/action-gh-release`
- `pypa/gh-action-pypi-publish`

Release workflow only declares `contents: write` for the release job. PyPI workflow only declares `id-token: write` in the `pypi` environment job.

## 10. Code security

**Settings → Code security and analysis**

建议开启 / Recommended:

- Dependabot alerts
- Dependabot security updates
- Secret scanning
- Secret scanning push protection
- Private vulnerability reporting
- CodeQL default setup for Python

如果 secret scanning 发现真实值，先轮换凭据，再处理仓库；不要只删除文件。

If secret scanning reports a real value, rotate it first. Deleting the file alone does not make the value safe.

## 11. Environments

**Settings → Environments**

创建 `pypi` environment：

Create a `pypi` environment:

- Required reviewers: at least one when a second maintainer exists
- Limit deployment branches and tags: `v*` tags only
- Environment secret: none required for Trusted Publishing
- Configure the same owner/repository/workflow/environment tuple on PyPI

## 12. Community files

确认 GitHub 能识别这些文件：

Confirm GitHub recognizes these files:

- `README.md` and `README.en.md`
- `LICENSE`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `DISCLAIMER.md`
- `RESPONSIBLE_USE.md`
- `PRIVACY.md`
- `THIRD_PARTY_NOTICES.md`
- `SUPPORT.md`
- `.github/ISSUE_TEMPLATE/*.yml`
- `.github/pull_request_template.md`
- `.github/release.yml`

`.github/ISSUE_TEMPLATE/config.yml` 已配置为 GitHub Private Vulnerability Reporting 的绝对链接。

`.github/ISSUE_TEMPLATE/config.yml` already links security reports to GitHub Private Vulnerability Reporting.

## 13. Discussions（可选） / Discussions (optional)

只有当维护者能持续响应时再开启。建议分类：

Enable only if maintainers can respond consistently. Suggested categories:

- Announcements
- Q&A
- Show and tell
- Ideas

Bug 复现、版本信息和错误日志使用 Issues；漏洞和敏感数据使用 Private Vulnerability Reporting。

Use Issues for reproducible bugs, version details, and error logs. Use Private Vulnerability Reporting for vulnerabilities and sensitive data.

## 14. 发布前页面检查 / Final page check

- README 首屏能看懂项目用途和限制 / The first screen explains purpose and limits.
- About、topics、license、social preview 已设置 / About, topics, license, and social preview are set.
- Issue forms 能正常打开 / Issue forms open correctly.
- Security policy 中的入口真实可用 / The security reporting entry works.
- Release 资产包含 wheel、sdist 和 checksums / Release assets include wheel, sdist, and checksums.
- 仓库公开后没有个人身份、密钥、真实报告或本机路径 / No identity data, secrets, real reports, or local paths are public.
