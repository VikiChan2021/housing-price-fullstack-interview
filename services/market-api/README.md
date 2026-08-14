# Market API

计划组件：Java 21、Spring Boot 3.4.4、Caffeine。

职责：

- 读取并校验住房训练数据。
- 市场摘要、筛选、分页、排序和分段统计。
- 调用 `ml-api` 完成 what-if。
- CSV/PDF 导出。
- 有界、短 TTL 的聚合缓存。

不得复制 Python 模型推理。Phase 0B 已建立 Java 21 / Spring Boot 3.4.4 最小工程、Maven Wrapper 和健康检查；业务实现尚未开始。
