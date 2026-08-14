# 范围与非目标

## V1 范围

- 使用提供的 50 条数据训练一个可解释的简单回归模型。
- 独立 FastAPI 模型服务及 Swagger。
- 独立 Python Estimator API。
- 独立 Spring Boot Market API。
- 一个 Next.js Portal，包含估价与市场分析两个应用。
- 单条/批量预测、模型信息、健康检查。
- 表单校验、结果图表、历史、比较。
- 市场统计、筛选、what-if、CSV/PDF 导出、响应式表格。
- Caffeine 缓存。
- Docker Compose 本地集成。
- 单元、契约、集成和浏览器端到端测试。
- GitHub 仓库、运行文档和面试演示手册。

## 明确不做

- 不采集真实房产数据，不连接外部 MLS 或商业数据源。
- 不提供真实估价或投资建议。
- 不实现登录、权限、多租户、支付或审计平台。
- 不引入 PostgreSQL、Redis、Kafka、Kubernetes 等非必要基础设施。
- 不构建在线训练、自动重训练、特征仓库或复杂 MLOps 平台。
- 不承诺高并发和生产 SLA。
- 不把公网部署作为本地交付完成的替代品。
- 不为了“微服务数量”重复模型逻辑。

## 可选加分项

- GitHub Actions 验证后端、前端和 Docker 构建。
- 公网只读演示环境。
- 从 OpenAPI 自动生成 TypeScript 客户端。
- 请求关联 ID、指标端点和简单可观测性面板。
- Lighthouse、axe 和 Playwright 自动化可访问性检查。

可选项只有在 V1 验收全部通过后才能开始。

