from typing import Final

FEATURE_NAMES: Final[tuple[str, ...]] = (
    "square_footage",
    "bedrooms",
    "bathrooms",
    "year_built",
    "lot_size",
    "distance_to_city_center",
    "school_rating",
)
TRAIN_COLUMNS: Final[tuple[str, ...]] = ("id", *FEATURE_NAMES, "price")
PREDICTION_COLUMNS: Final[tuple[str, ...]] = FEATURE_NAMES
INTEGER_FIELDS: Final[frozenset[str]] = frozenset({"id", "bedrooms", "year_built"})
RANDOM_SEED: Final = 42
N_SPLITS: Final = 5
ALPHA_GRID: Final[tuple[float, ...]] = (0.01, 0.1, 1.0, 10.0, 100.0)
EVALUATION_IMPLEMENTATION_VERSION: Final = "nested-cv-v1"

LIMITATIONS: Final[tuple[str, ...]] = (
    "Small demonstration dataset",
    "Highly correlated features",
    "Not intended for real-world valuation",
    "Predictions outside observed training ranges are less reliable",
)
