# Web Portal

Next.js App Router Portal，提供 Property Estimator 与 Market Analysis 两个真实后端驱动的应用。

## 组件边界

- Server Component：`app/market/page.tsx` 在服务端并行读取 Market summary、properties 和 segments，避免把内网服务地址暴露给浏览器。
- Client Component：Estimator 表单、本地历史/比较，以及 Market 筛选、排序、分页、what-if 交互。
- 同源 BFF：`app/api/estimates` 与 `app/api/market/[...path]` 代理业务后端，传播请求 ID、下载响应头和稳定错误。
- `app/api/ready` 同时检查 Estimator 与 Market readiness；任一依赖未就绪时返回 503。
- 历史数据使用版本化 localStorage，仅保存在当前浏览器。

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

最近一次本地验收：ESLint、严格 TypeScript、生产构建和 7 项 Vitest 测试通过；真实 Chromium 在 1280x800 与 360x800 下完成估价、刷新历史、比较、市场筛选/排序、what-if、CSV/PDF 下载、错误边界和重试恢复。故障注入产生的预期 503/504 不计为意外网络错误。

## 可访问性与响应式

- 跳过导航链接、语义化区域、显式 label、表格 caption、aria-live/alert。
- 估价主流程已用键盘完成。
- 宽表格在自身容器内滚动；页面在 360px 视口无横向溢出。
- loading/error 边界提供可读状态和重试操作。

浏览器截图、下载文件和 CLI 会话只属于本地验收，保存在已被 Git 忽略的 `output/playwright/` 或 `.playwright-cli/`。
