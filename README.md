# 白龙桌宠 Linux 适配版

基于 Wunsch2048/codex-bailong-desktop-pet 的 0.8.3 源码，复用其 0.7.9 发布版的原始 512px 动画。本仓库保存 Linux 适配源码，包含今日模型统计、Token 用量、金额估算和输出速率。来源与素材使用说明保留在 [NOTICE.md](NOTICE.md) 和 [docs/upstream/](docs/upstream/) 中；Windows 上游说明保留在 [README-UPSTREAM.md](README-UPSTREAM.md)。

仓库地址：[shiki-sl/bailong-linux](https://github.com/shiki-sl/bailong-linux)。当前适配版本：`0.8.3-linux.1`。

## 使用

首次使用请按下方“下载与运行”准备源码、Python 环境和动画素材，再运行 `./start-linux.sh`。已安装桌面入口的本机也可从应用菜单打开“白龙桌宠”，或运行 `bailong-pet`。

- 点击人物、右键菜单及托盘可打开卡片、设置和日报；托盘点击可找回人物。
- 额度通过当前用户的 Codex CLI 查询，Token 按本机 Codex 日志增量统计。未提供的额度窗口保持未知；不补造 5 小时额度。
- 使用现有本机 Codex 登录，不复制登录令牌。聊天服务是独立的可选功能，密钥存入系统 Secret Service 密钥环。
- 登录自启、随 Codex 启动均为可选设置；安装不自动开启。
- 日报 → 模型页提供“当天”范围，显示当前统计日期的各模型用量和占比，随 Token 扫描更新；原有全部、30 天、7 天范围保持截至昨日的口径。

## 预计金额和 Token 速率

完整状态卡片新增“今日估算 · USD”和输出速率，每 10 秒后台采样。缩小模式下点击桌宠展开查看；鼠标停在金额/速率区域可查看模型明细、未计价 Token 和采样口径。

- 独立复用本机 Token Monitor 随附的 Tokscale 4.18.0 原生采集器。运行文件、价格种子和许可证保存在 vendor/tokscale；运行缓存独立保存到 BailongEnhanced/metrics-collector，不依赖 Monitor 窗口、设置或历史数据库。
- 金额是本机可读 Codex 日志按 API 价格的估算，区分缓存输入，不能当作订阅账单、实际付费或账户额度。可能无法还原服务档位、工具费用等。只接受模型身份的精确价格匹配；无法确认的模型（例如 codex-auto-review）仍计入 Token，用“部分未计价”和星号标记金额覆盖不足，悬停列明缺口。
- Tokscale 将可见输出与推理分开输出，白龙合并一次，避免重复计算。速率用完整计时样本的输出 Token（含推理）除以对应请求耗时，多请求按耗时加权；两次采样有增量时显示“近期均速”，180 秒没有新样本则显示“今日均速”。这不是逐 Token 流式瞬时速度。
- 首次等待、更新失败、数据过期和跨日分别处理；不会把昨日金额继续标成今日，也不会把未知价格当成零。
- 已核对 Codex 客户端与白龙实际额度接口：均仅返回 codex 账户的一个周窗口，没有更完整的全模型总额度或绝对总消耗。额度逻辑维持原样，不将模型百分比相加，也不以本机 Token 推算订阅额度。

这两项 Codex 指标可直接在白龙查看，无须另外打开 Token Monitor。Monitor 应用、入口、历史和自启设置均保留。

本机已安装版本位于 `~/.local/share/bailong-linux/`，启动命令位于 `~/.local/bin/bailong-pet`，应用入口位于 `~/.local/share/applications/bailong-linux.desktop`。下面的源码运行步骤不会自动创建这些入口。运行数据位于 `${XDG_DATA_HOME:-~/.local/share}/BailongEnhanced/`，与 Codex 数据分开。

## Linux 兼容边界

- KDE Wayland 下使用 XWayland，以支持人物拖动、位置保存和独立卡片跟随。不修改桌面合成器配置。
- 通过当前用户的 `~/.codex/ipc/ipc.sock` 订阅实时生命周期；断开时保留连接状态提示，并继续读取会话日志。
- Windows 专用的全屏视频自动让位尚未移植；相关开关已停用，可以手动切换置顶。
- Windows 安装器和程序更新不能用于此 Linux 版本，下载和安装入口已阻止。源码与 Python 依赖需要单独维护。
- 统计只覆盖当前电脑可读的日志；无法据此汇总其他机器的消耗。额度查询失败、旧缓存、部分日志错误分别保留状态。

## 下载与运行

需要 Python 3.12、uv 和现有桌面环境。Wayland 下还需可用的 XWayland；聊天密钥功能需要系统 Secret Service 与 `secret-tool`。随仓库保留的 Tokscale 原生采集器用于 Linux x86_64 / glibc，其他架构需自行准备兼容版本。

```sh
git clone https://github.com/shiki-sl/bailong-linux.git
cd bailong-linux
```

准备 Python 环境：

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-linux.txt
```

动画单独发布在本仓库的 [512px 素材 Release](https://github.com/shiki-sl/bailong-linux/releases/tag/materials-light-8849481e60e0b3f2314ec6a0)，不进入 Git 历史。下载完整素材 ZIP 和校验文件，在仓库根目录执行：

```sh
BAILONG_MATERIALS_URL='https://github.com/shiki-sl/bailong-linux/releases/download/materials-light-8849481e60e0b3f2314ec6a0'
curl -fL --retry 3 -O "$BAILONG_MATERIALS_URL/bailong-light-8849481e60e0b3f2314ec6a0.zip"
curl -fL --retry 3 -O "$BAILONG_MATERIALS_URL/SHA256SUMS.txt"
sha256sum -c SHA256SUMS.txt
.venv/bin/python -m zipfile -e bailong-light-8849481e60e0b3f2314ec6a0.zip .
./start-linux.sh
```

请逐条执行：校验必须显示 `OK`，失败时重新下载，停止解压和启动。也可从 Release 页面手动下载这两个文件后执行校验、解压和启动命令。

素材包约 590 MiB，包含 `outputs/白龙桌宠素材/` 下的 31 个动画 WebP、`素材清单.json`，以及三份来源/授权说明；解压后直接形成程序需要的目录，不需要运行 Windows EXE。`material-manifest.json` 提供逐文件大小和 SHA-256。素材 ID 为 `8849481e60e0b3f2314ec6a0`，与源码 `app/material_catalog.json` 的 light 档完全匹配。

此 Release 是资源专用预发布，不提供 Linux 安装器。512px 默认素材和 720px 高清素材不能混用，文档演示图不能替代动画。角色和动画的来源与使用范围见 [NOTICE.md](NOTICE.md)；公开下载不额外授予商用或再分发许可。

运行时请先在这台电脑安装并登录 Codex CLI；额度和会话读取使用你自己的本机登录。源码环境与素材解压完成后，后续启动只需在仓库目录执行 `./start-linux.sh`。登录自启、随 Codex 启动和聊天服务均按需在设置中启用；聊天服务另需自行配置密钥。

Tokscale 的可执行文件、许可证和公共价格种子随源码保留，来源及 SHA-256 见 [vendor/tokscale/PROVENANCE.json](vendor/tokscale/PROVENANCE.json)。运行后生成的使用记录和缓存位于用户数据目录，不提交到仓库。

## 此前本机适配验证记录

- 25 项额度、会话与 Token 相关测试通过；20 项 Linux 适配和生命周期测试通过。
- 32 个素材文件与上游目录 SHA-256 一致；人物、卡片、设置、聊天入口、日报和工作动画已完成渲染检查。
- 实际桌面进程使用 xcb / XWayland，窗口和卡片可见，实时任务状态、额度接口和 Token 索引已接入，启动错误日志为空。
- 未进行系统级鼠标拖动或全屏视频验收；全屏视频自动让位在 Linux 版停用。
- 2026-10-23 金额/速率增量验证：4 项覆盖价格缺口、缓存/推理计数、计时增量和失效/跨日状态的测试通过；原生采集器隔离样本得到 110 Token、USD 0.000148、5 tok/s；真实日志和完整/展开卡片已渲染核验。

## 源码检查

Linux 检查沿用现有测试，使用隔离的临时目录；不读取真实登录或会话、不启动桌宠：

```sh
PYTHONPATH=app QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest test_linux_support test_usage_metrics test_quota_summary_data
```

GitHub Actions 保留上游 Windows 源码检查，并增加 Linux 适配检查；这些检查不部署或发布软件。真实桌面表现仍以对应设备的运行验收为准。
