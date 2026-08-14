# API Contracts

Phase 0B 已建立三份设计基线：

- `openapi/ml-api.yaml`
- `openapi/estimator-api.yaml`
- `openapi/market-api.yaml`
- `schemas/common.yaml`：跨服务共享的协议 schema，不是运行时共享业务包。

当前 YAML 是实现前机器可校验的设计基线。各服务实现后，生成的 OpenAPI 是运行时事实；契约测试必须比较设计基线与生成结果，差异先更新文档或 ADR。

校验入口：

```powershell
Set-Location apps/web
corepack pnpm contract:lint
```

后续由 OpenAPI 生成 TypeScript 类型或客户端，禁止再手写一份会漂移的重复类型。
