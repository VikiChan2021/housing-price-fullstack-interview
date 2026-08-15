# Housing Price Fullstack Interview Project

这是一个文档先行的面试项目仓库。目标是交付一套可现场演示的房价预测全栈系统：模型服务使用 FastAPI，房产估价应用使用 Python 后端，市场分析应用使用 Java/Spring Boot 后端，统一门户使用 Next.js。

## 当前状态

| 层级 | 状态 |
|---|---|
| 原始题目与数据归档 | 已完成并校验 |
| 需求、架构、接口、测试和实施文档 | 已完成开发前审计并获批准 |
| 工程基线 | Phase 0B 已验证通过 |
| 应用代码 | Phase 1~4 已完成本地验收 |
| Docker/本地运行 | 四服务 Compose 已实现并通过健康等待、关闭和重启验证 |
| 浏览器端到端验收 | Estimator、Market、导出、故障与恢复已在真实 Chromium 验证 |
| 公网部署 | 腾讯云已部署并通过真实 Chrome 验收：[kandian.site/housing](https://kandian.site/housing) |

本地与腾讯云公网验证均已执行；最终 GitHub 干净克隆仍未执行。

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
├─ apps/web/                  # Next.js Portal 与 standalone Dockerfile
├─ services/
│  ├─ ml-api/                 # FastAPI 模型服务，Phase 1 已完成
│  ├─ estimator-api/          # Python 估价业务服务，Phase 2 已完成
│  └─ market-api/             # Spring Boot 市场服务，Phase 3 已完成
├─ packages/api-contracts/    # OpenAPI 3.1 与共享 schema 基线
├─ data/raw/                  # 原始 CSV，只读
├─ models/                    # 后续生成的模型产物，不提交大文件
├─ infra/docker/              # Docker 约定
├─ output/playwright/         # 本地浏览器证据，已被 Git 忽略
├─ docs/                      # 项目事实与设计的主要入口
└─ references/original/       # 面试官原始题目，只读
```

## 原始资料

- [原始题目 PDF](references/original/Interview%20Tasks%20Fullstack.pdf)
- [训练数据](data/raw/House%20Price%20Dataset.csv)
- [待预测数据](data/raw/Test%20Data%20For%20Prediction.csv)
- [资料清单与 SHA-256](references/README.md)

## 开发启动条件

文档决策和 Phase 0B 工程基线均已完成，G0~G6 为 PASS；运行证据见 [正式开发就绪审计](docs/development/DEVELOPMENT_READINESS.md)。Phase 1~5 已完成本地、容器与真实浏览器验收，当前进入 Phase 6 交付整理。

默认顺序为模型与 ML API、Estimator API、Market API、Next.js Portal、Compose 集成、真实浏览器验收。

## 一键本地运行

前置条件仅为 Git、Docker Desktop（含 Compose v2）以及可用端口 3000、8000、8001、8080：

```powershell
docker compose config
docker compose up --build -d --wait
docker compose ps
```

入口：

- Portal：`http://localhost:3000`
- ML Swagger：`http://localhost:8000/docs`
- ML API：`http://localhost:8000`
- Estimator API：`http://localhost:8001`
- Market API：`http://localhost:8080`

停止并移除本项目容器及网络：

```powershell
docker compose down
```

## 质量检查

各组件使用冻结 lockfile/Maven Wrapper；完整策略见[测试策略](docs/testing/TEST_STRATEGY.md)。最短 Compose smoke 为：

```powershell
docker compose up -d --wait
Invoke-RestMethod http://localhost:3000/api/ready
Invoke-RestMethod http://localhost:8080/api/v1/market/summary
```

最近一次本地验收通过 14 项 ML 测试、13 项 Estimator 测试、14 项 Market 测试和 7 项 Web 测试，并完成四服务真实浏览器 E2E。腾讯云公网已验证 Estimator、Market RSC、what-if、CSV/PDF、桌面/移动布局和旧站回归；最终 GitHub 干净克隆仍标记为未验证。

## 公网地址

- 房价项目：<https://kandian.site/housing>
- 原“看点名著”：<https://kandian.site/zh-CN/>

公网使用同一域名证书。Nginx 仅将 `/housing` 子路径代理到独立 Compose Web 容器，原站根路径和 `/api/` 路由不变；生产拓扑与回滚说明见 [Tencent Cloud deployment](infra/tencent/README.md)。

## 模型与产品限制

- 模型只基于题目提供的 50 条演示数据，不是商业估价或金融建议。
- 特征存在较强相关性，样本量小，训练范围外预测可靠性更低。
- `id` 只用于标识，不参与训练；模型推理由 `ml-api` 单点负责。
- 历史只保存在当前浏览器 localStorage；Market 缓存是可丢失的进程内 Caffeine。

启动失败时按 ML → Estimator/Market → Web 的顺序检查 `docker compose ps` 和 `docker compose logs <service>`，并使用响应中的 `X-Request-ID` 关联排查。更详细步骤见[本地运行与部署](docs/operations/LOCAL_RUN_AND_DEPLOYMENT.md)。
