# 验收标准

每项验收在实现后记录为 `PASS`、`FAIL` 或 `NOT RUN`，并附命令、截图或测试报告。当前 AC-101~108 已在 Phase 1 本地验收为 `PASS`；Market 后端对应的 AC-305~307 已完成本地验收，但 AC-301~304 及 AC-305 的 Portal 交互仍为 `NOT RUN`。

## A. 仓库与启动

- AC-001：从干净克隆开始，只依赖 README 记录的工具即可启动。
- AC-002：根目录一条 Compose 命令可以构建并启动全部服务。
- AC-003：所有容器具有可观察的健康状态，不需要手工进入 IDE 启动。
- AC-004：仓库中没有真实密钥、机器专属绝对路径或未说明的私有依赖。

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

- AC-201：页面包含 7 个字段，标签、单位和合理输入范围清晰。
- AC-202：客户端校验不发送明显非法请求；服务端仍独立校验。
- AC-203：成功预测同时出现在表格和图表中。
- AC-204：历史在页面刷新后仍保留，可清空。
- AC-205：可选择至少两条历史记录并排比较输入与预测。
- AC-206：模型服务超时或不可用时显示可重试错误，不白屏。

## D. Market Analysis App

- AC-301：初始市场摘要由 Server Component 或服务端数据加载路径获取。
- AC-302：筛选条件会更新统计卡、图表和表格，且空结果有明确提示。
- AC-303：表格支持至少一个数值列排序和多个条件筛选。
- AC-304：what-if 修改一个或多个特征后调用真实 ML API 并显示基准差异。
- AC-305（后端 PASS，本地；Portal 下载交互 NOT RUN）：CSV 导出包含当前全部筛选数据与 UTF-8 BOM；PDF 包含标题、筛选条件、匹配数和平均/中位/价格范围，并已提取文本和渲染检查。
- AC-306（PASS，本地/容器）：重复统计请求从 `cache.hit=false` 变为 `true`；不同规范化筛选键结果隔离。
- AC-307（PASS，本地/容器）：下游 HTTP 错误映射为 502、读超时映射为 504；真实断网返回 503 与请求标识，重连后恢复健康。

Phase 3 证据：`services/market-api/src/test/` 共 14 项 Java 21 测试通过；真实 Java 与 Python 容器完成 what-if；源数据 50 行统计对账；CSV/PDF 真实 HTTP 导出、PDF PNG 渲染、ML 断网降级和恢复均通过。公网验证仍为 `NOT RUN`。

## E. Portal 与 UX

- AC-401：共享导航可在 Estimator 与 Market Analysis 之间切换，当前页面状态明显。
- AC-402：App Router、`loading.tsx` 和 `error.tsx` 被真实触发并验证。
- AC-403：Server/Client Component 边界有代码和 README 说明。
- AC-404：主要流程只使用键盘可完成；输入有 label，错误有 `aria-describedby` 或等价语义。
- AC-405：桌面与移动视口没有横向溢出、遮挡、不可读图表或被截断关键内容。
- AC-406：浏览器控制台没有未处理异常，关键 API 请求没有意外 4xx/5xx。

## F. 质量、文档和演示

- AC-501：Python、Java、TypeScript 的单元测试通过。
- AC-502：服务间契约和集成测试通过。
- AC-503：Docker Compose 下的端到端浏览器测试通过。
- AC-504：README 包含架构、启动、测试、API、模型限制和排错信息。
- AC-505：面试演示可在 8 至 12 分钟内完成，并准备一个失败场景。
- AC-506：项目状态明确区分本地验证与公网未验证内容。

## 完成门槛

- 所有原题对应的验收项必须 `PASS`。
- 可选公网部署可以是 `NOT RUN`，但必须明确说明。
- 任何关键流程只有在真实服务和真实浏览器中通过，才能算完成。
