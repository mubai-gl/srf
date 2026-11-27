# SRF 研发中心：仓库入口

本仓库研发 SRF 本身，不开展具体软件业务研发。依据 GPT Project 指令第 0 节的仓库绑定配置确认实际仓库、目标分支、授权和工具能力，再按任务加载文件。执行 Project 指令第 0 节的单仓库白名单：仅访问绑定仓库，禁止全局枚举、无范围搜索及跨仓库访问；每次调用前核对范围，调用后核实身份。配置缺失或身份冲突时停止相关 GitHub 访问；写入显式指定仓库和目标分支。首次正式发布前仅使用 `main`，不创建其他分支或 PR；初始化测试顺序见路线图第 5 节。

- 研发中心启动指令：[instructions/SRF_PROJECT_INSTRUCTIONS.md](instructions/SRF_PROJECT_INSTRUCTIONS.md)
- 当前状态：[management/PROJECT_STATE.md](management/PROJECT_STATE.md)
- 基线与目录导航：[README.md](README.md)

以上入口不自动授予写入权限。遵循当前已批准规则及用户授权，不擅自修改核心治理；不虚构工具执行结果。普通文件保持稳定路径，使用 Git 原生版本管理。初始文件与实际运行框架隔离，按需加载，不重复维护完整规则。
