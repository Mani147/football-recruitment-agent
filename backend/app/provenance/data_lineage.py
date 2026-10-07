from typing import Any, Optional
from pydantic import BaseModel
from .source_registry import DataSourceType, SourceMetadata, get_source_metadata, ConfidenceGrade

class ProvenanceItem(BaseModel):
    field_name: str
    value: Any
    source_type: DataSourceType
    source_name: str
    confidence: ConfidenceGrade
    notes: Optional[str] = None

class LineageAuditor:
    @staticmethod
    def tag_metric(field_name: str, value: Any, source_type: DataSourceType, notes: Optional[str] = None) -> ProvenanceItem:
        meta = get_source_metadata(source_type)
        return ProvenanceItem(
            field_name=field_name,
            value=value,
            source_type=source_type,
            source_name=meta.source_name if meta else "Unknown",
            confidence=meta.confidence_grade if meta else ConfidenceGrade.LOW,
            notes=notes
        )
