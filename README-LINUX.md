# 白龙桌宠 Linux 适配版

基于 Wunsch2048/codex-bailong-desktop-pet 的 0.8.3 源码，复用其 0.7.9 发布版的原始 512px 动画。本仓库保存 Linux 适配源码，包含今日模型统计、Token 用量、金额估算和输出速率。来源与素材使用说明保留在 [NOTICE.md](NOTICE.md) 和 [docs/upstream/](docs/upstream/) 中；Windows 上游说明保留在 [README-UPSTREAM.md](README-UPSTREAM.md)。

仓库地址：[shiki-sl/bailong-linux](https://github.com/shiki-sl/bailong-linux)。当前适配版本：`0.8.3-linux.1`。

## 使用

安装后从应用菜单打开“白龙桌宠”，或运行 `bailong-pet`。

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

程序安装于 `~/.local/share/bailong-linux/`，启动命令位于 `~/.local/bin/bailong-pet`，应用入口位于 `~/.local/share/applications/bailong-linux.desktop`。运行数据位于 `${XDG_DATA_HOME:-~/.local/share}/BailongEnhanced/`，与 Codex 数据分开。

## Linux 兼容边界

- KDE Wayland 下使用 XWayland，以支持人物拖动、位置保存和独立卡片跟随。不修改桌面合成器配置。
- 通过当前用户的 `~/.codex/ipc/ipc.sock` 订阅实时生命周期；断开时保留连接状态提示，并继续读取会话日志。
- Windows 专用的全屏视频自动让位尚未移植；相关开关已停用，可以手动切换置顶。
- Windows 安装器和程序更新不能用于此 Linux 版本，下载和安装入口已阻止。源码与 Python 依赖需要单独维护。
- 统计只覆盖当前电脑可读的日志；无法据此汇总其他机器的消耗。额度查询失败、旧缓存、部分日志错误分别保留状态。

## 从源码运行

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

Git 历史不包含大型角色动画，运行前需另行准备匹配的素材；这个仓库当前提供源码，不提供 Linux 安装包或动画 Release。已有本机 Linux 安装时，可复制它的素材目录：

```sh
cp -a "${XDG_DATA_HOME:-$HOME/.local/share}/bailong-linux/current/outputs/白龙桌宠素材/." "outputs/白龙桌宠素材/"
./start-linux.sh
```

其他机器须从 [Windows 上游 Release](https://github.com/Wunsch2048/codex-bailong-desktop-pet/releases) 准备同版本的完整 `outputs/白龙桌宠素材/` 目录。动画文件及 `素材清单.json` 必须匹配 `app/material_catalog.json` 中 light 档的尺寸与 SHA-256；512px 默认素材和 720px 高清素材不能混用，文档演示图不能替代动画。

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
