# ML API

计划组件：Python 3.12+、FastAPI、scikit-learn。

职责：

- 可复现训练与模型产物生成。
- 单条/批量预测。
- 模型系数、指标和限制信息。
- 健康与 readiness。

不得包含页面、用户历史或市场聚合。实现前阅读 `docs/architecture/DATA_AND_ML_DESIGN.md` 与 `docs/api/API_CONTRACTS.md`。

Phase 0B 已建立 FastAPI 最小工程、精确依赖锁和质量门。Phase 1 已实现可复现训练、产物加载、单条/批量预测、范围警告、模型信息和健康检查；容器与 Swagger 验收状态以 `docs/PROJECT_STATUS.md` 为准。

本机使用冻结工具链：

```powershell
uv sync --frozen
uv run python -m app.training
uv run ruff check .
uv run mypy
uv run pytest --cov=app --cov-report=term-missing
```

从仓库根目录构建（构建过程会从只读原始 CSV 重新训练，不提交二进制模型）：

```powershell
docker build -f services/ml-api/Dockerfile -t housing-price-ml-api:phase1 .
docker run --rm -p 8000:8000 housing-price-ml-api:phase1
```

Swagger UI：`http://localhost:8000/docs`。
