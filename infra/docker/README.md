# Docker Infrastructure

实现阶段在此维护共享 Docker 约定或辅助配置。每个应用的 Dockerfile 留在各自组件目录，根目录 `compose.yaml` 负责整合。

目标服务：`web`、`ml-api`、`estimator-api`、`market-api`。

已实现：

- 根目录 `compose.yaml`：四服务构建、端口、环境变量和健康依赖。
- 各组件目录 Dockerfile：冻结基础镜像，模型构建时训练，Web standalone 运行。
- 根 `.dockerignore`：排除 Git、IDE、依赖、构建产物、本地浏览器证据和日志。

运行入口和 smoke 命令见 `docs/operations/LOCAL_RUN_AND_DEPLOYMENT.md`。
