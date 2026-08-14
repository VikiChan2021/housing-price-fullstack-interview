# Housing Price Fullstack Interview Project

这是一个文档先行的面试项目仓库。目标是交付一套可现场演示的房价预测全栈系统：模型服务使用 FastAPI，房产估价应用使用 Python 后端，市场分析应用使用 Java/Spring Boot 后端，统一门户使用 Next.js。

## 当前状态

| 层级 | 状态 |
|---|---|
| 原始题目与数据归档 | 已完成并校验 |
| 需求、架构、接口、测试和实施文档 | 已完成初版 |
| 应用代码 | 尚未开始 |
| Docker/本地运行 | 尚未实现、尚未验证 |
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

Next.js、Node.js 和其余依赖的精确版本应在正式实现开始时根据兼容性选定并锁定，不在文档阶段虚构版本。

## 目标系统

- `ml-api`：训练产物加载、单条/批量房价预测、模型信息和健康检查。
- `estimator-api`：App 1 的 Python 业务后端，校验请求并调用 `ml-api`。
- `market-api`：App 2 的 Java 业务后端，完成数据聚合、筛选、缓存和 what-if 调用。
- `web`：统一 Next.js Portal，提供估价和市场分析两个应用。

## 仓库结构

```text
.
├─ apps/web/                  # Next.js Portal，当前为空
├─ services/
│  ├─ ml-api/                 # FastAPI 模型服务，当前为空
│  ├─ estimator-api/          # Python 估价业务服务，当前为空
│  └─ market-api/             # Spring Boot 市场服务，当前为空
├─ packages/api-contracts/    # 共享/生成的 API 类型，当前为空
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

正式开发前应先完成 [ADR 决策清单](docs/adr/README.md) 中标记为“实现前确认”的事项。默认实现顺序为模型与契约、ML API、两个业务后端、Next.js Portal、容器集成、浏览器验收。

