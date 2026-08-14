# Architecture Decision Records

ADR 记录会影响多个组件或长期维护的决策。Accepted ADR 是后续实现默认约束；改变时新增 superseding ADR，不直接抹掉历史。

| ADR | 状态 | 决策 |
|---|---|---|
| [ADR-001](ADR-001-service-boundaries.md) | Accepted | 四个运行服务，模型推理集中在 ML API |
| [ADR-002](ADR-002-ridge-model.md) | Accepted | LinearRegression baseline，StandardScaler + Ridge 为首选 |
| [ADR-003](ADR-003-lightweight-state.md) | Accepted | 浏览器历史 + Caffeine，不引入数据库/Redis |
| [ADR-004](ADR-004-version-pinning.md) | Accepted | 固定工具链、直接依赖与 lockfile 策略 |

## 模板

每个 ADR 包含：状态、日期、背景、决策、理由、后果和替代方案。
