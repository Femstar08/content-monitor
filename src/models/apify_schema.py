"""
Apify-compatible output schema for AWS Content Monitor.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from .base import Change, Digest, ExecutionResult, ContentSource
from .enums import ChangeType, ChangeClassification, DigestScope


@dataclass
class ApifyContentSource:
    """Apify-compatible content source output."""
    url: str
    source_type: str
    profile_name: Optional[str]
    discovered_at: str  # ISO format
    last_checked: str  # ISO format
    metadata: Dict[str, Any]
    
    # Apify standard fields
    _scrapedAt: str
    _source: str = "aws-content-monitor"


@dataclass
class ApifyChange:
    """Apify-compatible change output."""
    source_url: str
    change_type: str
    section_heading: str
    old_content: Optional[str]
    new_content: Optional[str]
    detected_at: str  # ISO format
    impact_score: float
    classification: str
    confidence_score: float
    
    # Apify standard fields
    _scrapedAt: str
    _source: str = "aws-content-monitor"


@dataclass
class ApifyDigest:
    """Apify-compatible digest output."""
    digest_id: str
    period_start: str  # ISO format
    period_end: str  # ISO format
    profile_names: Optional[List[str]]
    summary: str
    total_changes: int
    high_impact_changes: int
    security_changes: int
    generated_at: str  # ISO format
    scope: str
    
    # Format versions
    text_version: Optional[str]
    html_version: Optional[str]
    pdf_version: Optional[str]
    
    # Detailed changes
    changes: List[ApifyChange]
    
    # Apify standard fields
    _scrapedAt: str
    _source: str = "aws-content-monitor"


@dataclass
class ApifyExecutionSummary:
    """Apify-compatible execution summary."""
    execution_id: str
    profile_name: Optional[str]
    started_at: str  # ISO format
    completed_at: Optional[str]  # ISO format
    duration_seconds: Optional[float]
    
    # Metrics
    sources_discovered: int
    content_extracted: int
    changes_detected: int
    digest_generated: bool
    
    # Status
    status: str  # "completed", "failed", "partial"
    errors: List[str]
    
    # Apify standard fields
    _scrapedAt: str
    _source: str = "aws-content-monitor"


class ApifyOutputAdapter:
    """Adapter to convert internal models to Apify-compatible format."""
    
    @staticmethod
    def convert_content_source(source: ContentSource, profile_name: Optional[str] = None) -> ApifyContentSource:
        """Convert ContentSource to Apify format."""
        return ApifyContentSource(
            url=source.url,
            source_type=source.source_type.value,
            profile_name=profile_name,
            discovered_at=source.discovered_at.isoformat(),
            last_checked=source.last_checked.isoformat(),
            metadata=source.metadata,
            _scrapedAt=datetime.now(timezone.utc).isoformat()
        )
    
    @staticmethod
    def convert_change(change: Change, source_url: str) -> ApifyChange:
        """Convert Change to Apify format."""
        return ApifyChange(
            source_url=source_url,
            change_type=change.change_type.value,
            section_heading=change.section_id,  # Assuming section_id contains heading
            old_content=change.old_content,
            new_content=change.new_content,
            detected_at=change.detected_at.isoformat(),
            impact_score=change.impact_score,
            classification=change.classification.value,
            confidence_score=change.confidence_score,
            _scrapedAt=datetime.now(timezone.utc).isoformat()
        )
    
    @staticmethod
    def convert_digest(digest: Digest, profile_names: Optional[List[str]] = None, 
                      source_urls: Optional[Dict[str, str]] = None) -> ApifyDigest:
        """Convert Digest to Apify format."""
        # Convert changes
        apify_changes = []
        for change in digest.changes:
            source_url = source_urls.get(change.source_id, "unknown") if source_urls else "unknown"
            apify_changes.append(ApifyOutputAdapter.convert_change(change, source_url))
        
        # Calculate metrics
        high_impact_changes = len([c for c in digest.changes if c.impact_score > 0.7])
        security_changes = len([c for c in digest.changes if c.classification == ChangeClassification.SECURITY])
        
        return ApifyDigest(
            digest_id=digest.id,
            period_start=digest.period.start_date.isoformat(),
            period_end=digest.period.end_date.isoformat(),
            profile_names=profile_names,
            summary=digest.summary,
            total_changes=len(digest.changes),
            high_impact_changes=high_impact_changes,
            security_changes=security_changes,
            generated_at=digest.generated_at.isoformat(),
            scope=digest.scope.value,
            text_version=digest.format_versions.get("text"),
            html_version=digest.format_versions.get("html"),
            pdf_version=digest.format_versions.get("pdf"),
            changes=apify_changes,
            _scrapedAt=datetime.now(timezone.utc).isoformat()
        )
    
    @staticmethod
    def convert_execution_result(result: ExecutionResult, profile_name: Optional[str] = None) -> ApifyExecutionSummary:
        """Convert ExecutionResult to Apify format."""
        duration = None
        if result.completed_at and result.started_at:
            duration = (result.completed_at - result.started_at).total_seconds()
        
        # Determine status
        status = "completed"
        if result.errors:
            status = "partial" if result.completed_at else "failed"
        elif not result.completed_at:
            status = "running"
        
        return ApifyExecutionSummary(
            execution_id=result.execution_id,
            profile_name=profile_name,
            started_at=result.started_at.isoformat(),
            completed_at=result.completed_at.isoformat() if result.completed_at else None,
            duration_seconds=duration,
            sources_discovered=result.sources_discovered,
            content_extracted=result.content_extracted,
            changes_detected=result.changes_detected,
            digest_generated=result.digest_generated,
            status=status,
            errors=result.errors,
            _scrapedAt=datetime.now(timezone.utc).isoformat()
        )
    
    @staticmethod
    def to_dict(obj) -> Dict[str, Any]:
        """Convert dataclass to dictionary for JSON serialization."""
        return asdict(obj)