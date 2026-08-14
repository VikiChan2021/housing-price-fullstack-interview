# 正式开发就绪审计

审计日期：2026-08-14

## 1. 结论

仓库所有者已于 2026-08-14 明确批准进入 Phase 0B。工程基线已完成运行验证，G0~G6 全部为 `PASS`，因此项目已解除批准与工程阻塞，可以依照路线进入 Phase 1。

此结论只代表“依赖可复现、契约可机器校验、三类最小项目可构建”。业务功能、Compose、浏览器验收和公网部署仍必须按阶段分别验证，不能据此描述为已完成。

## 2. 原题覆盖审计

| 原题区域 | 规范入口 | 验收入口 | 结论 |
|---|---|---|---|
| Task 1：回归模型、单条/批量预测、模型信息、健康检查、Docker/Swagger | `PROJECT_REQUIREMENTS.md` 的 ML-001~008；`API_CONTRACTS.md` | AC-101~108 | 已覆盖 |
| Portal：共享布局、App Router、设计系统、loading/error | SYS-001~002、WEB-001~009；前端 UX 规格 | AC-401~406 | 已覆盖 |
| App 1：Python 后端、校验、图表、历史、比较 | EST-001~007 | AC-201~206 | 已覆盖 |
| App 2：Java 后端、统计、筛选、what-if、CSV/PDF、表格、缓存 | MKT-001~010 | AC-301~307 | 已覆盖 |
| GitHub 与现场演示 | DEL-001~005；本地运行设计；演示手册 | AC-001~004、AC-501~506 | 已覆盖 |

审计以 `references/original/Interview Tasks Fullstack.pdf` 为最高事实来源。PDF 共 3 页；原件及两份 CSV 的 SHA-256 与 `references/README.md` 一致。只读数据检查确认训练集 50 行、预测集 10 行，字段集合与数据设计一致。

## 3. 就绪门

| Gate | 条件 | 当前状态 | 证据/动作 |
|---|---|---|---|
| G0 来源完整 | 原始 PDF/CSV 未改动，哈希匹配 | PASS | `references/README.md` |
| G1 需求完整 | 原题要求均有需求 ID 和验收 ID | PASS | 需求追踪矩阵 |
| G2 架构已决策 | 所有实现前 ADR 为 Accepted 或 Deferred | PASS | ADR-001~004 均为 Accepted |
| G3 契约无关键语义歧义 | 路径、字段、边界、错误、批量上限明确 | PASS | API 契约第 1~6 节 |
| G4 模型协议可复现 | 特征、CV、alpha 选择、产物元数据明确 | PASS | 数据与模型设计第 5~7 节 |
| G5 所有者批准 | 明确允许开始 Phase 0B/正式开发 | PASS | 2026-08-14 用户明确批准“进入 Phase 0B，并按路线继续正式开发” |
| G6 工程基线可运行 | 锁文件、构建工具、OpenAPI 基线通过验证 | PASS | 见第 5 节 Phase 0B 运行证据 |

只有 G0~G5 为 PASS 才能创建工程脚手架。只有 G6 PASS 才能进入 Phase 1。

## 4. 冻结的直接技术基线

版本选择快照日期为 2026-08-14。直接依赖按下表固定；传递依赖由 lockfile 固定，禁止使用未锁定的 `latest` 参与 CI 或 Docker 构建。

| 区域 | 基线 |
|---|---|
| Python | Python 3.12.13；uv 0.11.32；两个 Python 服务各自使用 `uv.lock` |
| Python API/ML | FastAPI 0.139.2；scikit-learn 1.9.0 |
| Web runtime | Node.js 24.18.0 LTS；pnpm 11.15.1 |
| Web framework | Next.js 16.2.12；React/React DOM 19.2.8；Tailwind CSS 4.3.3 |
| Java | Java 21；Spring Boot 3.4.4（原题固定） |
| Java build | Maven Wrapper 3.9.16 |

测试库、图表库、OpenAPI 生成器和 PDF 库在 Phase 0B 选择最小集合并精确锁定；选择不得改变已接受的 API 或服务边界。若直接依赖无法在目标容器中共同安装，停止开发、记录失败证据并更新 ADR-004，不得静默换版本。

官方核对入口：

- [Next.js 安装与 Node 要求](https://nextjs.org/docs/app/getting-started/installation)
- [Node.js 发布与 LTS 状态](https://nodejs.org/en/about/previous-releases)
- [Tailwind CSS 的 Next.js 安装方式](https://tailwindcss.com/docs/installation/framework-guides/nextjs)
- [FastAPI 安装与 uv lockfile](https://fastapi.tiangolo.com/tutorial/)
- [uv 安装与版本固定](https://docs.astral.sh/uv/getting-started/installation/)
- [scikit-learn 安装说明](https://scikit-learn.org/stable/install.html)
- [Spring Boot 3.4 系统要求](https://docs.spring.io/spring-boot/3.4/system-requirements.html)
- [Maven 发布历史](https://maven.apache.org/docs/history)

## 5. Phase 0B 运行证据（不等于业务验收）

2026-08-14 已执行：

- 两个 Python 服务均由 uv 0.11.32 使用 Python 3.12.13 完成 `uv lock --check`、冻结运行、Ruff、严格 mypy、pytest 和覆盖率门槛；最小健康检查各 2 项通过，覆盖率 100%。
- Web 在 `node:24-slim` 的 linux/amd64 目标容器内，以 pnpm 11.15.1 冻结安装后通过 ESLint、TypeScript、Vitest、OpenAPI lint 和 Next.js 16.2.12 生产构建。
- Java 工程在 `maven:3.9.16-eclipse-temurin-21` 的 linux/amd64 目标容器内通过 Maven Wrapper 构建和 2 项 Spring MVC 测试。
- `ml-api`、`estimator-api`、`market-api` 三份 OpenAPI 3.1 基线及共享 JSON Schema 通过 Redocly recommended 规则校验；健康检查端点按约定跳过不适用的 `operation-4xx-response` 规则。
- Docker Engine 29.6.2 已启动并用于目标容器验证；宿主机原有 Node 22、Python 3.11 和 Java 缺失未被覆盖。

冻结镜像（linux/amd64）：

- `node@sha256:b31e7a42fdf8b8aa5f5ed477c72d694301273f1069c5a2f71d53c6482e99a2fc`
- `python@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf`
- `maven@sha256:c07f7ccfb8ca6c9fa29ee523f00afa7d2ca6132c92f8652c4aebb5ee3491f502`

## 6. Phase 0B 已执行动作

1. 为两个 Python 服务分别创建 `pyproject.toml` 与 `uv.lock`，在 `apps/web` 创建 `package.json` 与 `pnpm-lock.yaml`，在 `market-api` 创建 Maven Wrapper；只生成最小脚手架与 lockfile。
2. 验证 Python 3.12、uv 0.11.32、Node 24、Java 21、Maven 3.9.16 和 Docker 构建工具链。
3. 把人类可读契约转换为初始 OpenAPI/JSON Schema fixtures；校验全部示例和统一错误 envelope。
4. 固定基础镜像不可变摘要，记录构建平台；运行依赖安装和最小空项目构建。
5. 更新本文件 G6 与 `PROJECT_STATUS.md`；G6 已为 PASS，下一阶段为 Phase 1。

## 7. 变更控制

- 本次批准覆盖路线中的正式开发，不包含公网部署和可选加分项。
- 版本、安全或原题理解发生变化时，先更新 ADR/需求/追踪矩阵，再改代码。
- 任何未执行验证必须保留为 `NOT RUN`，不得以“配置已写”替代运行证据。
