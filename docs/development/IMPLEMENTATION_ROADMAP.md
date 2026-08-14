# 实施路线

原则：一次完成一个可验证的纵向阶段。所有任务引用需求/验收 ID；每阶段退出前更新 `docs/PROJECT_STATUS.md`。

## Phase 0A：文档决策与批准门（已完成文档，等待批准）

任务：

- 阅读原题、需求、ADR 和 API 契约。
- 确认精确 Node/Next.js、Python 包和 Java 构建工具版本。
- 定义统一错误代码、请求 ID 和环境变量命名。
- 固定输入硬边界、模型评估协议和正式开发就绪门。
- 获得仓库所有者明确批准。

退出条件：

- ADR 均为 Accepted 或明确 Deferred：已满足。
- 人类可读契约不存在关键语义歧义：已满足。
- 开发就绪审计 G0~G4 为 PASS：已满足。
- 所有者批准：等待中。

## Phase 0B：工程基线（仅在批准后执行）

任务：

- 创建 Python、Node 和 Java 最小工程脚手架与 lockfile。
- 将 API 契约转换为初始 OpenAPI/JSON Schema 或契约测试 fixtures。
- 校验成功/失败示例、错误 envelope 和字段路径。
- 固定 Docker 基础镜像 tag/digest，验证目标工具链和冻结安装。
- 运行最小 lint、type-check、test、build，不编写业务功能。

退出条件：

- `DEVELOPMENT_READINESS.md` 的 G6 为 PASS。
- 依赖版本可在目标开发机或目标容器中安装。
- API 示例可以通过 schema 校验。
- 三类空项目均可构建，且 lockfile 已纳入版本控制。
- 不得有契约歧义；失败时先更新 ADR/文档，不进入 Phase 1。

## Phase 1：数据、模型和 ML API

任务：

- 建立 `ml-api` Python 项目。
- 实现数据加载和数据契约校验。
- 实现 baseline LinearRegression。
- 实现 StandardScaler + Ridge 和规定的交叉验证。
- 生成模型、元数据和 10 条预测报告。
- 实现 `/predict`、`/model-info`、`/health`。
- 增加单元、API 和模型损坏测试。
- 添加 Dockerfile，并通过 Swagger 手工验证。

退出条件：

- AC-101~108 全部 PASS。
- 单条和批量请求的 OpenAPI 示例可直接执行。
- 模型指标由脚本生成，不含手填值。
- Docker 容器内外预测一致。

## Phase 2：Estimator API

任务：

- 建立第二个轻量 FastAPI 项目。
- 实现与 ML API 的超时客户端。
- 实现单条和批量 estimates。
- 映射下游 4xx/5xx/timeout。
- 添加 mock 客户端测试和真实 ML 集成测试。
- 添加 Dockerfile 与健康检查。

退出条件：

- EST-006~007、AC-206 相关后端部分 PASS。
- Estimator 中没有 sklearn 或模型文件依赖。
- ML API 停止时错误稳定、日志可关联。

## Phase 3：Market API

任务：

- 建立 Java 21 / Spring Boot 3.4.4 项目。
- 启动时校验并加载训练 CSV。
- 实现 summary、properties、segments、what-if、export。
- 实现 Caffeine TTL/size 上限和规范化缓存键。
- 实现 ML API HTTP 客户端和错误映射。
- 添加 controller、service、client、cache、export 测试。
- 添加 Dockerfile 与 health/readiness。

退出条件：

- MKT-006~010、AC-306~307 PASS。
- 统计值与源 CSV 对账。
- 可证明缓存命中且不同筛选条件不会串数据。
- CSV/PDF 导出内容可读取、非空。

## Phase 4：Next.js Portal

任务：

- 建立 App Router 项目和 Tailwind 设计 token。
- 完成共享 layout、导航、loading、error。
- 完成 Estimator 表单、结果、图表、历史、比较。
- 完成 Market RSC 首屏、筛选、图表、表格、what-if、导出。
- 实现 API client、自定义 Hooks 和稳定错误展示。
- 添加组件测试、可访问性测试和页面 E2E。

退出条件：

- AC-201~205、AC-301~305、AC-401~406 PASS。
- 真实浏览器无关键 console/network 错误。
- 360px 和 1280px 视口均完成视觉检查。
- 所有页面使用真实后端，不用硬编码假数据冒充集成完成。

## Phase 5：Compose 集成与系统测试

任务：

- 添加根 `compose.yaml` 和四个服务的健康依赖。
- 统一环境变量、网络、日志和只读数据挂载/构建策略。
- 添加契约测试和 Docker Compose E2E。
- 从干净环境验证 build、up、test、down。
- 完成故障注入测试。

退出条件：

- AC-001~004、AC-501~503 PASS。
- 一条命令启动全部服务。
- 所有展示功能在 Compose 网络中使用真实调用链。

## Phase 6：交付与面试彩排

任务：

- 补齐最终 README、架构图、指标、限制和排错。
- 添加示例 curl 和 Swagger 截图。
- 执行演示手册，控制在 8~12 分钟。
- 准备离线兜底：镜像预构建、端口检查、截图或短录屏。
- 可选：GitHub Actions 和公网部署。

退出条件：

- 所有必须验收项 PASS。
- GitHub 干净克隆验证通过。
- `PROJECT_STATUS.md` 不含虚假的已验证声明。
- 面试者可以解释架构取舍、模型限制和一个失败场景。

## 建议提交节奏

1. `docs: establish project specification`
2. `feat(ml-api): train and serve regression model`
3. `feat(estimator-api): add model-backed estimate service`
4. `feat(market-api): add analytics and what-if service`
5. `feat(web): build estimator and market portal`
6. `test: add compose and browser acceptance`
7. `docs: finalize interview runbook`

不要把未通过验收的阶段混入“项目完成”提交。
