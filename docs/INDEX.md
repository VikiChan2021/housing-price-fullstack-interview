# 文档索引

## 项目状态与来源

- [项目状态](PROJECT_STATUS.md)：区分已准备、待实现和待验证内容。
- [原始资料清单](../references/README.md)：来源、大小和 SHA-256。

## 需求

- [项目要求](requirements/PROJECT_REQUIREMENTS.md)
- [范围与非目标](requirements/SCOPE_AND_NON_GOALS.md)
- [验收标准](requirements/ACCEPTANCE_CRITERIA.md)
- [需求追踪矩阵](requirements/TRACEABILITY_MATRIX.md)

## 架构与设计

- [系统架构](architecture/SYSTEM_ARCHITECTURE.md)
- [仓库结构](architecture/REPOSITORY_STRUCTURE.md)
- [数据与模型设计](architecture/DATA_AND_ML_DESIGN.md)
- [前端与 UX 规格](architecture/FRONTEND_UX_SPECIFICATION.md)
- [安全与可靠性](architecture/SECURITY_AND_RELIABILITY.md)

## API

- [API 契约](api/API_CONTRACTS.md)

## 开发

- [正式开发就绪审计](development/DEVELOPMENT_READINESS.md)
- [实施路线](development/IMPLEMENTATION_ROADMAP.md)
- [编码与协作规范](development/CODING_STANDARDS.md)

## 测试和验收

- [测试策略](testing/TEST_STRATEGY.md)

## 运行、部署与演示

- [本地运行与部署设计](operations/LOCAL_RUN_AND_DEPLOYMENT.md)
- [面试演示手册](operations/INTERVIEW_DEMO_RUNBOOK.md)

## 架构决策

- [ADR 索引](adr/README.md)

## 文档维护规则

- 新增功能必须关联至少一条需求和一条验收标准。
- 改动服务边界、数据持久化、模型选择或部署方式时新增 ADR。
- 每次里程碑完成后更新 `PROJECT_STATUS.md` 与追踪矩阵。
- 示例响应应与正式 OpenAPI 保持一致；实现后以生成的 OpenAPI 为机器可读真相。
