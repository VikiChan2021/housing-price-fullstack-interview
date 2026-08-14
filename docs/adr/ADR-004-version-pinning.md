# ADR-004：工具链与依赖版本锁定

- 状态：Accepted
- 日期：2026-08-14

## 背景

原题固定了 Python 3.12+、Java 21、Spring Boot 3.4.4，但没有固定 Next.js、Node.js、Tailwind、FastAPI 和 scikit-learn 的精确版本。版本会随时间变化。

## 决策

采用以下直接基线：

| 区域 | 固定版本/策略 |
|---|---|
| Python | Python 3.12.13；uv 0.11.32；两个 Python 服务分别使用 `pyproject.toml` 与受版本控制的 `uv.lock` |
| Python 核心依赖 | FastAPI 0.139.2；scikit-learn 1.9.0 |
| Web 运行时 | Node.js 24.18.0 LTS；pnpm 11.15.1 |
| Web 核心依赖 | Next.js 16.2.12；React/React DOM 19.2.8；Tailwind CSS 4.3.3 |
| Java | Java 21；Spring Boot 3.4.4（原题固定，不自行升级） |
| Java 构建 | Maven Wrapper 3.9.16 |

直接依赖在 manifest 中使用精确版本，传递依赖由 `uv.lock`、`pnpm-lock.yaml` 和 Maven dependency management 固定。Docker 基础镜像在首次成功构建后记录 tag 和不可变 digest。

测试库、图表库、HTTP 客户端、OpenAPI 生成器和 PDF 库在 Phase 0B 按最小依赖原则选择并锁定。它们不得改变已接受的服务边界或 API 语义。

版本信息是 2026-08-14 的兼容性快照，不代表永久追随最新版本。升级必须单独变更并重新执行构建、契约和浏览器验收。

## 理由

- Next.js 16 官方最低要求为 Node.js 20.9；Node 24 当前处于 LTS，满足要求并避免使用已经 EOL 的 Node 20。
- Tailwind CSS 4 的官方 Next.js/PostCSS 方案与目标浏览器基线一致。
- FastAPI 0.139.2 支持 Python 3.10+，scikit-learn 1.9.0 提供 Python 3.12 wheel。
- Spring Boot 3.4 支持 Java 21 与 Maven 3.6.3+；Maven 3.9.16 满足要求，而 Spring Boot 3.4.4 必须服从原题固定版本。
- lockfile 比在文档中枚举所有传递依赖更可靠，也能在后续安装中保持可复现。

## 接受条件

- 官方支持关系已核对：已完成。
- 直接依赖与构建工具已确定：已完成。
- lockfile 已生成并通过冻结安装：批准后 Phase 0B 执行。
- 所有组件能在 Docker 构建：批准后 Phase 0B/对应实现阶段执行。

后两项是实现验证，不影响 ADR 的决策状态；若验证失败，必须更新或替代本 ADR。

## 官方依据

- <https://nextjs.org/docs/app/getting-started/installation>
- <https://nodejs.org/en/about/previous-releases>
- <https://tailwindcss.com/docs/installation/framework-guides/nextjs>
- <https://fastapi.tiangolo.com/tutorial/>
- <https://docs.astral.sh/uv/getting-started/installation/>
- <https://scikit-learn.org/stable/install.html>
- <https://docs.spring.io/spring-boot/3.4/system-requirements.html>
- <https://maven.apache.org/docs/history>

## 后果

- 核心版本升级必须显式修改 manifest/ADR 并重跑构建、契约、模型和浏览器验证。
- 开发机不必全局覆盖已有运行时，可以由 uv、Corepack/Maven Wrapper 或 Docker 提供冻结版本。
- Spring Boot 3.4.4 即使不是当前 3.4 维护线的最新补丁，也必须服从原题；若安全扫描发现不可接受问题，需要先向仓库所有者报告并新增 ADR。

## 未选方案

- 开发时始终使用 `latest`：无法复现，且可能在面试前引入破坏性升级。
- 只固定主版本：不能阻止补丁/次版本造成 OpenAPI、构建或模型产物漂移。
- 将原题固定的 Spring Boot 3.4.4 自动升级到更新补丁：会静默改变最高优先级要求。
