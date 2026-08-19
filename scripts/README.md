# Scripts

本目录放置跨组件、可重复执行的辅助任务，例如：

- 源数据校验。
- OpenAPI 契约同步检查。
- Compose smoke test。
- 面试前环境预检。
- 本地四服务的一键启动与停止。

当前 PowerShell 入口：

- `start-local.ps1`：不使用 Docker，按依赖顺序启动四个服务并打开浏览器。
- `stop-local.ps1`：只停止由 `start-local.ps1` 记录的本地开发进程。
- `status-local.ps1`：检查四个本地端点。
- `start-docker.ps1`：构建并启动完整 Compose，等待健康后打开浏览器。

详细说明见 `docs/operations/LOCAL_DEBUGGING_GUIDE.md`。
