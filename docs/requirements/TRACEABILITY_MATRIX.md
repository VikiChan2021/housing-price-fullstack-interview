# 需求追踪矩阵

Phase 0B 工程基线、Phase 1~4 应用验收和 Phase 5 Compose/系统 E2E 已运行；最终 GitHub 干净克隆与公网证据仍未运行。

工程基线证据：两个 Python 服务的 health/ready 测试、Web 首页测试和 Java health/ready MVC 测试均已通过；三份 OpenAPI 3.1 基线已通过 lint，冻结目标环境构建结果记录在 `docs/development/DEVELOPMENT_READINESS.md`。这些证据不替代下表对应的业务、容器或浏览器验收。

| 需求 | 责任组件 | 主要验收 | 证据/计划 |
|---|---|---|---|
| SYS-001~003 | `apps/web`、三个服务 | AC-401、AC-503 | PASS：Compose 四服务 + Chrome Estimator/Market E2E + 服务调用日志 |
| ML-001 | `services/ml-api` | AC-101、AC-102 | PASS：`test_data.py`、`test_training.py`、`models/metadata.json` |
| ML-002 | `services/ml-api` | AC-103~105 | PASS：`test_api.py` 单条/批量/边界/错误测试 |
| ML-003 | `services/ml-api` | AC-106 | PASS：`test_model_info_health_and_openapi_examples` + 容器 HTTP |
| ML-004 | `services/ml-api` | AC-107 | PASS：缺失/损坏模型测试 + Docker healthcheck |
| ML-005~006 | `services/ml-api`、Docker | AC-002、AC-108 | PASS：ML Docker/真实 Swagger + 全栈 Compose |
| EST-001~003 | `apps/web`、`estimator-api` | AC-201~203 | PASS：`estimator.test.tsx` + Compose Chrome E2E |
| EST-004~005 | `apps/web` | AC-204~205 | PASS：localStorage 刷新/比较 Chrome E2E |
| EST-006~007 | `estimator-api` | AC-206 | PASS：13 项测试、真实 ML HTTP、Compose 断网 UI 错误与恢复 |
| MKT-001~005 | `apps/web` | AC-301~305 | PASS：`market.test.tsx` + Compose Chrome + CSV/PDF 下载/内容检查 |
| MKT-006~010 | `market-api` | AC-306~307 | PASS：14 项 Java 测试、真实 ML HTTP、缓存、断网降级/恢复与 Portal 呈现 |
| WEB-001~004 | `apps/web` | AC-301、AC-402~403 | PASS：App Router/RSC、真实 error 边界、Web README |
| WEB-005~009 | `apps/web` | AC-401~406 | PASS：Playwright Chrome、键盘、360/1280、console/network；axe 未单独运行 |
| DEL-001 | 根仓库 | AC-001、AC-504 | README PASS；最终 GitHub 干净克隆 NOT RUN |
| DEL-002 | `ml-api` | AC-002 | PASS：Dockerfile + Compose 构建日志 |
| DEL-003 | `ml-api` | AC-108、AC-505 | Swagger PASS；完整计时演示 NOT RUN |
| DEL-004 | 全系统 | AC-503、AC-505 | Compose E2E/本地截图 PASS；完整计时演示 NOT RUN |

## 更新规则

- 新增实现任务时必须引用需求 ID。
- 新增测试时必须引用验收 ID。
- 若需求变更，先改要求与 ADR，再改代码。
- 不能用单元测试替代浏览器或容器级验收。
