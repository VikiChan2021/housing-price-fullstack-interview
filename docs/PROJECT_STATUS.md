# 项目状态

最后更新：2026-08-14

## 已完成

- 创建独立 Git 仓库与 `main` 分支。
- 归档面试官原始 PDF、训练 CSV 和预测 CSV。
- 记录原始资料的 SHA-256。
- 创建应用、服务、测试、基础设施和文档目录骨架。
- 完成需求、架构、接口、测试、部署和演示文档的开发前审计。
- 接受 ADR-004，冻结核心工具链/直接依赖与 lockfile 策略。
- 固定 API 输入边界和可复现模型评估协议。
- 获得仓库所有者对 Phase 0B 和后续路线开发的明确批准。
- 完成 Phase 0B：Python/Node/Java 最小工程、精确 lockfile/Maven Wrapper 和三份 OpenAPI 3.1 基线。
- 在冻结的 Python 3.12.13、Node 24.18.0 和 Java 21 目标环境中通过最小 lint、类型检查、测试与构建；开发就绪 G6 为 PASS。

## 当前进行中

- Phase 3：Java/Spring Boot `market-api`。

## 尚未开始

- Next.js Portal。
- Market/Web Dockerfile 与 Docker Compose。
- 业务自动化测试、浏览器验收和公网部署。

## 已有探索证据，不等于最终模型结果

对原始 50 条训练数据做过只读探索：数据无缺失、无重复；特征高度相关；普通线性回归可以获得较高的交叉验证 R²。正式项目必须通过仓库内可复现训练脚本重新计算并持久化指标，不能直接复制探索数字作为最终结果。

## Phase 1 已验证结果

- 模型版本：`ridge-v1-0e36c622-a05bac12`；训练数据 SHA-256 与原始资料清单一致。
- Nested 5-fold CV：R² `0.984720 ± 0.004843`，MAE `7378.35 ± 1481.66`，RMSE `9311.09 ± 2144.91`；数值来自训练脚本及 `models/metadata.json`。
- 14 项 ML 测试通过，覆盖率 87.78%；冻结镜像构建、健康检查、真实 HTTP 与 Chromium Swagger “Try it out” 通过。
- 此处只声明本地与容器验证；公网部署仍未验证。

## Phase 2 已验证结果

- Estimator API 通过 13 项测试，覆盖率 91.36%，并通过 Ruff、严格 mypy 和生成 OpenAPI 校验。
- Estimator 容器通过 HTTP 调用真实 ML 容器，单条价格与模型版本完全一致；批量顺序保持不变。
- 断开 ML 网络时返回稳定 `504 UPSTREAM_TIMEOUT`，MockTransport 另覆盖连接不可用 503、下游 4xx/5xx 到 502 和畸形响应。
- Estimator 镜像确认不含 sklearn 或模型文件；浏览器历史仍按 ADR-003 留给 Web 本地存储。

## 下一步

进入实施路线 Phase 3：实现 Java 数据集加载、筛选/聚合/导出/Caffeine 缓存、ML HTTP what-if、Dockerfile 和相应测试。
