# ADR-001：服务边界

- 状态：Accepted
- 日期：2026-08-14

## 背景

原题既要求独立 Task 1 模型容器，又要求 App 1 使用 Python 后端集成模型容器，App 2 使用 Java 后端集成同一模型。

## 决策

运行四个服务：Next.js `web`、FastAPI `ml-api`、FastAPI `estimator-api`、Spring Boot `market-api`。模型推理只存在于 `ml-api`。

## 理由

- 最直接对应题目措辞。
- 明确展示跨服务 API 设计和错误处理。
- 避免 Python/Java 复制模型。

## 后果

- Compose 和健康检查更复杂。
- Estimator API 很薄，但它仍体现业务边界和下游故障映射。
- 必须用契约测试防止三个后端 schema 漂移。

## 未选方案

将 Estimator 与 ML 合并：更简单，但可能被认为没有完成“集成模型容器”的独立后端要求。

