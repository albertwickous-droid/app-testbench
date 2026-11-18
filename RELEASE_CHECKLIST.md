# 发布检查清单 / Release Checklist

版本 / Version: `0.1.1` · 目标 tag / Target tag: `v0.1.1`

## 1. 源码与版本 / Source and version

- [ ] `CHANGELOG.md` 已包含 `0.1.1` / changelog includes `0.1.1`
- [ ] `pyproject.toml`、`src/app_testbench/__init__.py` 版本一致 / versions match
- [ ] `README.md` 和 `README.en.md` 内容对齐 / both READMEs are in sync
- [ ] `docs/releases/v0.1.1.md` 已审阅 / release notes reviewed
- [ ] LICENSE 使用项目级署名，不包含私人信息 / license uses project attribution
- [ ] DISCLAIMER.md、RESPONSIBLE_USE.md、PRIVACY.md、THIRD_PARTY_NOTICES.md 已审阅 / responsibility notices reviewed
- [ ] 权责声明不与 MIT License 冲突，第三方商标与依赖已列明 / notices do not conflict with MIT and list third-party marks/dependencies
- [ ] 没有个人介绍、用户名、邮箱或机器专属路径 / no personal intro, username, email, or machine path
- [ ] Git author 使用仓库级公开 handle 与 GitHub noreply 邮箱 / local Git identity uses a public handle and noreply email
- [ ] README 和 v0.1.1 release notes 中的 OWNER 已替换为真实仓库所有者 / OWNER placeholders in user-facing READMEs and release notes are replaced

## 2. 隐私与安全 / Privacy and security

- [ ] 全仓敏感模式扫描完成 / sensitive-pattern scan completed
- [ ] 没有 cookie、Authorization、Bearer、JWT、API key、PAT、私钥或证书 / no secrets
- [ ] 没有 `.env`、`auth.json`、cookies、Codex/MCP 配置 / no local credentials
- [ ] 没有 APK、原始或未审查截图、UI XML、原始 logcat、`runs/` 或未筛选报告 / no raw or unreviewed screenshots, UI XML, raw logcat, `runs/`, or unfiltered reports
- [ ] 示例只使用 `com.example.app` 等明显占位值 / examples use obvious placeholders
- [ ] `git status --ignored --short` 显示运行时目录已被忽略 / runtime folders ignored
- [ ] `git add -n .` 文件列表已逐项检查 / dry-run staging reviewed
- [ ] GitHub secret scanning push protection 已开启 / push protection enabled

## 3. 自动验证 / Automated verification

- [ ] `python -m ruff check .`
- [ ] `python -m ruff format --check .`
- [ ] `python -m pytest -q`
- [ ] `python -m build`
- [ ] `python -m twine check dist/*`
- [ ] `.\scripts\check.ps1` 通过 / local verification script passes
- [ ] `.github/workflows/ci.yml` 在 Windows/Linux、Python 3.10–3.12 全绿 / CI matrix green
- [ ] Release workflow 只创建 GitHub draft，不自动发布 PyPI / GitHub release does not publish PyPI

## 4. 真实环境验证 / Live-environment verification

- [ ] `app-testbench doctor` 在真实 Windows MuMu 主机通过 / passes on a real host
- [ ] `instance list/start/stop` 已验证 / instance lifecycle tested
- [ ] APK install 已验证 / APK installation tested
- [ ] launch/close 已验证 / app lifecycle tested
- [ ] tap/swipe/text/keyevent 已验证 / input actions tested
- [ ] screenshot、`dump-ui`、logcat 已验证 / evidence actions tested
- [ ] 至少一个 JSON 或 YAML flow 生成报告 / one flow produces a report
- [ ] `report.html` 离线打开且截图已内嵌 / report opens offline with embedded images
- [ ] Wikipedia 真实案例 63/63 步通过 / Wikipedia live case passed 63/63 steps
- [ ] Firefox/Fennec 真实案例 66/66 步通过，下载文件精确校验 / Firefox live case passed 66/66 with exact download verification
- [ ] VLC 真实案例 43/43 步通过，Activity 与 logcat 断言通过 / VLC live case passed 43/43 with Activity and logcat assertions
- [ ] `wait_for_activity` 与 `assert_logcat_contains` 有单元测试 / new actions have unit and flow tests
- [ ] 失败 `run --json` 通过打包的 `cli-v1.schema.json` / failed `run --json` validates against the packaged schema
- [ ] 测试的 MuMu 版本记录在 release notes / MuMu version documented
- [ ] 无法完成的真实环境项明确列为限制 / unavailable live checks are documented as limits

## 5. GitHub 页面 / GitHub repository

- [ ] About、topics、license、social preview 已设置 / metadata configured
- [ ] Issues 已开启 / issues enabled
- [ ] Private Vulnerability Reporting 已开启 / private reporting enabled
- [ ] Dependabot alerts/security updates 已开启 / Dependabot enabled
- [ ] Secret scanning 与 push protection 已开启 / secret scanning enabled
- [ ] `main` ruleset 要求 PR 和 CI，禁止强推/删除 / branch rules configured
- [ ] `v*` tag ruleset 限制为维护者 / tag rules configured
- [ ] Actions 默认 token 只读 / default Actions token is read-only
- [ ] `pypi` environment 已配置（如发布 PyPI）/ environment configured if needed

## 6. Git 与 Release

- [ ] 首次提交前完成 `git diff --cached` 审阅 / staged diff reviewed
- [ ] 初始提交信息已确认 / initial commit message confirmed
- [ ] 先以 private 仓库验证渲染和 Actions / private repository checked first
- [ ] 确认后再切换 Public / public switch explicitly approved
- [ ] `v0.1.1` 指向预期提交 / tag points to the intended commit
- [ ] Release 为 draft，人工核对后才发布 / release stays draft until reviewed
- [ ] 资产包含 wheel、sdist、`SHA256SUMS.txt` / expected assets attached
- [ ] Release notes 包含安全限制与已知边界 / notes contain safety and limits
- [ ] 不移动已发布 tag / published tags are never moved

## 7. PyPI（可选） / PyPI (optional)

- [ ] 包名可用性已重新检查 / package name availability rechecked
- [ ] Trusted Publisher 的 owner/repo/workflow/environment 完全匹配 / publisher tuple matches
- [ ] workflow 手动输入 `PUBLISH` / manual confirmation required
- [ ] environment review 已配置 / environment review configured
- [ ] 干净环境安装 wheel/sdist 成功 / clean install succeeds
- [ ] `app-testbench --version`、`--help`、`skill-path` 正常 / CLI entry points work
- [ ] 发布后不再修改同一版本；发现问题发布 patch / never replace a published version

## 8. 发布后 / Post-release

- [ ] README 和文档链接有效 / documentation links work
- [ ] Release 资产可下载且 checksum 匹配 / assets and checksums verified
- [ ] CI、Dependabot、secret scanning 无新增高优先级告警 / no critical alerts
- [ ] 真实 MuMu 主机完成最小 smoke test / minimal live smoke test completed
- [ ] 记录已知兼容性、未验证版本和升级注意事项 / compatibility notes recorded
- [ ] 发现真实凭据时先轮换，再处理仓库历史 / rotate before history cleanup

## 9. 宣传与首发 / Promotion and launch

- [ ] `docs/promotion.md` 的渠道策略已审阅 / promotion playbook reviewed
- [ ] `docs/launch-copy.md` 文案已按真实链接和能力替换 / launch copy customized
- [ ] social preview 与 report preview 已检查 / social and report previews reviewed
- [ ] 所有公开截图来自真实运行并已脱敏、去元数据 / public screenshots are live, redacted, and metadata-free
- [ ] 文案没有“支持所有模拟器”“绕过检测”等不实宣传 / no unsupported claims
- [ ] 已阅读目标社区/板块的 self-promotion 规则 / community rules checked
- [ ] 首发渠道不超过 2–3 个，避免同日重复灌水 / intentional channel list
- [ ] 发布后 24 小时有维护者回复计划 / response plan ready
- [ ] 已记录首日基线：views、clones、stars、issues、release downloads / baseline recorded
- [ ] D+7 有反馈小结和 FAQ 更新计划 / feedback review scheduled
