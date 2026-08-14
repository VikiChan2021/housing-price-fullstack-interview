# 编码与协作规范

## 通用

- 优先可读、可演示的简单实现，不引入与题目无关的框架。
- 配置通过环境变量注入；提供安全默认值和 `.env.example`。
- API、日志、测试和文档使用相同字段名称。
- 禁止把 TODO、mock 响应或占位指标包装成最终功能。
- 错误不能只打印后吞掉；映射为稳定响应并保留可排查日志。

## Python

- Python 3.12+，使用类型标注。
- Pydantic schema 与业务/模型逻辑分离。
- sklearn Pipeline 作为完整推理产物，避免预处理漂移。
- 用明确模块管理 settings、logging、clients 和 exceptions。
- 测试覆盖数据契约、模型、API 和下游失败。

## Java

- Java 21、Spring Boot 3.4.4。
- Controller 只做协议转换，聚合和缓存逻辑放 Service。
- ML HTTP 调用封装在 client 层。
- DTO 与内部 domain 分离；Bean Validation 提供字段错误。
- 统计函数应纯净可测，避免在 Controller 中循环计算。

## TypeScript / Next.js

- TypeScript strict 模式。
- 默认 Server Component；只有交互、浏览器 API 或客户端状态需要时使用 Client Component。
- API 调用集中在 `lib/` 或生成客户端，不散落在组件。
- 自定义 Hooks 只承载复用行为，不隐藏服务端可完成的数据加载。
- 表单和图表组件保持可测试；货币格式化集中处理。

## 测试命名

- 测试名称说明行为和条件，例如 `returns_422_when_school_rating_exceeds_10`。
- 每个 E2E 用例引用验收 ID。
- 固定随机种子，避免依赖测试执行顺序。

## 文档和状态

- 改变 API：更新 API 契约、OpenAPI 快照、客户端类型和契约测试。
- 改变架构：新增或替代 ADR。
- 完成阶段：更新项目状态、验收清单和追踪矩阵。
- 本地通过不能写成公网或生产验证通过。

## Git

- 小而有意图的提交，不提交密钥、构建产物、模型二进制或本机 IDE 状态。
- 不覆盖原始数据。
- PR/提交信息说明已运行和未运行的验证。

