# SRF 文件与协议设计

- 状态：PH-07 FP-02候选协议，F06–F11待负责人确认；非运行规范、非已实现解析器。F01–F05已批准，物理架构见[目录规划](SRF_REPOSITORY_LAYOUT.md)。
- 依据：[详细设计](SRF_DETAILED_DESIGN.md) J01/J02/J09/J10/J35及J01–J37整体基线、[概要设计](SRF_ARCHITECTURE_DESIGN.md)、[正式需求](../project/SRF_REQUIREMENTS_SPECIFICATION.md)。本文件为FP-02–06协议字段、语义、样例及验证设计唯一研发入口，后续原位补充；不复制目录架构或详细设计全文。PH-08/09实施，PH-10/11实际验证，PH-12经授权发布。

## 1. FP-02 入口、索引与模块加载

### 1.1 表达格式与最小索引（F06）

推荐 UTF-8 JSON（无BOM、单一对象），源文件 framework/manifest.json、部署 .srf/manifest.json，替代FP-01暂定manifest.yaml；待F06批准后才原位更新目录规划，不兼容双索引或自动回退。JSON结构可由一般解析工具处理，便于严格类型、路径、引用和依赖检查；Markdown适合正文，不适合复杂机器索引；YAML可读性好但额外语法与解析差异需要限制。依据公开非仓库标准[RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.html)第4/8节（唯一成员名、UTF-8及互操作）与[YAML 1.2.2](https://yaml.org/spec/1.2.2/)相关语法说明（本轮检索结果选段，非全文研读）。JSON不自动安全：严格拒绝重复对象键（包括转义后同名）、非法编码、截断、重复ID/路径、未知字段、错误类型/版本；普通JSON.parse可能吞掉重复键，正式检查必须在对象折叠前识别。禁止注释、尾随逗号、非标准值及执行型表达。限制输入体积、深度和读取次数由真实环境校准，超限不自动截断后继续。框架独立于解析器，不能可靠核验时阻塞依赖操作并交接，不把AI目测当严格解析证据。

| 字段 | 类型/要求 | 权威语义 |
|---|---|---|
| schema_version | 整数，当前候选1，必需 | 索引协议代际，不是框架发布版本；未知版本停止，不按旧协议猜测 |
| entrypoint | 相对路径字符串，必需 | 指向已安装且受信的启动指令源，不能由任意索引改变根 |
| modules | 模块对象数组，必需 | 每项id/path/kind/requires/triggers，唯一ID及路径，未声明不可自动启用 |
| assets | 资源对象数组，必需，可为空 | path/kind/owner；仅实际存在的知识、模板及必要支持资源；owner指向模块ID，不授予权限 |

模块字段：id为稳定标识；path为包内Markdown相对路径；kind为core/adapter/capability/evolution/extension之一；requires为直接必要规范前置ID数组（无重复、允许空）；triggers为非空且唯一的短语义标签数组（小写英文字母起始、字母数字连字符），只辅助定位而非自然语言分类器或执行条件。实际触发/排除、前置、输出/失败等由模块正文契约解释。资产kind候选reference/template/support分别限定knowledge/、templates/、entrypoints/必要支持资源；不得包含执行脚本或外部URL。安装工具、许可及版本/产物证据的必要结构由FP-06补充，而非本轮冻结完整发布协议。

核心、入口、实际模块及已声明资源组成源发布选择入口；不能把目录或未审核文件默认纳入包。最终产物实际清单、版本、摘要、源提交及兼容在FP-06决定，若需扩展字段先经授权修订协议。当前样例不宣称实际包已存在。入口与索引自身不作为运行模块节点，避免索引自依赖。路径相对包根，拒绝绝对路径、空段、点/点点、反斜线、URL、大小写折叠冲突及保留/非法平台路径；允许的ASCII段和真实文件类型、符号链接/重定向必须按实际工具与平台校验，不凭字符串证明解包安全。各模块路径必须符合物理职责，入口路径固定，不能由远端任意值改变可信启动位置。

### 1.2 稳定标识、正文契约与规则定位（F07）

模块ID候选 srf.<语义名>（小写字母起始、字母数字及点/连字符分段），不由路径或版本自动生成；首版14个明确模块，见1.3样例。扩展ID按同一语法且经有效配置及索引准入，必须唯一，不能占用既有ID。规则ID候选 SRF-R-<初始职责命名空间>-<三位序号>，全框架唯一，命名空间用于首次分配而非当前物理归属；不复用退役ID，不因文件移动或条款顺序变化改号。规则拆合或语义破坏性变化须评估消费者/兼容并保留必要迁移定位，不建常规历史文件。普通知识条目不强制编号；重要可追踪约束、公开契约和验收关联需要稳定定位。

正文Markdown固定契约节 `## CONTRACT`：身份/职责及非职责；触发/排除；输入输出/实际前置；权限与执行边界；完成、证据、失败/交接；必要需求/决定/测试关联。索引拥有ID/路径/类型/直接依赖/定位标签的唯一元数据定义，正文不复制这些字段，契约中的身份仅以模块ID定位并与索引一致核验；具体格式候选 `Module: srf.design` 紧随契约标题。规则标题候选 `### SRF-R-GOV-001 | MUST`，紧随自然语言适用范围、约束及例外/覆盖声明（适用时）、证据和必要关联；标题类型是规则性质，不自动赋予效力。五类类型及三个层级仍按J01解释，框架正文中规则属于框架层，项目/任务约束由FP-03定位，不以标题提升其层级。规则引用使用ID及必要版本/适用范围，解析时由已核实索引模块路径与正文精确标题定位，不依赖Markdown渲染器自动锚点。不得以字符串搜索命中代替完整规则及上下文解释。

规则全量二级索引如确有需求由确定性工具从规范正文导出（可在内存生成）；不维护第二份手工ID→路径表。运行按模块/职责/标签缩小搜索，遇已知规则ID可在当前可信范围查找，不能全局搜索其他仓库。PH-07/08结构检查须辨识真实Markdown标题与代码块/引用示例（不把示例当规则）；实际标题重复、失效引用、未知性质或契约身份不符均阻塞依赖规则，其他合法独立分析可继续。复杂语义冲突仍按J01由AI及必要人工审查，不能由正则判断。需求、设计、测试关联在权威正文/测试处按J10保存，反向查询可派生；不要求每条规则建独立文件。

### 1.3 候选完整模块索引示例（设计数据，非实际文件）

下例为批准前的完整14模块样例，路径与FP-01的16个文件（除暂定索引格式）对应。源索引和发布索引不维护双份权威，正式Release按FP-06绑定实际产物。

```json
{
  "schema_version": 1,
  "entrypoint": "entrypoints/PROJECT_INSTRUCTIONS.md",
  "modules": [
    {
      "id": "srf.governance",
      "path": "core/governance.md",
      "kind": "core",
      "requires": [],
      "triggers": [
        "startup"
      ]
    },
    {
      "id": "srf.collaboration",
      "path": "core/collaboration.md",
      "kind": "core",
      "requires": [
        "srf.governance"
      ],
      "triggers": [
        "intent",
        "authorization"
      ]
    },
    {
      "id": "srf.facts",
      "path": "orchestration/facts-context.md",
      "kind": "core",
      "requires": [
        "srf.governance"
      ],
      "triggers": [
        "facts",
        "recovery"
      ]
    },
    {
      "id": "srf.engineering",
      "path": "governance/engineering.md",
      "kind": "core",
      "requires": [
        "srf.governance",
        "srf.collaboration",
        "srf.facts"
      ],
      "triggers": [
        "risk",
        "quality"
      ]
    },
    {
      "id": "srf.execution",
      "path": "adapters/execution.md",
      "kind": "core",
      "requires": [
        "srf.governance",
        "srf.collaboration",
        "srf.facts"
      ],
      "triggers": [
        "execution"
      ]
    },
    {
      "id": "srf.workflow",
      "path": "orchestration/workflow.md",
      "kind": "core",
      "requires": [
        "srf.governance",
        "srf.collaboration",
        "srf.facts",
        "srf.engineering",
        "srf.execution"
      ],
      "triggers": [
        "task"
      ]
    },
    {
      "id": "srf.github",
      "path": "adapters/github.md",
      "kind": "adapter",
      "requires": [
        "srf.execution"
      ],
      "triggers": [
        "github"
      ]
    },
    {
      "id": "srf.professional",
      "path": "capabilities/common.md",
      "kind": "capability",
      "requires": [
        "srf.governance"
      ],
      "triggers": [
        "professional"
      ]
    },
    {
      "id": "srf.requirements",
      "path": "capabilities/requirements.md",
      "kind": "capability",
      "requires": [
        "srf.professional"
      ],
      "triggers": [
        "requirements"
      ]
    },
    {
      "id": "srf.design",
      "path": "capabilities/design.md",
      "kind": "capability",
      "requires": [
        "srf.professional"
      ],
      "triggers": [
        "design"
      ]
    },
    {
      "id": "srf.development",
      "path": "capabilities/development.md",
      "kind": "capability",
      "requires": [
        "srf.professional"
      ],
      "triggers": [
        "development",
        "review"
      ]
    },
    {
      "id": "srf.testing",
      "path": "capabilities/testing.md",
      "kind": "capability",
      "requires": [
        "srf.professional"
      ],
      "triggers": [
        "testing"
      ]
    },
    {
      "id": "srf.delivery",
      "path": "capabilities/delivery.md",
      "kind": "capability",
      "requires": [
        "srf.professional"
      ],
      "triggers": [
        "delivery",
        "maintenance"
      ]
    },
    {
      "id": "srf.lifecycle",
      "path": "evolution/lifecycle.md",
      "kind": "evolution",
      "requires": [
        "srf.governance"
      ],
      "triggers": [
        "feedback",
        "lifecycle"
      ]
    }
  ],
  "assets": []
}
```

### 1.4 必要依赖闭包及加载准入（F08）

14模块、21条直接必要规范前置边；六核心节点保持原概要13条内部边，GitHub→execution、专业共用→governance、五专业→professional、生命周期→governance 为细化边。映射M01–06各一个核心节点，M05另含GitHub适配，M07含专业共用及五专业，M08生命周期，M09为按有效配置另行准入的可选扩展（不伪造首版已建模块）。将同逻辑单元内部边折叠后，保留概要已批准关系；M09未实体化故其边不计入21条。common对知识来源/证据的使用是语义消费，解释其专业契约仅需governance；执行活动仍消费facts/其他核心，不形成额外规范加载循环。

算法：确认索引来源/版本/路径及完整性 → 严格解析结构及所有声明依赖，拒绝未知节点、重复边、自环、环、核心缺失或依赖可选模块 → 按任务目标与实际能力选择必要模块 → 求直接依赖传递闭包去重，依赖优先确定性拓扑排序（同级可按稳定ID排序，不靠数组顺序决定权限）→ 按版本及权威定位取得完整必要契约与相关规则，核实实际内容/身份/适用性/冲突 → 输出已核实读取引用、缺失及阻塞范围。全图结构有效不等于所有模块都需要读正文；声明结构无效且无法确定影响时阻塞正常运行，不能静默删掉必需边。有效结构内非当前可选能力实际不可用时仅阻塞其依赖活动；若发布清单/运行包完整性要求不成立，先按J35阻塞依赖有效版本的活动。规则来源、覆盖、引用和调用结果不混入必要加载图。核心集合由批准架构/可信产物确定，当前六项不可由索引kind篡改删除；工作流闭包必须恰含六核心。兼容变化需审批及版本迁移，不能以核心节点写死后忽略正式变更。

| 请求解释范围 | 依赖闭包（含请求自身） |
|---|---|
| srf.workflow | 6核心 |
| srf.design | governance、professional、design（3） |
| srf.github | governance、collaboration、facts、execution、github（5） |
| 正常开发+GitHub（workflow+development+github） | 6核心+professional+development+github（9） |
| 正常生命周期（workflow+lifecycle） | 6核心+lifecycle（7） |

解释单个专业/工具规范的闭包不是执行准入；任何正常有副作用任务仍需完整适用核心闭环、事实、有效授权、风险及真实工具前置。正常分析也不能遗漏适用核心约束，不要求全量核心正文每次重读；保留可信且仍适用的完整必要契约及相关条款。扩展只可按有效配置选择，兼容、来源、核心保护、真实能力、权限及测试条件须核实，未启用不加载，不可将扩展设为核心必要前置；具体启用与兼容由FP-03/06决定。

### 1.5 稳定入口与可信自举（F09）

稳定入口为安装后用户实际导入/配置的 .srf/entrypoints/PROJECT_INSTRUCTIONS.md 对应内容，不假定平台会自动读取它。Project根绑定、允许引用及最低安全准入来自用户实际有效配置，入口不能从待核实远端索引获得根信任，也不含通用用户的具体仓库值。入口保留必要自举约束，与core/governance.md权威语义一致；PH-08/09从已确认权威规则生成或逐项核对最小摘录，记录可验证来源及版本，FP-03/06定义实际激活/完整性证据；不允许两份独立可修改治理源。若平台无法核实实际设置，报告限制并要求必要人工证据，而非推断入口已生效。

启动顺序：①核实有效Project配置、对象/允许引用、工具可限定范围及读权限，任何未知停止相关读取；②仅最小限定只读核实仓库身份、实际提交/锁定包及可信入口/索引位置，每次核对参数和返回；③核实可信指定产物、受管文件、配置及入口一致性（J35），严格索引结构及版本，读取必要治理及核心契约；④定位现有权威状态/任务及实际结果，按J36重新判当前授权、按J37确认结果而非复用状态文字；⑤选择任务活动和模块闭包，加载必要上下文，再按正常执行准入开展。初始只读不可写、不能扫描无关范围；身份不符停止，不处理越界数据，不自动回退其他仓库/版本/索引。实际版本、配置、授权和能力变化时重新核实；历史摘要不替代权威状态。PH-08验证试验入口，PH-09形成软件Project正式启动指令，本研发中心入口保持独立。

### 1.6 上下文预算、增量加载与恢复（F10）

沿J09四视角，不新增存储或固定token配额。启动视角先保根、版本和适用核心；任务视角保目标、范围、有效授权、基线、验收、未决/未知；专业视角按活动与闭包取得必要契约、相关完整规则和具体实现/测试；扩展视角仅按价值增加历史、参考、模板与领域扩展。读取前检查实际工具能否提供完整内容/分页/范围；记录或保留可核实引用（对象、版本、路径、模块/规则ID及完整性/范围）。缓存仅用于同一有效基线与相同适用条件，身份/版本/配置/权限/事实变化或返回冲突触发失效；不把跨会话记忆作有效加载。重复前置按ID+已核实版本去重，按稳定引用定位，不能把摘要代替安全关键规则；范围读取须含完整相关条款及其适用条件/例外/依赖，否则补读。工具不能可靠分段或正文截断时，先合法补齐或缩小任务，不能从缺失片段推断规则。

预算压力处理顺序：去重及不相关历史→延迟非必要扩展/参考→分阶段活动、缩小可安全完成范围→保留必要安全、权限、质量与恢复前置；仍不够则停止受影响动作，明确缺失及交接，不删除关键约束以“继续”。未知实际上下文上限/模型费用不虚构数值；PH-08/10试测记录读取文件/段数、重复读取、实际可测token/耗时、遗漏规则及误拒，阈值由正式测试方案决定。合法低风险普通任务不输出完整加载日志；重大风险、冲突、失败和恢复保留最小可定位证据。不能读取必要前置不意味着允许降格执行；任务或配置变化重新选择，不默认全量重载。

### 1.7 兼容、确定性验证及交接（F11）

索引协议schema_version独立于SRF整体版本，仅在必要不兼容协议变化时提高；当前严格模式未知字段/版本停止，未来增加字段须评估旧消费者可否解析，不能仅因“新增字段”宣称兼容。FP-06定义实际公共契约兼容和版本协商；不自动尝试多种解析器、双索引或绕过未知安全字段。索引路径、模块ID/规则ID和公开契约属于拟议稳定定位边界，内部路径迁移须保持ID和更新引用，必要迁移与回滚按J31/32授权，当前无已发布消费者。正式文件校验应检查实际文件存在/类型/完整性、严格解析及字段、模块和规则身份、前置图、核心闭包、索引/清单一致、权限不可由元数据扩大、引用存在与发布边界；语义冲突及实际加载行为另验。

本次实际内存原型：JSON.stringify/parse往返、14模块/21边、16路径对应FP-01、六核心闭包、5个代表闭包及1个合成可选扩展检查通过；15项结构负例拒绝（duplicate module ID、duplicate path、case collision、missing dependency、cycle、self cycle、path escape、absolute path、research path、unknown schema version、unknown field、missing core、core depends on optional、unknown asset owner、duplicate edge）；2个合成规则标题定位、重复规则和未知引用两项负例拒绝。候选路径没有真实创建；用内存对象校验器验证字段/类型/路径/图，不是生产解析器，未验证原始JSON重复键拒绝、UTF-8字节/截断/限制、实际Markdown代码块解析、真实文件存在、符号链接、完整性、权限及AI行为。示例规则正则仅处理合成无代码块文本；不得声称已验证真实规则提取。正式PH-08/10必须覆盖这些未测项并按J35/36/37验证启动恢复、非法配置/规则冲突和预算不足；负例不得访问白名单外仓库。实际原型结果只证明该模型上的结构判定。

| 需求 | FP-02设计定位及后续验证 |
|---|---|
| 003/005 | 1.2/1.5规则性质与生效、根准入；FP-03覆盖协议，PH-10冲突/越权负例 |
| 004/044/049 | 1.1–1.4/1.7身份、完整契约、DAG及真实检查；PH-08/10实际索引/替换/失败 |
| 006/022/031 | 1.4/1.6扩展与专业知识按需，保留来源/许可；PH-09/10真实能力与不兼容负例 |
| 030/033/051 | 1.5/1.6独立入口、根/版本/状态/授权恢复及预算；FP-03/04与PH-08–11实测 |
| 032/046/048 | 1.1/1.2/1.7唯一定位、稳定标识、无重复索引；FP-06兼容，PH-10/11迁移 |

## 2. FP-02 重要公共协议决策（候选）

| ID | 推荐取舍 | 主要边界 |
|---|---|---|
| F06 | 单一严格JSON索引及候选最小字段 | manifest.json替代暂定manifest.yaml，严格解析、未知阻塞；FP-06完善产物清单，批准前不改目录约定 |
| F07 | 稳定模块ID/规则ID、Markdown契约及唯一定位 | 14个模块标识、规则类型标题、索引元数据唯一，规则定位可派生；不建重复手工索引，不冻结全部规则编号 |
| F08 | 14节点21边必要加载图及闭包准入 | 六核心完整，专业/适配/演进按需，扩展不入核心；解释与执行分离，不把调用关系当依赖 |
| F09 | 可信入口与最低限定只读自举 | J35根准入、锁定版本/实际入口一致、J36/J37恢复；无权限扩大，不假定平台自动加载 |
| F10 | 四视角预算、增量读取、去重和失效 | 必要规则优先、完整条款、未知/截断/不足阻塞或交接；不固定token阈值 |
| F11 | 严格兼容及确定性校验边界 | schema_version未知拒绝，结构/语义/实际行为分开，内存验证不是实现；FP-06/07补全、PH-08/10/11实测 |

F06–F11待负责人确认，不成为正式运行规范、执行授权或冻结协议；批准后按F06原位调整目录索引路径、更新协议及状态，再开展FP-03项目配置与授权协议。PH-07未结项。
