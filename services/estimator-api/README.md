# Estimator API

计划组件：Python 3.12+、FastAPI。

职责：

- App 1 业务入口。
- 服务端输入校验。
- 调用 `ml-api` 并转换错误。
- 单条和批量估价响应。

不得依赖 sklearn、读取模型文件或保存浏览器历史。当前目录没有应用代码。

