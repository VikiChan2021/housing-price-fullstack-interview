# 需求追踪矩阵

Phase 0B 的工程基线测试已运行；下表的业务验收证据仍为计划状态，实现时将测试文件或测试用例 ID 填入“证据”列。

工程基线证据：两个 Python 服务的 health/ready 测试、Web 首页测试和 Java health/ready MVC 测试均已通过；三份 OpenAPI 3.1 基线已通过 lint，冻结目标环境构建结果记录在 `docs/development/DEVELOPMENT_READINESS.md`。这些证据不替代下表对应的业务、容器或浏览器验收。

| 需求 | 责任组件 | 主要验收 | 计划证据 |
|---|---|---|---|
| SYS-001~003 | `apps/web`、三个服务 | AC-401、AC-503 | Portal E2E + 服务调用日志 |
| ML-001 | `services/ml-api` | AC-101、AC-102 | PASS：`test_data.py`、`test_training.py`、`models/metadata.json` |
| ML-002 | `services/ml-api` | AC-103~105 | PASS：`test_api.py` 单条/批量/边界/错误测试 |
| ML-003 | `services/ml-api` | AC-106 | PASS：`test_model_info_health_and_openapi_examples` + 容器 HTTP |
| ML-004 | `services/ml-api` | AC-107 | PASS：缺失/损坏模型测试 + Docker healthcheck |
| ML-005~006 | `services/ml-api`、Docker | AC-002、AC-108 | 部分：ML Docker/真实 Swagger PASS；全栈 Compose AC-002 NOT RUN |
| EST-001~003 | `apps/web`、`estimator-api` | AC-201~203 | 组件测试 + Estimator E2E |
| EST-004~005 | `apps/web` | AC-204~205 | localStorage/比较 E2E |
| EST-006~007 | `estimator-api` | AC-206 | 后端 PASS：13 项测试、真实 ML HTTP 集成、断网故障注入；UI 部分 NOT RUN |
| MKT-001~005 | `apps/web` | AC-301~305 | Market E2E + 导出文件检查 |
| MKT-006~010 | `market-api` | AC-306~307 | Spring 集成测试 + 缓存指标/日志 |
| WEB-001~004 | `apps/web` | AC-301、AC-402~403 | 路由/渲染测试 + 架构说明 |
| WEB-005~009 | `apps/web` | AC-401~406 | Playwright + axe + 截图 |
| DEL-001 | 根仓库 | AC-001、AC-504 | GitHub 链接 + 克隆验证 |
| DEL-002 | `ml-api` | AC-002 | Dockerfile 构建日志 |
| DEL-003 | `ml-api` | AC-108、AC-505 | Swagger 演示 |
| DEL-004 | 全系统 | AC-503、AC-505 | Compose E2E + 演示录像/截图 |

## 更新规则

- 新增实现任务时必须引用需求 ID。
- 新增测试时必须引用验收 ID。
- 若需求变更，先改要求与 ADR，再改代码。
- 不能用单元测试替代浏览器或容器级验收。
