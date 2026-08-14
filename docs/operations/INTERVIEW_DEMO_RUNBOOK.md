# 面试演示手册

目标时长：8~12 分钟。不要现场从零安装依赖或训练未验证的新模型。

## 面试前 30 分钟

- 确认当前 Git commit 和工作区状态。
- 关闭占用 3000、8000、8001、8080 的旧进程。
- 预构建镜像并启动 Compose。
- 执行 health、单条预测、Market summary 和浏览器主流程。
- 准备 Swagger、Estimator、Market 三个标签页。
- 检查浏览器 console/network。
- 保留一组已知输入与预期数量级，不死记精确浮点值。
- 准备截图或短录屏作为不可控环境故障的兜底证据。

已验证的准备命令：

```powershell
docker compose up --build -d --wait
docker compose ps
Invoke-RestMethod http://localhost:3000/api/ready
```

## 1. 30 秒开场

说明系统目标和边界：这是 50 条演示数据上的技术项目，不是商业估价产品；重点是可解释模型、API 契约和 Python/Java/Next.js 集成。

## 2. 架构说明（1 分钟）

展示架构图：

- ML API 是唯一模型推理源。
- Python Estimator 和 Java Market 各自承担业务职责。
- Next.js 提供统一入口。
- Compose 保证一键复现。

主动解释为什么没有数据库/Redis：题目不需要，localStorage 和 Caffeine 足够，降低演示故障面。

## 3. Swagger（2 分钟）

依次演示：

1. `/health`。
2. 单条 `/api/v1/predict`。
3. 批量 `/api/v1/predict`。
4. `/api/v1/model-info` 的系数、指标、模型版本和限制。
5. 一个非法评分，展示 422 字段错误。

## 4. Estimator（2~3 分钟）

- 提交一套房产。
- 指出客户端/服务端校验。
- 展示表格、图表和模型版本。
- 刷新页面证明历史保留。
- 选择多套记录进行比较。

## 5. Market（2~3 分钟）

- 展示服务端首屏统计。
- 使用筛选更新指标、图表和表格。
- 排序表格。
- 运行 what-if 并强调“关联不是因果”。
- 导出 CSV 或 PDF。
- 如时间允许，指出缓存命中证据。

## 6. 工程质量（1 分钟）

- 展示测试摘要与 Compose 状态。
- 说明模型评估协议和特征共线性。
- 说明故障处理和请求 ID。
- 明确本地/公网验证边界。

## 7. 准备的失败场景

优先演示非法输入。停止 ML 的场景已在 Compose 与真实浏览器彩排：

```powershell
docker compose stop ml-api
# 在 Estimator 再次提交，观察带 request ID 的可重试错误
docker compose start ml-api
docker compose up -d --wait
# 点击原页面的 Retry last estimate
```

恢复后先确认 `http://localhost:3000/api/ready` 返回 200，再继续演示。

## 常见追问

### 为什么不用更复杂模型？

数据只有 50 条，题目要求系数。Ridge 在保留可解释性的同时缓解共线性；复杂模型并不自动代表更好的工程判断。

### 为什么拆两个 Python 服务？

原题要求 App 1 Python 后端“集成 Task 1 模型容器”。分离后职责和网络调用可见，也避免把业务 API 与模型 API 混为一谈。

### 为什么历史不进数据库？

没有账户、多设备同步和长期保存要求。localStorage 完成 V1 需求，避免无关基础设施；如果产品需求改变再增加数据库。

### 预测可信吗？

只适合技术演示。样本小、特征共线且缺少真实市场变量；API 明确返回模型版本和限制。

## 演示失败时

1. 不在屏幕前盲目重装。
2. 用 health 和 Compose 状态定位是哪一层。
3. 若短时间无法恢复，展示预先保存的截图/测试报告和代码结构。
4. 清楚说明哪些是刚刚现场验证、哪些是之前本地验证。
