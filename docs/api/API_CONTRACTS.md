# API 契约

状态：设计基线，尚未实现。实现后的 OpenAPI 文件必须与本文一致；如有差异，先通过 ADR 更新设计。

## 1. 通用约定

- JSON 字段使用 `snake_case`，前端通过生成类型或适配层消费。
- API 版本前缀：`/api/v1`。
- 请求/响应使用 UTF-8。
- 接受或生成 `X-Request-ID`，并在响应中回传。
- 时间使用 ISO 8601 UTC。
- 金额使用 number，单位为美元；展示层再格式化。

### 通用错误

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "One or more fields are invalid.",
    "details": [
      {
        "field": "school_rating",
        "message": "must be between 0 and 10"
      }
    ],
    "request_id": "5c59f6b4-4a42-49c5-a7aa-b1dcb1431212"
  }
}
```

稳定错误代码：

- `VALIDATION_ERROR`
- `EMPTY_BATCH`
- `BATCH_TOO_LARGE`
- `MODEL_NOT_READY`
- `UPSTREAM_UNAVAILABLE`
- `UPSTREAM_TIMEOUT`
- `DATASET_NOT_READY`
- `EXPORT_FAILED`
- `INTERNAL_ERROR`

## 2. PropertyFeatures

```json
{
  "square_footage": 1550,
  "bedrooms": 3,
  "bathrooms": 2,
  "year_built": 1997,
  "lot_size": 6800,
  "distance_to_city_center": 4.1,
  "school_rating": 7.6
}
```

| 字段 | JSON 类型 | 说明 |
|---|---|---|
| `square_footage` | number | 大于 0 |
| `bedrooms` | integer | 非负，合理上限由 schema 固定 |
| `bathrooms` | number | 非负，允许 0.5 增量但不强制 |
| `year_built` | integer | 合理历史年份，不直接限制在训练范围 |
| `lot_size` | number | 大于 0 |
| `distance_to_city_center` | number | 大于等于 0 |
| `school_rating` | number | 0~10 |

所有数字必须有限，禁止 NaN 和 Infinity。

## 3. ML API

Base URL：`http://ml-api:8000`

### 3.1 `POST /api/v1/predict`

为最直接满足“单条和批量”，请求根节点接受 OpenAPI `oneOf`：一个 `PropertyFeatures` 对象，或一个 `PropertyFeatures[]` 数组。最大批量 100。

单条请求：

```json
{
  "square_footage": 1550,
  "bedrooms": 3,
  "bathrooms": 2,
  "year_built": 1997,
  "lot_size": 6800,
  "distance_to_city_center": 4.1,
  "school_rating": 7.6
}
```

批量请求：

```json
[
  {
    "square_footage": 1550,
    "bedrooms": 3,
    "bathrooms": 2,
    "year_built": 1997,
    "lot_size": 6800,
    "distance_to_city_center": 4.1,
    "school_rating": 7.6
  },
  {
    "square_footage": 2200,
    "bedrooms": 4,
    "bathrooms": 2.5,
    "year_built": 2008,
    "lot_size": 9600,
    "distance_to_city_center": 7,
    "school_rating": 8.8
  }
]
```

统一响应：

```json
{
  "predictions": [
    {
      "index": 0,
      "predicted_price": 250879.73,
      "warnings": []
    }
  ],
  "count": 1,
  "model_version": "ridge-v1",
  "request_id": "5c59f6b4-4a42-49c5-a7aa-b1dcb1431212"
}
```

预测示例中的金额只是契约示例，最终值以仓库训练产物为准。

### 3.2 `GET /api/v1/model-info`

```json
{
  "model_name": "ridge_regression",
  "model_version": "ridge-v1",
  "feature_names": [
    "square_footage",
    "bedrooms",
    "bathrooms",
    "year_built",
    "lot_size",
    "distance_to_city_center",
    "school_rating"
  ],
  "coefficient_space": "standardized",
  "coefficients": {
    "square_footage": 0.0,
    "bedrooms": 0.0,
    "bathrooms": 0.0,
    "year_built": 0.0,
    "lot_size": 0.0,
    "distance_to_city_center": 0.0,
    "school_rating": 0.0
  },
  "intercept": 0.0,
  "training_rows": 50,
  "training_data_sha256": "0E36C6224E1F6FB97C308C9DBE1D6DA22D78D78055181067F8AC4C7155A4A726",
  "metrics": {
    "evaluation_protocol": "nested_5_fold_cross_validation",
    "r2_mean": 0.0,
    "r2_std": 0.0,
    "mae_mean": 0.0,
    "rmse_mean": 0.0
  },
  "limitations": [
    "Small demonstration dataset",
    "Highly correlated features",
    "Not intended for real-world valuation"
  ]
}
```

所有 `0.0` 是待训练填充的占位值，不得作为最终指标。

### 3.3 `GET /health`

```json
{
  "status": "healthy",
  "service": "ml-api",
  "model_loaded": true,
  "model_version": "ridge-v1"
}
```

可增加 `/ready`，但不能删除原题要求的 `/health`。

## 4. Estimator API

Base URL：`http://estimator-api:8001`

### 4.1 `POST /api/v1/estimates`

请求为单个 `PropertyFeatures`。服务端校验后调用 ML API 单条预测。

```json
{
  "estimate_id": "f5b13af6-2436-4e13-8a10-26b9c80a11d8",
  "property": {
    "square_footage": 1550,
    "bedrooms": 3,
    "bathrooms": 2,
    "year_built": 1997,
    "lot_size": 6800,
    "distance_to_city_center": 4.1,
    "school_rating": 7.6
  },
  "predicted_price": 250879.73,
  "model_version": "ridge-v1",
  "warnings": [],
  "created_at": "2026-08-14T00:00:00Z",
  "request_id": "5c59f6b4-4a42-49c5-a7aa-b1dcb1431212"
}
```

### 4.2 `POST /api/v1/estimates/batch`

请求为 1~100 个 `PropertyFeatures` 数组，响应按输入顺序返回估价对象。用于比较页面一次刷新多条记录。

### 4.3 `GET /health`

返回 Estimator 进程状态和 ML 依赖状态；ML 不可用时可以返回 `degraded`，并配合适当 HTTP 状态和 readiness。

Estimator API 不保存浏览器历史。

## 5. Market API

Base URL：`http://market-api:8080`

### 5.1 通用筛选参数

- `min_price`、`max_price`
- `min_square_footage`、`max_square_footage`
- `bedrooms`
- `min_bathrooms`
- `min_year_built`、`max_year_built`
- `min_school_rating`
- `max_distance_to_city_center`

参数组合先规范化，再用于筛选和缓存键。

### 5.2 `GET /api/v1/market/summary`

```json
{
  "count": 50,
  "average_price": 264600.0,
  "median_price": 245000.0,
  "min_price": 160000.0,
  "max_price": 410000.0,
  "average_square_footage": 1690.2,
  "applied_filters": {},
  "cache": {
    "hit": false,
    "ttl_seconds": 300
  },
  "request_id": "5c59f6b4-4a42-49c5-a7aa-b1dcb1431212"
}
```

`median_price` 应在实现测试中根据源数据核对，本文示例不得替代自动计算。

### 5.3 `GET /api/v1/market/properties`

支持筛选、分页和排序：

- `page` 从 0 开始。
- `size` 默认 20，最大 100。
- `sort` 使用白名单，例如 `price,desc`。

响应包含 `items`、`page`、`size`、`total_items`、`total_pages` 和 `applied_filters`。

### 5.4 `GET /api/v1/market/segments`

提供图表所需聚合，可通过 `group_by=bedrooms|year_band|price_band` 选择允许的分组。禁止把任意客户端字符串拼接成表达式。

### 5.5 `POST /api/v1/market/what-if`

```json
{
  "baseline": {
    "square_footage": 1550,
    "bedrooms": 3,
    "bathrooms": 2,
    "year_built": 1997,
    "lot_size": 6800,
    "distance_to_city_center": 4.1,
    "school_rating": 7.6
  },
  "scenario": {
    "square_footage": 1750,
    "bedrooms": 3,
    "bathrooms": 2,
    "year_built": 1997,
    "lot_size": 6800,
    "distance_to_city_center": 4.1,
    "school_rating": 7.6
  }
}
```

响应包含基准预测、场景预测、绝对差、百分比差、模型版本和“非因果解释”提示。

### 5.6 `GET /api/v1/market/export`

参数：通用筛选参数 + `format=csv|pdf`。响应使用正确的 `Content-Type` 与 `Content-Disposition`。CSV 防止公式注入；PDF 包含筛选条件和生成时间。

### 5.7 `GET /health`

返回 Java 进程、CSV 数据加载和 ML 依赖状态。

## 6. Next.js BFF

如果使用 Route Handlers，浏览器端仅调用同源 `/api/...`：

- `/api/estimates` -> Estimator API
- `/api/market/*` -> Market API

BFF 只负责转发、请求 ID、超时和安全响应头，不复制业务计算。Server Components 可在服务端直接使用配置的后端地址。

## 7. HTTP 状态

| 状态 | 用途 |
|---:|---|
| 200 | 成功读取/预测 |
| 400 | 无法解析或逻辑冲突的请求 |
| 413 | 批量过大 |
| 422 | 字段校验失败 |
| 500 | 未预期内部错误 |
| 502 | 下游服务不可用或无效响应 |
| 503 | 本服务尚未 ready |
| 504 | 下游超时 |

## 8. 契约治理

- ML API 的 OpenAPI 是模型相关 schema 的事实来源。
- 实现后将 OpenAPI 快照保存到 `packages/api-contracts/`。
- Estimator 与 Market 客户端通过契约测试防止字段漂移。
- Next.js 优先使用生成的 TypeScript 类型。
- 破坏性修改需要新版本路径或明确 ADR。
