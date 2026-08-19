# Web Portal

Next.js App Router Portal，提供 Property Estimator 与 Market Analysis 两个真实后端驱动的应用。

## 组件边界

- Server Component：`app/market/page.tsx` 在服务端并行读取 Market summary 和 properties，避免把内网服务地址暴露给浏览器。
- Client Component：Estimator 表单、本地历史/比较，以及 Market 筛选、排序、分页、what-if 交互。
- 共享布局中的 `MarketStateProvider` 缓存 Market 页面状态；在两个应用间切换时保留筛选条件、结果、排序和 what-if 输入，刷新页面时仍以服务端最新数据为准。
- 同源 BFF：`app/api/estimates` 与 `app/api/market/[...path]` 代理业务后端，传播请求 ID、下载响应头和稳定错误。
- `app/api/ready` 同时检查 Estimator 与 Market readiness；任一依赖未就绪时返回 503。
- Estimator 历史使用版本化 localStorage；Market 路由缓存仅保存在当前标签页内存中。

浏览器不会直接访问 ML API，也不持有内部服务地址或密钥。

## 环境变量

| 变量 | 默认值 | 用途 |
|---|---|---|
| `ESTIMATOR_API_BASE_URL` | `http://127.0.0.1:8001` | Web server 到 Estimator |
| `MARKET_API_BASE_URL` | `http://127.0.0.1:8080` | Web server/RSC 到 Market |
| `WEB_API_TIMEOUT_SECONDS` | `10` | 服务端代理和 RSC 请求超时 |

Compose 会覆盖为服务内网名称。所有变量仅在服务端读取。

## 本地质量门

在 Node 24.18.0 与 pnpm 11.15.1 下：

```powershell
pnpm install --frozen-lockfile
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

standalone 镜像从仓库根目录构建：

```powershell
docker build -f apps/web/Dockerfile -t housing-price-web:local .
```

最近一次本地验收：严格 TypeScript 和 11 项 Vitest 测试通过；真实浏览器和生产构建的最新结论以仓库根 README 的开发状态为准。市场页测试覆盖搜索/排序、路由往返状态保留、what-if，以及带浏览器时区的 CSV/PDF 导出链接；估价页测试覆盖字段化范围提示、稳定历史序号和图表/表格同序展示。

## 可访问性与响应式

- 跳过导航链接、语义化区域、显式 label、表格 caption、aria-live/alert。
- 估价主流程已用键盘完成。
- 宽表格在自身容器内滚动；页面在 360px 视口无横向溢出。
- loading/error 边界提供可读状态和重试操作。

浏览器截图、下载文件和 CLI 会话只属于本地验收，保存在已被 Git 忽略的 `output/playwright/` 或 `.playwright-cli/`。
