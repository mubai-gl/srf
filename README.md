# SRF · 通用软件研发协作框架

SRF 自身的研发主仓库。当前为研发启动阶段，尚未形成可部署的正式框架。

最高设计要求：框架内部可以复杂，但用户使用起来必须简单；框架变更必须可定位、可控制、可验证、可恢复。

## 导航

| 内容 | 入口 |
|---|---|
| 项目章程 | [项目章程](docs/project/SRF_PROJECT_CHARTER.md) |
| 初始需求 | [初始需求](docs/project/SRF_INITIAL_REQUIREMENTS.md) |
| 研发计划 | [研发路线图](docs/project/SRF_DEVELOPMENT_ROADMAP.md) |
| 架构 | [顶层设计](docs/architecture/SRF_TOP_LEVEL_DESIGN.md) |
| 仓库组织 | [目录规划](docs/architecture/SRF_REPOSITORY_LAYOUT.md) |
| 研发现场 | [当前状态](management/PROJECT_STATE.md) |
| GPT Project | [研发中心指令](instructions/SRF_PROJECT_INSTRUCTIONS.md) |
| AI 入口 | [AGENTS.md](AGENTS.md) |

当前文件是研发启动资料，不是 SRF 正式运行包。初始化流程见研发路线图第 5 节：先上传启动资料并配置 SRF Project，再在 `main` 经授权实测 GitHub，基础通过后才写入正式基线，最后新对话验证恢复。首次正式发布前仅使用 `main`，不建立其他分支或 PR。后续运行规范位于 framework/，由正式研发逐步建立；整体发布使用 Git Tag 与 GitHub Releases。
