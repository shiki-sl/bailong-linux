# 来源与授权说明

原项目：https://github.com/jingh12312-rgb/bailong-desktop-pet

本地改造基线：白龙桌宠 v0.3.3。原角色、初始15段动画和基础程序来源于原项目；后续合入上游v0.4.1的10段新动作，共25段播放素材，并增加Codex联动、状态气泡、统计日报、交互与部署优化。

发布者于 2026-10-21 确认已取得原作者对本次源码、角色素材和安装包公开再分发的授权。此记录是发布者的确认，不代表原作者向所有访问者另行授予权利，也不覆盖第三方组件。原项目未附统一代码许可证；请勿因仓库公开而推定为 MIT、可自由商用或不受限制的再分发。

原素材声明完整保留在 docs/upstream/ASSETS.md。角色动画随 Release 分发，不放入 Git 历史。若希望另作商业使用、改编或再分发，请向相应权利人确认许可范围。

字体 Chakra Petch 来自 Google Fonts，按随附 SIL Open Font License 使用。Qt/PySide6、Pillow、msgspec、comtypes 等依赖按各自许可证分发。app/licenses 保存已有组件声明；打包运行库还包含其自身许可文件。本 NOTICE 不替代这些许可。

UI 图表截图与 GIF 使用隔离演示数据。开发报告的项目模型用量图只公开累计汇总，不含会话原文、账号或密钥。

上游v0.4.1的素材声明另原样保留在[ASSETS-v0.4.1.md](docs/upstream/ASSETS-v0.4.1.md)。此次新增素材继续遵从同一授权边界，没有替它们另行授予商用、改编或再分发许可。

## Linux 适配

Linux 适配仓库：https://github.com/shiki-sl/bailong-linux 。基于 Wunsch2048/codex-bailong-desktop-pet 0.8.3，保留其来源、素材和组件声明；上述再分发授权确认是 Windows 上游发布者的历史声明，本仓库不扩大该声明的授权范围，也不将整个项目标为 MIT。角色动画不纳入本仓库 Git 历史。

金额与速率采集使用 Tokscale 4.18.0，其 MIT 许可证及来源记录位于 vendor/tokscale/；此许可仅覆盖对应第三方组件。价格 JSON 是公共模型目录的静态种子，不包含本机账户、会话或用量。
