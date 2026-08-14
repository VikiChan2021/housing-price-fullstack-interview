# ADR-004：未固定依赖的版本锁定

- 状态：Proposed
- 日期：2026-08-14

## 背景

原题固定了 Python 3.12+、Java 21、Spring Boot 3.4.4，但没有固定 Next.js、Node.js、Tailwind、FastAPI 和 scikit-learn 的精确版本。版本会随时间变化。

## 建议决策

在 Phase 0 查询官方兼容性后选择稳定版本，并通过 lockfile、容器基础镜像和模型元数据锁定。不要在文档阶段凭记忆声明“最新版本”。

## 接受条件

- Next.js 与 Node.js 官方支持关系已核对。
- Python 3.12 与 FastAPI/scikit-learn 版本兼容。
- Spring Boot 固定 3.4.4，Java toolchain 固定 21。
- 所有组件能在 Docker 构建。

