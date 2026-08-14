# 仓库结构设计

以下是目标结构。当前仅创建一级骨架，具体文件由实施阶段按路线生成。

```text
.
├─ apps/
│  └─ web/
│     ├─ app/
│     │  ├─ estimator/
│     │  ├─ market/
│     │  ├─ api/                 # 可选 BFF Route Handlers
│     │  ├─ layout.tsx
│     │  ├─ loading.tsx
│     │  └─ error.tsx
│     ├─ components/
│     ├─ hooks/
│     ├─ lib/
│     ├─ types/
│     └─ tests/
├─ services/
│  ├─ ml-api/
│  │  ├─ app/
│  │  │  ├─ api/
│  │  │  ├─ core/
│  │  │  ├─ ml/
│  │  │  ├─ schemas/
│  │  │  └─ main.py
│  │  └─ tests/
│  ├─ estimator-api/
│  │  ├─ app/
│  │  │  ├─ api/
│  │  │  ├─ clients/
│  │  │  ├─ schemas/
│  │  │  └─ main.py
│  │  └─ tests/
│  └─ market-api/
│     └─ src/
│        ├─ main/java/.../
│        │  ├─ config/
│        │  ├─ controller/
│        │  ├─ client/
│        │  ├─ domain/
│        │  ├─ dto/
│        │  ├─ exception/
│        │  └─ service/
│        └─ test/java/.../
├─ packages/
│  └─ api-contracts/             # OpenAPI 快照/生成类型
├─ data/
│  ├─ raw/                       # 不修改
│  └─ processed/                 # 运行时生成，gitignore
├─ models/                       # 模型二进制 gitignore；元数据可提交
├─ infra/
│  └─ docker/
├─ scripts/                      # 跨平台验证/演示辅助脚本
├─ tests/
│  └─ e2e/
├─ docs/
└─ references/original/
```

## 组织原则

- 每个后端独立管理自己的依赖、测试和 Dockerfile。
- 不创建共享 Python/Java 业务包；共享的是 HTTP 契约，不是运行时内部对象。
- TypeScript 类型优先由 OpenAPI 生成，避免手写漂移。
- 原始数据只有一个仓库副本；服务通过构建上下文或只读挂载使用。
- 根目录只保留跨组件配置、文档和 Compose，不堆放业务源码。

## 未来应生成但当前没有的文件

- 精确依赖清单：`pyproject.toml`、`package.json`、Gradle/Maven 配置。
- 每个服务的 Dockerfile。
- 根目录 `compose.yaml`。
- OpenAPI 快照和生成的 TypeScript 类型。
- 模型元数据 JSON。
- CI 工作流。

这些文件应由对应实施阶段创建，并在创建时锁定版本。

