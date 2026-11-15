# 第三方声明 / Third-Party Notices

## 1. 项目许可 / Project license

App TestBench 的源代码、文档和项目原创 SVG/PNG 素材按 [`LICENSE`](LICENSE) 中的 MIT License 发布，版权署名为 `App TestBench contributors`。

The source code, documentation, and original SVG/PNG assets of App TestBench are released under the MIT License in [`LICENSE`](LICENSE), with copyright attributed to `App TestBench contributors`.

MIT License 不授予任何第三方商标、应用、APK、模拟器、服务或数据的使用权。

The MIT License does not grant rights to any third-party trademark, application, APK, emulator, service, or data.

## 2. 无隶属关系 / No affiliation

App TestBench 是独立项目，与以下主体不存在隶属、授权、赞助、认证或官方背书关系：

- 网易 / NetEase；
- MuMu Player / MuMu 模拟器；
- Google LLC / Android / Android SDK / ADB；
- Python Software Foundation；
- GitHub, Inc.；
- OpenAI / Codex；
- 任何被测试、部署或集成的第三方应用及其权利人。

App TestBench is an independent project and is not affiliated with, authorized by, sponsored by, certified by, or endorsed by:

- NetEase;
- MuMu Player or the MuMu emulator;
- Google LLC, Android, Android SDK, or ADB;
- the Python Software Foundation;
- GitHub, Inc.;
- OpenAI or Codex;
- any tested, deployed, or integrated third-party application or its rights holder.

## 3. 商标与名称 / Trademarks and names

本项目和文档中出现第三方名称、产品名、命令名或商标，仅用于描述兼容对象、依赖、文件格式或互操作场景。所有商标、服务标记、商号和产品名称归各自权利人所有。

Third-party names, product names, command names, or trademarks in this project and documentation are used only to describe compatibility targets, dependencies, file formats, or interoperability. All trademarks, service marks, trade names, and product names belong to their respective owners.

不得将本项目名称、logo 或素材用于暗示第三方背书、官方兼容认证或合作关系。

Do not use the project name, logo, or assets to imply third-party endorsement, official compatibility certification, or partnership.

## 4. 运行时依赖 / Runtime dependency

### PyYAML

- 项目：https://github.com/yaml/pyyaml
- 用途：解析 YAML flow 配置 / parsing YAML flow configuration
- 许可：MIT License
- 分发方式：作为 Python 包依赖安装，不内嵌在项目的 wheel 中 / installed as a Python package dependency, not vendored into the project wheel

PyYAML 的版权和许可声明以其发行包中的 LICENSE 文件为准。

PyYAML's copyright and license notices are governed by the LICENSE included in its distribution.

## 5. 用户自行安装的第三方软件 / User-installed third-party software

以下组件不由本项目分发：

- MuMu Player 和 `MuMuManager.exe`；
- Android SDK Platform Tools 和 `adb.exe`；
- Windows、Android 系统镜像和模拟器镜像；
- 被测 APK、AAB、XAPK 或应用资源；
- Python 解释器、pip、虚拟环境和用户安装的依赖。

The project does not distribute:

- MuMu Player or `MuMuManager.exe`;
- Android SDK Platform Tools or `adb.exe`;
- Windows, Android system images, or emulator images;
- tested APKs, AABs, XAPKs, or application assets;
- the Python interpreter, pip, virtual environments, or user-installed dependencies.

用户必须自行取得这些组件的合法许可，并遵守其开发商、平台和应用商店的条款。用户安装的 APK、截图、图标、字体、音乐、视频和其他素材，其权利和责任由用户自行承担。

Users must obtain lawful licenses for these components and comply with the terms of their vendors, platforms, and app stores. Users are responsible for the rights and obligations associated with APKs, screenshots, icons, fonts, music, video, and other assets they install or process.


### Live-case applications

- **Markor** is a separate open-source Android application. The repository links to its official F-Droid download and stores a pin (version, size, and SHA256), but does not redistribute the APK or claim endorsement by its maintainers. See <https://github.com/gsantner/markor> and the app's own license and notices.
- **Android Settings** refers to the AOSP Settings app included in the user's MuMu Android image. The project does not distribute the system image or app.
- Public case screenshots are selected from real test runs. Third-party app names, icons, and UI text remain the property of their respective rights holders and are shown only to document interoperability and test evidence.

- **Markor** 是独立的开源 Android 应用。本仓库只链接其官方 F-Droid 下载并记录版本、大小和 SHA256，不重新分发 APK，也不表示获得其维护者背书。许可证与声明以 Markor 项目自身为准。
- **Android Settings** 指用户 MuMu Android 镜像中自带的 AOSP 系统设置应用；本仓库不分发系统镜像或该应用。
- 公开案例截图为真实测试运行中的筛选结果。第三方应用名称、图标和 UI 文本归各自权利人所有，仅用于说明互操作与测试证据。

## 6. 开发与 CI 工具 / Development and CI tools

开发和 CI 可能使用 Python、pytest、Ruff、build、twine、GitHub Actions、actions/checkout、actions/setup-python、upload/download-artifact、softprops/action-gh-release 和 pypa/gh-action-pypi-publish 等工具。

Development and CI may use Python, pytest, Ruff, build, twine, GitHub Actions, actions/checkout, actions/setup-python, upload/download-artifact, softprops/action-gh-release, and pypa/gh-action-pypi-publish.

这些工具按其各自许可证和平台条款提供。它们的名称或链接不表示本项目获得其官方认证或背书。

These tools are provided under their own licenses and platform terms. Their names or links do not indicate official certification or endorsement of this project.

GitHub Actions 使用的第三方 action 版本、权限和供应链风险由维护者在发布流程中审查，但本项目不对第三方 action 的中断、漏洞或政策变化作保证。

Maintainers review third-party action versions, permissions, and supply-chain risk in the release workflow, but the project does not guarantee against third-party action outages, vulnerabilities, or policy changes.

## 7. 外部链接与徽章 / External links and badges

README 中的 shields.io 徽章和第三方链接可能产生外部请求。图片可用性、跟踪行为、缓存、条款和隐私政策由对应服务负责。

Shields.io badges and third-party links in the README may generate external requests. Availability, tracking behavior, caching, terms, and privacy policies are controlled by the relevant service.

如果组织环境不允许外部图片请求，可在内部镜像或离线文档中移除徽章，这不影响软件运行。

If an organization prohibits external image requests, badges can be removed from an internal mirror or offline documentation without affecting the software.

## 8. 原创素材 / Original assets

`assets/banner.svg`、`assets/social-preview.*` 和 `assets/report-preview.*` 是为本项目创建的合成视觉素材，不包含真实应用截图、客户数据或第三方图标库。除第三方商标外，这些素材随项目按 MIT License 发布。

`assets/banner.svg`, `assets/social-preview.*`, and `assets/report-preview.*` are synthetic visuals created for this project. They do not contain real application screenshots, customer data, or third-party icon libraries. Except for third-party trademarks, these assets are released with the project under the MIT License.

如果权利人认为某个名称、图标或链接使用不当，请通过 GitHub Issue 提供最小化说明，维护者会评估更正或移除。

If a rights holder believes a name, icon, or link is used improperly, open a minimized GitHub Issue so maintainers can evaluate correction or removal.

## 9. 许可证文件优先级 / License precedence

第三方组件的许可证以其自身发行包或官方页面为准。本文件只提供项目级说明，不复制、修改或替代任何第三方许可证。

Third-party component licenses are governed by their own distributions or official pages. This document provides project-level notice only and does not copy, modify, or replace any third-party license.

如果本文件与第三方许可证或 [`LICENSE`](LICENSE) 有冲突，以相应第三方许可证或项目 MIT License 的正式文本为准。

If this document conflicts with a third-party license or [`LICENSE`](LICENSE), the official text of the applicable third-party license or the project MIT License controls.
