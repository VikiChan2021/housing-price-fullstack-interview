# Market API

组件：Java 21、Spring Boot 3.4.4、Caffeine、Apache PDFBox 3.0.8。

职责：

- 读取并校验住房训练数据。
- 市场摘要、筛选、分页、排序和分段统计。
- 调用 `ml-api` 完成 what-if。
- CSV/PDF 导出。
- 有界、短 TTL 的聚合缓存。

不得复制 Python 模型推理。Phase 3 已实现全部职责，并通过 14 项 Java 21 测试、真实跨容器 ML what-if、缓存、导出、故障注入与恢复验收。最终本地镜像摘要为 `sha256:47885a0370708c9b103bf08a5f9bd919c40c6bcb45851897df04e6ee7db3d5db`；公网部署未验证。
