# Housing Price Fullstack Interview Project

这是一个文档先行的面试项目仓库。目标是交付一套可现场演示的房价预测全栈系统：模型服务使用 FastAPI，房产估价应用使用 Python 后端，市场分析应用使用 Java/Spring Boot 后端，统一门户使用 Next.js。

## 当前状态

| 层级 | 状态 |
|---|---|
| 原始题目与数据归档 | 已完成并校验 |
| 需求、架构、接口、测试和实施文档 | 已完成开发前审计并获批准 |
| 工程基线 | Phase 0B 已验证通过 |
| 应用代码 | Phase 1（模型与 ML API）进行中 |
| Docker/本地运行 | 工具链已验证；业务镜像与 Compose 尚未实现 |
| 浏览器端到端验收 | 尚未执行 |
| 公网部署 | 不在当前已验证范围 |

不要把本文档中的目标架构、接口示例或验收条件描述为已经实现。

## 后续 AI 开发的阅读顺序

1. [AGENTS.md](AGENTS.md)
2. [文档索引](docs/INDEX.md)
3. [项目要求](docs/requirements/PROJECT_REQUIREMENTS.md)
4. [验收标准](docs/requirements/ACCEPTANCE_CRITERIA.md)
5. [系统架构](docs/architecture/SYSTEM_ARCHITECTURE.md)
6. [API 契约](docs/api/API_CONTRACTS.md)
7. [数据与模型设计](docs/architecture/DATA_AND_ML_DESIGN.md)
8. [实施路线](docs/development/IMPLEMENTATION_ROADMAP.md)
9. [测试策略](docs/testing/TEST_STRATEGY.md)
10. [本地运行与部署设计](docs/operations/LOCAL_RUN_AND_DEPLOYMENT.md)

## 硬性技术约束

- Python 3.12+
- FastAPI
- scikit-learn
- Next.js App Router
- Tailwind CSS
- Java 21
- Spring Boot 3.4.4
- Docker 容器化
- GitHub 源码交付
- 面试现场可演示

冻结的直接版本和 lockfile 策略见 [ADR-004](docs/adr/ADR-004-version-pinning.md)。版本选择基于 2026-08-14 官方兼容性快照；正式实现使用 lockfile 和容器镜像摘要保持可复现。

## 目标系统

- `ml-api`：训练产物加载、单条/批量房价预测、模型信息和健康检查。
- `estimator-api`：App 1 的 Python 业务后端，校验请求并调用 `ml-api`。
- `market-api`：App 2 的 Java 业务后端，完成数据聚合、筛选、缓存和 what-if 调用。
- `web`：统一 Next.js Portal，提供估价和市场分析两个应用。

## 仓库结构

```text
.
├─ apps/web/                  # Next.js Portal，已有 Phase 0B 最小工程
├─ services/
│  ├─ ml-api/                 # FastAPI 模型服务，Phase 1 进行中
│  ├─ estimator-api/          # Python 估价业务服务，已有最小工程
│  └─ market-api/             # Spring Boot 市场服务，已有最小工程
├─ packages/api-contracts/    # OpenAPI 3.1 与共享 schema 基线
├─ data/raw/                  # 原始 CSV，只读
├─ models/                    # 后续生成的模型产物，不提交大文件
├─ infra/docker/              # 后续 Docker 配置
├─ tests/e2e/                 # 后续端到端测试
├─ docs/                      # 项目事实与设计的主要入口
└─ references/original/       # 面试官原始题目，只读
```

## 原始资料

- [原始题目 PDF](references/original/Interview%20Tasks%20Fullstack.pdf)
- [训练数据](data/raw/House%20Price%20Dataset.csv)
- [待预测数据](data/raw/Test%20Data%20For%20Prediction.csv)
- [资料清单与 SHA-256](references/README.md)

## 开发启动条件

文档决策和 Phase 0B 工程基线均已完成，G0~G6 为 PASS；运行证据见 [正式开发就绪审计](docs/development/DEVELOPMENT_READINESS.md)。当前按路线实施 Phase 1。

默认顺序为模型与 ML API、Estimator API、Market API、Next.js Portal、Compose 集成、真实浏览器验收。
