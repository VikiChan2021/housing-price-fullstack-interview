# 数据目录

## `raw/`

- `House Price Dataset.csv`：50 条训练数据，包含 `id`、7 个模型特征和目标 `price`。
- `Test Data For Prediction.csv`：10 条待预测数据，只包含 7 个模型特征。

## 数据保护规则

- `raw/` 只读，不在原文件中填充预测结果。
- 派生数据应写入后续创建的 `data/processed/` 或临时构建目录。
- 预测结果应由 API 返回，必要时导出到独立文件。
- CSV 带 UTF-8 BOM；读取时使用 `utf-8-sig` 或显式清理列名。
- `id` 不是模型特征。

完整数据画像和模型方案见 [数据与模型设计](../docs/architecture/DATA_AND_ML_DESIGN.md)。

