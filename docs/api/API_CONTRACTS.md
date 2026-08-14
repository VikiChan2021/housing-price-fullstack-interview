# API 契约

状态：ML API、Estimator API 与 Market API 已分别在 Phase 1~3 实现并完成本地及容器验证；Portal 同源代理仍为 Phase 4 设计基线。实现后的 OpenAPI 必须与本文一致；如有差异，先通过 ADR 更新设计。

## 1. 通用约定

- JSON 字段使用 `snake_case`，前端通过生成类型或适配层消费。
- API 版本前缀：`/api/v1`。
- 请求/响应使用 UTF-8。
- 接受或生成 `X-Request-ID`，并在响应中回传。
- 时间使用 ISO 8601 UTC。
- 金额使用 number，单位为美元；展示层再格式化。
- 请求对象拒绝未声明字段，避免拼写错误被静默忽略。
- 所有字段级错误使用 JSON 字段名；数组元素使用 `items[0].school_rating` 形式的稳定路径。

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

校验错误的 HTTP 状态与错误码固定如下：字段/类型/对象结构错误返回 `422 VALIDATION_ERROR`；空批次返回 `422 EMPTY_BATCH`；超过 100 条返回 `413 BATCH_TOO_LARGE`。无法解析 JSON 返回 `400 VALIDATION_ERROR`。

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
| `square_footage` | number | `> 0` 且 `<= 100000` |
| `bedrooms` | integer | `>= 0` 且 `<= 100` |
| `bathrooms` | number | `>= 0` 且 `<= 100`；允许小数，不强制 0.5 增量 |
| `year_built` | integer | `>= 1600` 且 `<= 2100`；不直接限制在训练范围 |
| `lot_size` | number | `> 0` 且 `<= 100000000` |
| `distance_to_city_center` | number | `>= 0` 且 `<= 10000` |
| `school_rating` | number | 0~10 |

所有数字必须有限，禁止 NaN 和 Infinity。以上是防止明显错误和资源滥用的硬边界，不是模型可靠范围；超出训练集各特征最小/最大值但仍在硬边界内时允许预测，并为对应字段返回范围外 warning。

### 2.1 RangeWarning

范围警告使用结构化对象，不返回不可解析的自由文本数组：

```json
{
  "code": "OUTSIDE_TRAINING_RANGE",
  "field": "year_built",
  "message": "Value is outside the range observed during training.",
  "value": 2013,
  "training_min": 1978,
  "training_max": 2012
}
```

同一输入有多个字段超出训练范围时，按固定特征顺序返回多个 warning。批量响应中 warning 只属于对应的 prediction item。

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
  "model_version": "ridge-v1-0e36c622-a1b2c3d4",
  "request_id": "5c59f6b4-4a42-49c5-a7aa-b1dcb1431212"
}
```

预测示例中的金额只是契约示例，最终值以仓库训练产物为准。

### 3.2 `GET /api/v1/model-info`

```json
{
  "model_name": "ridge_regression",
  "model_version": "ridge-v1-0e36c622-a1b2c3d4",
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
  "hyperparameters": {
    "alpha": 1.0
  },
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
  "feature_mean": {
    "square_footage": 0.0,
    "bedrooms": 0.0,
    "bathrooms": 0.0,
    "year_built": 0.0,
    "lot_size": 0.0,
    "distance_to_city_center": 0.0,
    "school_rating": 0.0
  },
  "feature_scale": {
    "square_footage": 0.0,
    "bedrooms": 0.0,
    "bathrooms": 0.0,
    "year_built": 0.0,
    "lot_size": 0.0,
    "distance_to_city_center": 0.0,
    "school_rating": 0.0
  },
  "training_rows": 50,
  "training_data_sha256": "0E36C6224E1F6FB97C308C9DBE1D6DA22D78D78055181067F8AC4C7155A4A726",
  "metrics": {
    "evaluation_protocol": "nested_5_fold_cross_validation",
    "r2_mean": 0.0,
    "r2_std": 0.0,
    "mae_mean": 0.0,
    "mae_std": 0.0,
    "rmse_mean": 0.0,
    "rmse_std": 0.0
  },
  "limitations": [
    "Small demonstration dataset",
    "Highly correlated features",
    "Not intended for real-world valuation"
  ]
}
```

所有 `0.0` 是待训练填充的占位值，不得作为最终指标；示例 alpha 和模型版本也只表示响应格式，最终值必须由训练脚本生成。

### 3.3 `GET /health`

```json
{
  "status": "healthy",
  "service": "ml-api",
  "model_loaded": true,
  "model_version": "ridge-v1-0e36c622-a1b2c3d4"
}
```

另提供 `GET /ready`：模型产物已加载且元数据/schema 校验通过时返回 200，否则返回 `503 MODEL_NOT_READY`。不能用 `/ready` 替代原题要求的 `/health`。

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
  "model_version": "ridge-v1-0e36c622-a1b2c3d4",
  "warnings": [],
  "created_at": "2026-08-14T00:00:00Z",
  "request_id": "5c59f6b4-4a42-49c5-a7aa-b1dcb1431212"
}
```

### 4.2 `POST /api/v1/estimates/batch`

请求为 1~100 个 `PropertyFeatures` 数组，响应按输入顺序返回估价对象。用于比较页面一次刷新多条记录。

```json
{
  "estimates": [
    {
      "index": 0,
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
      "model_version": "ridge-v1-0e36c622-a1b2c3d4",
      "warnings": [],
      "created_at": "2026-08-14T00:00:00Z"
    }
  ],
  "count": 1,
  "request_id": "5c59f6b4-4a42-49c5-a7aa-b1dcb1431212"
}
```

### 4.3 `GET /health`

返回 Estimator 进程状态和 ML 依赖状态；ML 不可用时可以返回 `degraded`，并配合适当 HTTP 状态和 readiness。

另提供 `GET /ready`：Estimator 自身配置有效且 ML API ready 时返回 200，否则返回 503。Estimator API 不保存浏览器历史。

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

- 所有数值参数必须有限，并遵循 `PropertyFeatures` 的全局硬边界；价格参数必须 `>= 0`。
- 任一 `min_* > max_*` 返回 `422 VALIDATION_ERROR`，不自动交换。
- 缺失参数表示该维度不过滤；空字符串不得解释为 0。
- 规范化缓存键按参数名排序，数值使用解析后的规范形式，使 `3` 与 `3.0` 等价。

市场数据行统一为 `MarketProperty`：包含 `id`、7 个 `PropertyFeatures` 字段和 `price`。`id` 可用于表格稳定键和定位源行，但不得传给模型。

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
- `sort` 格式为 `<field>,<asc|desc>`；字段白名单为 `id`、`price` 和 7 个特征名，默认 `id,asc`。

响应形状固定为：

```json
{
  "items": [
    {
      "id": 1,
      "square_footage": 1500,
      "bedrooms": 3,
      "bathrooms": 2,
      "year_built": 1995,
      "lot_size": 6500,
      "distance_to_city_center": 4.5,
      "school_rating": 7.5,
      "price": 250000
    }
  ],
  "page": 0,
  "size": 20,
  "total_items": 50,
  "total_pages": 3,
  "sort": "id,asc",
  "applied_filters": {},
  "request_id": "5c59f6b4-4a42-49c5-a7aa-b1dcb1431212"
}
```

### 5.4 `GET /api/v1/market/segments`

提供图表所需聚合，可通过 `group_by=bedrooms|year_band|price_band` 选择允许的分组。禁止把任意客户端字符串拼接成表达式。

```json
{
  "group_by": "bedrooms",
  "segments": [
    {
      "key": "3",
      "label": "3 bedrooms",
      "count": 20,
      "average_price": 270000.0,
      "median_price": 260000.0
    }
  ],
  "applied_filters": {},
  "request_id": "5c59f6b4-4a42-49c5-a7aa-b1dcb1431212"
}
```

分段按数值区间或数值 key 升序返回。`year_band` 使用固定十年区间，`price_band` 使用固定 50000 美元区间；边界为左闭右开，最后区间包含上界。空结果返回 200 和空 `segments`。

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

响应固定为：

```json
{
  "baseline_prediction": 250879.73,
  "scenario_prediction": 270120.25,
  "absolute_difference": 19240.52,
  "percentage_difference": 7.67,
  "model_version": "ridge-v1-0e36c622-a1b2c3d4",
  "baseline_warnings": [],
  "scenario_warnings": [],
  "disclaimer": "This comparison is a model association, not a causal estimate.",
  "request_id": "5c59f6b4-4a42-49c5-a7aa-b1dcb1431212"
}
```

`absolute_difference = scenario - baseline`；百分比以 baseline 为分母并四舍五入到两位。若 baseline 为 0，则 `percentage_difference` 为 `null`。

### 5.6 `GET /api/v1/market/export`

参数：通用筛选参数 + `format=csv|pdf`。响应使用正确的 `Content-Type` 与 `Content-Disposition`。CSV 防止公式注入；PDF 包含筛选条件和生成时间。

- CSV：`text/csv; charset=utf-8`，包含当前全部筛选行（不受列表分页影响）、固定列头和 UTF-8 BOM。
- PDF：`application/pdf`，包含标题、UTC 生成时间、筛选条件、摘要统计和主要数据表；空结果仍生成带“无匹配数据”说明的有效 PDF。
- `Content-Disposition` 使用安全文件名 `market-export-YYYYMMDD.<csv|pdf>`，不得反射未经清理的查询参数。

### 5.7 `GET /health`

返回 Java 进程、CSV 数据加载和 ML 依赖状态，例如：

```json
{
  "status": "healthy",
  "service": "market-api",
  "dataset_loaded": true,
  "row_count": 50,
  "ml_api_status": "up"
}
```

另提供 `GET /ready`：CSV 已校验加载且 ML API ready 时返回 200，否则返回 503。

## 6. Next.js BFF

V1 使用 Route Handlers 作为浏览器同源 BFF。浏览器端仅调用同源 `/api/...`：

- `/api/estimates` -> Estimator API
- `/api/market/*` -> Market API

BFF 只负责转发、请求 ID、超时和安全响应头，不复制业务计算。Server Components 可在服务端直接使用配置的后端地址。客户端代码不得读取或拼接 Compose 内部服务地址。

Web 另提供同源 `GET /api/health` 和 `GET /api/ready`。前者只证明 Next.js 进程可响应；后者检查 Estimator 与 Market readiness，供 Compose 使用。

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
