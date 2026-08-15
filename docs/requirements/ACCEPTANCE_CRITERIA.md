# 验收标准

每项验收在实现后记录为 `PASS`、`FAIL` 或 `NOT RUN`，并附命令、截图或测试报告。当前 Phase 1~5 对应的本地、容器、腾讯云公网与浏览器验收均已执行；最终 GitHub 干净克隆仍为 `NOT RUN`。

## A. 仓库与启动

- AC-001（NOT RUN）：最终变更提交后的 GitHub 干净克隆尚未验证。
- AC-002（PASS，本地）：根目录 `docker compose up --build -d --wait` 可以构建并启动全部服务。
- AC-003（PASS，本地）：四个容器具有可观察的 healthy 状态，不需要手工进入 IDE 启动。
- AC-004（PASS，本地检查）：仓库中没有真实密钥、机器专属绝对路径或未说明的私有依赖；本地证据目录已忽略。

## B. 模型与 ML API

- AC-101（PASS，本地）：训练脚本读取原始 CSV 时正确处理 BOM，并明确排除 `id`。
- AC-102（PASS，本地+容器）：同一数据和随机种子可重现模型、指标和预测。
- AC-103（PASS，本地+容器）：单条有效请求返回一个有限、正数的预测价格和模型版本。
- AC-104（PASS，本地+容器）：批量有效请求按输入顺序返回相同数量的预测。
- AC-105（PASS，本地）：缺失字段、非数字、越界值和空批次返回 4xx 及字段级错误。
- AC-106（PASS，本地+容器）：`/model-info` 返回特征顺序、系数、截距、训练行数、模型版本、R²、MAE、RMSE 和评估协议。
- AC-107（PASS，本地+容器）：`/health` 在模型加载成功后返回健康；模型缺失或损坏时不得假装健康。
- AC-108（PASS，真实 Chromium）：Swagger 中包含单条、批量、成功和失败示例。

Phase 1 证据：`services/ml-api/tests/` 共 14 项测试通过，覆盖率 87.78%；Ruff、严格 mypy、OpenAPI validator 与 Redocly recommended-strict 通过；冻结镜像构建成功并达到 Docker `healthy`；Swagger “Try it out” 的真实 POST 返回 200，浏览器控制台 0 错误/0 警告。公网验证仍为 `NOT RUN`。

## C. Estimator App

- AC-201（PASS，组件+浏览器）：页面包含 7 个字段，标签、单位和合理输入范围清晰。
- AC-202（PASS，组件+浏览器）：客户端校验不发送明显非法请求；服务端仍独立校验。
- AC-203（PASS，组件+浏览器）：成功预测同时出现在表格和图表中。
- AC-204（PASS，浏览器）：历史在页面刷新后仍保留，可清空。
- AC-205（PASS，浏览器）：可选择至少两条历史记录并排比较输入与预测。
- AC-206（PASS，Compose 浏览器）：停止 ML 后显示带请求 ID 的可重试错误，不白屏；恢复后重试成功。

## D. Market Analysis App

- AC-301（PASS，Compose 浏览器）：初始市场摘要由动态 Server Component 并行获取真实 Market 数据。
- AC-302（PASS，组件+浏览器）：筛选条件同步更新统计卡、图表和表格，空结果有明确提示。
- AC-303（PASS，浏览器）：表格支持价格排序和价格、卧室、面积组合筛选。
- AC-304（PASS，Compose 浏览器）：what-if 通过 Market → ML 真实调用链显示基准、场景和差异。
- AC-305（PASS，后端+Compose 浏览器）：CSV/PDF 内容已读取/渲染检查，Portal 当前筛选下载交互返回 200 并产生真实文件。
- AC-306（PASS，本地/容器）：重复统计请求从 `cache.hit=false` 变为 `true`；不同规范化筛选键结果隔离。
- AC-307（PASS，本地/容器）：下游 HTTP 错误映射为 502、读超时映射为 504；真实断网返回 503 与请求标识，重连后恢复健康。

Phase 3 证据：`services/market-api/src/test/` 共 14 项 Java 21 测试通过；真实 Java 与 Python 容器完成 what-if；源数据 50 行统计对账；CSV/PDF 真实 HTTP 导出、PDF PNG 渲染、ML 断网降级和恢复均通过。公网验证仍为 `NOT RUN`。

## E. Portal 与 UX

- AC-401（PASS，浏览器）：共享导航可在两个应用间切换，当前页面状态明显。
- AC-402（PASS，浏览器）：App Router 动态页面、loading 导航状态和 Market 后端停止后的 `error.tsx` 均被真实触发。
- AC-403（PASS，代码+文档）：Server/Client Component 边界已在代码和 `apps/web/README.md` 说明。
- AC-404（PASS，浏览器）：Estimator 主流程只用键盘完成；输入有 label，错误使用 alert/关联语义。
- AC-405（PASS，浏览器）：1280x800 与 360x800 无页面横向溢出或关键内容截断。
- AC-406（PASS，浏览器）：正常主流程 console 0 错误/0 警告，关键 API 均 200；仅故障注入出现预期 503/504。

## F. 质量、文档和演示

- AC-501（PASS，本地/目标工具链）：14 项 ML、13 项 Estimator、14 项 Market、7 项 Web 测试通过。
- AC-502（PASS，本地/容器）：服务间固定 fixtures、真实 HTTP、请求 ID、超时和失败映射均通过。
- AC-503（PASS，Compose+公网浏览器）：四服务真实估价、RSC、what-if、下载、故障和恢复通过；公网同路径流程再次通过。
- AC-504（PASS，文档检查）：README 包含架构、启动、测试、API、模型限制和排错信息。
- AC-505（NOT RUN）：8 至 12 分钟完整计时彩排尚未执行；失败场景已验证并写入手册。
- AC-506（PASS，文档检查）：项目状态明确区分本地验证、公网验证和 GitHub 干净克隆未验证。

## 完成门槛

- 所有原题对应的验收项必须 `PASS`。
- 可选公网部署已执行；最终 GitHub 干净克隆仍必须在提交后单独验证。
- 任何关键流程只有在真实服务和真实浏览器中通过，才能算完成。
