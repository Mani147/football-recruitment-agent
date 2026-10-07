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
        source_name="StatsBomb Open Data",
        source_type=DataSourceType.STATSBOMB_MATCH_EVENT,
        license_or_origin="Open Data Repository (2025/26 Season)",
        confidence_grade=ConfidenceGrade.HIGH,
        season="2025/2026",
        description="Match events, lineups, per-90 metrics and spatial event logs."
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
        source_name="Statistical Style Synthesis (Option C)",
        source_type=DataSourceType.DERIVED_SEMANTIC_SYNTHESIS,
        license_or_origin="Generated from deterministic per-90 percentiles + Gemini Embedding",
        confidence_grade=ConfidenceGrade.HIGH,
        season="2025/2026",
        description="Synthesized qualitative scout narratives embedded via gemini-embedding-2-preview."
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
