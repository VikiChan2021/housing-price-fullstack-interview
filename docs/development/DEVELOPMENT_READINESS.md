# 正式开发就绪审计

审计日期：2026-08-14

## 1. 结论

仓库的需求、架构、接口、模型、测试、运行和演示文档已经形成闭环，原始题目的必做项均可追踪到需求与验收标准。经过本次补充后，**文档层面已具备开始正式开发的条件**。

正式开发当前仍为 `BLOCKED_BY_APPROVAL`：尚未获得仓库所有者批准。本状态不是技术缺陷，也不得通过创建脚手架、锁文件、模型或应用代码来绕过。

批准后先执行路线图 Phase 0B（工程基线），其结果是“依赖能够解析、契约能够机器校验、工具链能够运行”；通过后才进入模型和业务代码阶段。

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
| G5 所有者批准 | 明确允许开始 Phase 0B/正式开发 | WAITING | 本轮结束后等待用户批准 |
| G6 工程基线可运行 | 锁文件、构建工具、OpenAPI 基线通过验证 | NOT RUN | 批准后执行 Phase 0B |

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

## 5. 当前开发机预检（不等于项目验收）

2026-08-14 的只读预检结果：

- Git 可用，工作分支为 `main`，检查前工作区无改动。
- Docker CLI 29.6.2、Compose v5.3.1 已安装，但 Docker Desktop Linux Engine 未运行。
- 当前 PATH 中 Node.js 为 22.22.0，不是冻结的 Node 24.18.0。
- 当前仅发现 Python 3.11.9，没有 Python 3.12。
- 当前 PATH 中没有 Java。

这不阻塞文档批准，但会阻塞本机直接运行 Phase 0B。批准开发后可优先使用 Docker 化工具链；执行 Compose 验收前必须启动 Docker Engine。若需要宿主机直接开发，则安装或通过版本管理器提供冻结版本，不覆盖系统现有运行时。

## 6. 批准后的第一批动作

1. 为两个 Python 服务分别创建 `pyproject.toml` 与 `uv.lock`，在 `apps/web` 创建 `package.json` 与 `pnpm-lock.yaml`，在 `market-api` 创建 Maven Wrapper；只生成最小脚手架与 lockfile。
2. 验证 Python 3.12、uv 0.11.32、Node 24、Java 21、Maven 3.9.16 和 Docker 构建工具链。
3. 把人类可读契约转换为初始 OpenAPI/JSON Schema fixtures；校验全部示例和统一错误 envelope。
4. 固定基础镜像不可变摘要，记录构建平台；运行依赖安装和最小空项目构建。
5. 更新本文件 G6、`PROJECT_STATUS.md` 和追踪矩阵；只有 G6 PASS 才开始 Phase 1。

## 7. 变更控制

- 未获批准前，只允许继续审阅或修改文档。
- 批准应明确指出允许进入 Phase 0B；未明确扩大范围时，不包含公网部署和可选加分项。
- 版本、安全或原题理解发生变化时，先更新 ADR/需求/追踪矩阵，再改代码。
- 任何未执行验证必须保留为 `NOT RUN`，不得以“配置已写”替代运行证据。
