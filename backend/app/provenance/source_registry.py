from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel

class DataSourceType(str, Enum):
    STATSBOMB_MATCH_EVENT = "STATSBOMB_MATCH_EVENT"
    EXTERNAL_MARKET_ESTIMATE = "EXTERNAL_MARKET_ESTIMATE"
    DERIVED_SEMANTIC_SYNTHESIS = "DERIVED_SEMANTIC_SYNTHESIS"
    DETERMINISTIC_ANALYTICS = "DETERMINISTIC_ANALYTICS"

class ConfidenceGrade(str, Enum):
    HIGG = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class SourceMetadata(BaseModel):
    source_name: str
    source_type: DataSourceType
    license_or_origin: str
    confidence_grade: ConfidenceGrade
    season: str = "2025/2026"
    description: str

REGISTRY: Dict[DataSourceType, SourceMetadata] = {
    DataSourceType.STATSBOMB_MATCH_EVENT: SourceMetadata(
        source_name="Illustrative event-metric benchmark",
        source_type=DataSourceType.STATSBOMB_MATCH_EVENT,
        license_or_origin="Hand-authored portfolio demonstration data; not a verified StatsBomb feed",
        confidence_grade=ConfidenceGrade.LOW,
        season="2025/2026",
        description="Illustrative per-90 values and percentiles stored in seed_database.py; no live event ingestion or independent validation."
    ),
    DataSourceType.EXTERNAL_MARKET_ESTIMATE: SourceMetadata(
        source_name="External Market Intelligence Benchmark",
        source_type=DataSourceType.EXTERNAL_MARKET_ESTIMATE,
        license_or_origin="Aggregated Benchmark Valuation (Estimated)",
        confidence_grade=ConfidenceGrade.MEDIUM,
        season="2025/2026",
        description="Estimated player market valuation, contract expiry, and weekly wages."
    ),
    DataSourceType.DERIVED_SEMANTIC_SYNTHESIS: SourceMetadata(
        source_name="Demo scouting narratives",
        source_type=DataSourceType.DERIVED_SEMANTIC_SYNTHESIS,
        license_or_origin="Hand-authored narratives indexed with scikit-learn TF-IDF",
        confidence_grade=ConfidenceGrade.HIGH,
        season="2025/2026",
        description="Local word and phrase similarity; no Gemini embeddings or live LLM calls."
    ),
    DataSourceType.DETERMINISTIC_ANALYTICS: SourceMetadata(
        source_name="Python Analytics Engine",
        source_type=DataSourceType.DETERMINISTIC_ANALYTICS,
        license_or_origin="Deterministic Mathematical Logic",
        confidence_grade=ConfidenceGrade.HIGH,
        season="2025/2026",
        description="Calculated league adjustments, sample reliability indices, and amortization models."
    )
}

def get_source_metadata(source_type: DataSourceType) -> Optional[SourceMetadata]:
    return REGISTRY.get(source_type)
