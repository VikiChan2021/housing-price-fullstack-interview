# 项目状态

最后更新：2026-08-15

## 已完成

- 创建独立 Git 仓库与 `main` 分支。
- 归档面试官原始 PDF、训练 CSV 和预测 CSV。
- 记录原始资料的 SHA-256。
- 创建应用、服务、测试、基础设施和文档目录骨架。
- 完成需求、架构、接口、测试、部署和演示文档的开发前审计。
- 接受 ADR-004，冻结核心工具链/直接依赖与 lockfile 策略。
- 固定 API 输入边界和可复现模型评估协议。
- 获得仓库所有者对 Phase 0B 和后续路线开发的明确批准。
- 完成 Phase 0B：Python/Node/Java 最小工程、精确 lockfile/Maven Wrapper 和三份 OpenAPI 3.1 基线。
- 在冻结的 Python 3.12.13、Node 24.18.0 和 Java 21 目标环境中通过最小 lint、类型检查、测试与构建；开发就绪 G6 为 PASS。
- 完成 Phase 4 Portal：Estimator、Market、RSC 首屏、同源 BFF、本地历史/比较、what-if 与导出均已实现。
- 完成 Phase 5 Compose：四个镜像、健康依赖、一条命令启动、真实调用链、故障注入、关闭与重新启动均已本地验证。
- 完成腾讯云公网部署：`https://kandian.site/housing` 复用现有域名/证书，通过独立 Compose 与 Nginx 子路径隔离运行。

## 当前进行中

- Phase 6：交付文档、演示彩排与最终仓库验证。

## 尚未验证

- 最终变更提交后的 GitHub 干净克隆验证。
- 8~12 分钟人工计时演示彩排。

## 已有探索证据，不等于最终模型结果

对原始 50 条训练数据做过只读探索：数据无缺失、无重复；特征高度相关；普通线性回归可以获得较高的交叉验证 R²。正式项目必须通过仓库内可复现训练脚本重新计算并持久化指标，不能直接复制探索数字作为最终结果。

## Phase 1 已验证结果

- 模型版本：`ridge-v1-0e36c622-a05bac12`；训练数据 SHA-256 与原始资料清单一致。
- Nested 5-fold CV：R² `0.984720 ± 0.004843`，MAE `7378.35 ± 1481.66`，RMSE `9311.09 ± 2144.91`；数值来自训练脚本及 `models/metadata.json`。
- 14 项 ML 测试通过，覆盖率 87.78%；冻结镜像构建、健康检查、真实 HTTP 与 Chromium Swagger “Try it out” 通过。
- Phase 1 当时只声明本地与容器验证；当前模型推理已通过 Portal 公网真实调用链验证，ML API 本身按设计不直接暴露公网。

## Phase 2 已验证结果

- Estimator API 通过 13 项测试，覆盖率 91.36%，并通过 Ruff、严格 mypy 和生成 OpenAPI 校验。
- Estimator 容器通过 HTTP 调用真实 ML 容器，单条价格与模型版本完全一致；批量顺序保持不变。
- 断开 ML 网络时返回稳定 `504 UPSTREAM_TIMEOUT`，MockTransport 另覆盖连接不可用 503、下游 4xx/5xx 到 502 和畸形响应。
- Estimator 镜像确认不含 sklearn 或模型文件；浏览器历史仍按 ADR-003 留给 Web 本地存储。

## Phase 3 已验证结果

- Market API 通过 14 项 Java 21 测试；覆盖数据校验、聚合/筛选/分页/排序、Caffeine 缓存、snake_case ML 合约、HTTP 502/504 映射和 CSV/PDF 导出。
- 源 CSV 的 50 行统计已对账：平均价 `264600`、中位价 `245000`、最低价 `160000`、最高价 `410000`、平均面积 `1690.2`。
- 真实 Java 容器通过 HTTP 调用真实 ML 容器完成两条有序 what-if；重复摘要由 `cache.hit=false` 变为 `true`，不同筛选键未串数据。
- CSV 具备 UTF-8 BOM、固定表头和全部筛选行；最终 PDF 包含标题、筛选条件、匹配数、平均/中位/价格范围，并完成文本提取与 PNG 渲染检查。
- 断开 ML 网络后 `/health` 返回 degraded，`/ready` 与 what-if 返回稳定 503 和请求标识；客户端测试另覆盖下游 HTTP 到 502、读超时到 504。重连后恢复 healthy。
- 最终本地镜像：`sha256:47885a0370708c9b103bf08a5f9bd919c40c6bcb45851897df04e6ee7db3d5db`。Market 已通过 Portal 公网 RSC、what-if 和导出链路验证，服务端口按设计仅绑定回环地址。

## Phase 4 已验证结果

- Web 在精确 Node 24.18.0 / pnpm 11.15.1 环境通过 ESLint、严格 TypeScript、生产构建和 7 项 Vitest 测试。
- 真实 Chromium 完成 7 字段估价、两条历史比较、刷新后保留、市场筛选/统计/图表/排序、真实 what-if 以及 CSV/PDF 下载。
- 1280x800 与 360x800 均已检查；移动端 `scrollWidth == clientWidth`，浏览器正常流程为 0 console 错误/0 警告。
- Estimator 的 ML 断连错误、Market RSC 错误边界与恢复重试均已真实触发。预期 503/504 会被浏览器记录为失败资源，但页面有稳定可重试提示。

## Phase 5 已验证结果

- `docker compose config --quiet` 通过；四个镜像从根构建上下文生成，Web 使用 standalone 运行镜像，运行时不包含开发依赖树。
- `docker compose up -d --wait` 按 ML → 两个业务 API → Web 的健康依赖启动，四容器均为 healthy。
- Compose 网络中 ML 与 Estimator 对相同输入返回完全相同价格 `248849.64329890147` 和模型版本 `ridge-v1-0e36c622-a05bac12`；Market 基线为 50 条、平均价 264600。
- Compose 下真实 Chromium 完成估价、Market RSC、what-if、CSV/PDF 下载；正常流程 console 为 0 错误/0 警告。
- 停止 ML 后 Web readiness 返回 503 与请求 ID，Estimator 显示可重试错误；恢复 ML 后点击原错误的重试按钮成功。`docker compose down` 清除容器/网络后再次一条命令启动成功。
- 本地浏览器截图、下载与构建日志已通过 `.gitignore`/`.dockerignore` 排除，不进入 Git 或 Docker 构建上下文。

## 腾讯云公网已验证结果

- 部署地址：`https://kandian.site/housing`；原 `https://kandian.site/zh-CN/` 保持正常。
- 部署前资源：4 vCPU、根盘可用 14 GiB、内存 available 1.7 GiB；部署后根盘可用 12 GiB、内存 available 1.4 GiB、Swap 可用 1.1 GiB。
- 四容器均 healthy，实际内存约为 ML 109 MiB、Estimator 48 MiB、Market 251 MiB、Web 124 MiB，均低于配置上限。
- 所有宿主机端口只监听 `127.0.0.1`；公网只通过 Nginx `/housing` 路由进入 Web，业务 API 和 ML API 不直接暴露。
- 真实 Chrome 公网验证 Estimator POST、Market Server Component、what-if、CSV/PDF 下载均为 200；正常 console 0 错误/0 警告。
- 1280x800 与 360x800 已检查，移动端 `scrollWidth == clientWidth`；旧 BookSim 书架与核心 API 回归通过。
- Nginx 修改前备份：`/etc/nginx/backups/booksim-before-housing-20260815013813`，路由修正前备份：`/etc/nginx/backups/booksim-before-housing-route-fix-20260815014151`。

## 下一步

完成 Phase 6 剩余事项：检查最终 diff，提交后从 GitHub 干净克隆复跑 Compose，并按 8~12 分钟演示手册彩排。
