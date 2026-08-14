# Estimator API

计划组件：Python 3.12+、FastAPI。

职责：

- App 1 业务入口。
- 服务端输入校验。
- 调用 `ml-api` 并转换错误。
- 单条和批量估价响应。

不得依赖 sklearn、读取模型文件或保存浏览器历史。Phase 2 已实现独立校验、单条/批量估价、ML HTTP 客户端、下游错误映射、健康/readiness 和 Dockerfile；本地与双容器集成已验证，UI 尚未实现。
