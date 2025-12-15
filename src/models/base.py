"""
Base data models for AWS Content Monitor.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import re
import hashlib
from .enums import SourceType, ChangeType, ChangeClassification, DigestScope


class ValidationError(Exception):
    """Raised when model validation fails."""
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.field = field


@dataclass
class DateRange:
    """Represents a date range for filtering."""
    start_date: datetime
    end_date: datetime
    
    def __post_init__(self):
        """Validate date range after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate the date range."""
        if not isinstance(self.start_date, datetime):
            raise ValidationError("start_date must be a datetime object", "start_date")
        if not isinstance(self.end_date, datetime):
            raise ValidationError("end_date must be a datetime object", "end_date")
        if self.start_date >= self.end_date:
            raise ValidationError("start_date must be before end_date", "start_date")


@dataclass
class InclusionRules:
    """Rules for including content during scraping."""
    domains: List[str] = field(default_factory=list)
    url_patterns: List[str] = field(default_factory=list)
    file_types: List[str] = field(default_factory=list)
    content_types: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate inclusion rules after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate inclusion rules."""
        for domain in self.domains:
            if not isinstance(domain, str) or not domain.strip():
                raise ValidationError("All domains must be non-empty strings", "domains")
        
        for pattern in self.url_patterns:
            if not isinstance(pattern, str):
                raise ValidationError("All URL patterns must be strings", "url_patterns")
            # Convert glob patterns to regex for validation
            try:
                if '*' in pattern and not self._is_valid_regex(pattern):
                    # Convert glob pattern to regex
                    regex_pattern = self._glob_to_regex(pattern)
                    re.compile(regex_pattern)
                else:
                    re.compile(pattern)
            except re.error as e:
                raise ValidationError(f"Invalid URL pattern '{pattern}': {e}", "url_patterns")
        
        for file_type in self.file_types:
            if not isinstance(file_type, str) or not file_type.strip():
                raise ValidationError("All file types must be non-empty strings", "file_types")
        
        for content_type in self.content_types:
            if not isinstance(content_type, str) or not content_type.strip():
                raise ValidationError("All content types must be non-empty strings", "content_types")
    
    def matches_domain(self, url: str) -> bool:
        """Check if URL matches any included domain."""
        if not self.domains:
            return True  # No restrictions if empty
        return any(domain in url for domain in self.domains)
    
    def matches_url_pattern(self, url: str) -> bool:
        """Check if URL matches any included pattern."""
        if not self.url_patterns:
            return True  # No restrictions if empty
        
        for pattern in self.url_patterns:
            try:
                if '*' in pattern and not self._is_valid_regex(pattern):
                    # Convert glob pattern to regex
                    regex_pattern = self._glob_to_regex(pattern)
                    if re.search(regex_pattern, url):
                        return True
                else:
                    if re.search(pattern, url):
                        return True
            except re.error:
                continue  # Skip invalid patterns
        
        return False
    
    def matches_file_type(self, file_extension: str) -> bool:
        """Check if file extension matches any included type."""
        if not self.file_types:
            return True  # No restrictions if empty
        return file_extension.lower() in [ft.lower() for ft in self.file_types]
    
    def _is_valid_regex(self, pattern: str) -> bool:
        """Check if pattern is a valid regex (not a glob pattern)."""
        # Simple heuristic: if it contains regex special chars other than *, it's likely regex
        regex_chars = set('[]()+?^$|\\{}.')
        return any(char in pattern for char in regex_chars)
    
    def _glob_to_regex(self, glob_pattern: str) -> str:
        """Convert glob pattern to regex pattern."""
        # Escape regex special characters except *
        escaped = re.escape(glob_pattern)
        # Replace escaped * with regex equivalent
        regex_pattern = escaped.replace('\\*', '.*')
        return f'^{regex_pattern}$'


@dataclass
class ExclusionRules:
    """Rules for excluding content during scraping."""
    domains: List[str] = field(default_factory=list)
    url_patterns: List[str] = field(default_factory=list)
    file_types: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate exclusion rules after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate exclusion rules."""
        for domain in self.domains:
            if not isinstance(domain, str) or not domain.strip():
                raise ValidationError("All domains must be non-empty strings", "domains")
        
        for pattern in self.url_patterns:
            if not isinstance(pattern, str):
                raise ValidationError("All URL patterns must be strings", "url_patterns")
            # Convert glob patterns to regex for validation
            try:
                if '*' in pattern and not self._is_valid_regex(pattern):
                    # Convert glob pattern to regex
                    regex_pattern = self._glob_to_regex(pattern)
                    re.compile(regex_pattern)
                else:
                    re.compile(pattern)
            except re.error as e:
                raise ValidationError(f"Invalid URL pattern '{pattern}': {e}", "url_patterns")
        
        for file_type in self.file_types:
            if not isinstance(file_type, str) or not file_type.strip():
                raise ValidationError("All file types must be non-empty strings", "file_types")
        
        for keyword in self.keywords:
            if not isinstance(keyword, str) or not keyword.strip():
                raise ValidationError("All keywords must be non-empty strings", "keywords")
    
    def excludes_domain(self, url: str) -> bool:
        """Check if URL should be excluded based on domain."""
        return any(domain in url for domain in self.domains)
    
    def excludes_url_pattern(self, url: str) -> bool:
        """Check if URL should be excluded based on pattern."""
        for pattern in self.url_patterns:
            try:
                if '*' in pattern and not self._is_valid_regex(pattern):
                    # Convert glob pattern to regex
                    regex_pattern = self._glob_to_regex(pattern)
                    if re.search(regex_pattern, url):
                        return True
                else:
                    if re.search(pattern, url):
                        return True
            except re.error:
                continue  # Skip invalid patterns
        
        return False
    
    def excludes_file_type(self, file_extension: str) -> bool:
        """Check if file extension should be excluded."""
        return file_extension.lower() in [ft.lower() for ft in self.file_types]
    
    def excludes_content(self, content: str) -> bool:
        """Check if content should be excluded based on keywords."""
        content_lower = content.lower()
        return any(keyword.lower() in content_lower for keyword in self.keywords)
    
    def _is_valid_regex(self, pattern: str) -> bool:
        """Check if pattern is a valid regex (not a glob pattern)."""
        # Simple heuristic: if it contains regex special chars other than *, it's likely regex
        regex_chars = set('[]()+?^$|\\{}.')
        return any(char in pattern for char in regex_chars)
    
    def _glob_to_regex(self, glob_pattern: str) -> str:
        """Convert glob pattern to regex pattern."""
        # Escape regex special characters except *
        escaped = re.escape(glob_pattern)
        # Replace escaped * with regex equivalent
        regex_pattern = escaped.replace('\\*', '.*')
        return f'^{regex_pattern}$'


@dataclass
class ResourceProfile:
    """User-defined resource collection for monitoring."""
    id: str
    name: str
    starting_urls: List[str]
    inclusion_rules: InclusionRules
    exclusion_rules: ExclusionRules
    scraping_depth: int
    include_downloads: bool
    track_changes: bool
    check_frequency: Optional[str]  # cron expression
    generate_digest: bool
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        """Validate resource profile after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate the resource profile."""
        if not self.id or not isinstance(self.id, str):
            raise ValidationError("ID must be a non-empty string", "id")
        
        if not self.name or not isinstance(self.name, str):
            raise ValidationError("Name must be a non-empty string", "name")
        
        if not self.starting_urls or not isinstance(self.starting_urls, list):
            raise ValidationError("Starting URLs must be a non-empty list", "starting_urls")
        
        for url in self.starting_urls:
            if not isinstance(url, str) or not url.strip():
                raise ValidationError("All starting URLs must be non-empty strings", "starting_urls")
            if not (url.startswith('http://') or url.startswith('https://')):
                raise ValidationError(f"Invalid URL format: {url}", "starting_urls")
        
        if not isinstance(self.inclusion_rules, InclusionRules):
            raise ValidationError("Inclusion rules must be an InclusionRules instance", "inclusion_rules")
        
        if not isinstance(self.exclusion_rules, ExclusionRules):
            raise ValidationError("Exclusion rules must be an ExclusionRules instance", "exclusion_rules")
        
        if not isinstance(self.scraping_depth, int) or self.scraping_depth < 0:
            raise ValidationError("Scraping depth must be a non-negative integer", "scraping_depth")
        
        if not isinstance(self.include_downloads, bool):
            raise ValidationError("Include downloads must be a boolean", "include_downloads")
        
        if not isinstance(self.track_changes, bool):
            raise ValidationError("Track changes must be a boolean", "track_changes")
        
        if not isinstance(self.generate_digest, bool):
            raise ValidationError("Generate digest must be a boolean", "generate_digest")
        
        if not isinstance(self.created_at, datetime):
            raise ValidationError("Created at must be a datetime", "created_at")
        
        if not isinstance(self.updated_at, datetime):
            raise ValidationError("Updated at must be a datetime", "updated_at")


@dataclass
class ContentSource:
    """Represents a discovered content source."""
    id: str
    url: str
    source_type: SourceType
    profile_id: Optional[str]  # Associated resource profile
    discovered_at: datetime
    last_checked: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate content source after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate the content source."""
        if not self.id or not isinstance(self.id, str):
            raise ValidationError("ID must be a non-empty string", "id")
        
        if not self.url or not isinstance(self.url, str):
            raise ValidationError("URL must be a non-empty string", "url")
        
        if not (self.url.startswith('http://') or self.url.startswith('https://')):
            raise ValidationError(f"Invalid URL format: {self.url}", "url")
        
        if not isinstance(self.source_type, SourceType):
            raise ValidationError("Source type must be a SourceType enum", "source_type")
        
        if self.profile_id is not None and (not isinstance(self.profile_id, str) or not self.profile_id.strip()):
            raise ValidationError("Profile ID must be None or a non-empty string", "profile_id")
        
        if not isinstance(self.discovered_at, datetime):
            raise ValidationError("Discovered at must be a datetime", "discovered_at")
        
        if not isinstance(self.last_checked, datetime):
            raise ValidationError("Last checked must be a datetime", "last_checked")
        
        if not isinstance(self.metadata, dict):
            raise ValidationError("Metadata must be a dictionary", "metadata")


@dataclass
class ContentSection:
    """A section within extracted content."""
    id: str
    heading: str
    content: str
    level: int
    position: int
    
    def __post_init__(self):
        """Validate content section after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate the content section."""
        if not self.id or not isinstance(self.id, str):
            raise ValidationError("ID must be a non-empty string", "id")
        
        if not isinstance(self.heading, str):
            raise ValidationError("Heading must be a string", "heading")
        
        if not isinstance(self.content, str):
            raise ValidationError("Content must be a string", "content")
        
        if not isinstance(self.level, int) or self.level < 0:
            raise ValidationError("Level must be a non-negative integer", "level")
        
        if not isinstance(self.position, int) or self.position < 0:
            raise ValidationError("Position must be a non-negative integer", "position")


@dataclass
class ExtractedContent:
    """Content extracted from a source."""
    source_id: str
    content_hash: str
    sections: List[ContentSection]
    extracted_at: datetime
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate extracted content after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate the extracted content."""
        if not self.source_id or not isinstance(self.source_id, str):
            raise ValidationError("Source ID must be a non-empty string", "source_id")
        
        if not self.content_hash or not isinstance(self.content_hash, str):
            raise ValidationError("Content hash must be a non-empty string", "content_hash")
        
        if not isinstance(self.sections, list):
            raise ValidationError("Sections must be a list", "sections")
        
        for i, section in enumerate(self.sections):
            if not isinstance(section, ContentSection):
                raise ValidationError(f"Section {i} must be a ContentSection instance", "sections")
        
        if not isinstance(self.extracted_at, datetime):
            raise ValidationError("Extracted at must be a datetime", "extracted_at")
        
        if not isinstance(self.extraction_metadata, dict):
            raise ValidationError("Extraction metadata must be a dictionary", "extraction_metadata")
    
    def calculate_hash(self) -> str:
        """Calculate content hash based on sections."""
        content_str = "".join(f"{s.heading}:{s.content}" for s in self.sections)
        return hashlib.sha256(content_str.encode()).hexdigest()


@dataclass
class Change:
    """Represents a detected change between versions."""
    id: str
    source_id: str
    change_type: ChangeType
    section_id: str
    old_content: Optional[str]
    new_content: Optional[str]
    detected_at: datetime
    impact_score: float
    classification: ChangeClassification
    confidence_score: float = 0.0
    
    def __post_init__(self):
        """Validate change after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate the change."""
        if not self.id or not isinstance(self.id, str):
            raise ValidationError("ID must be a non-empty string", "id")
        
        if not self.source_id or not isinstance(self.source_id, str):
            raise ValidationError("Source ID must be a non-empty string", "source_id")
        
        if not isinstance(self.change_type, ChangeType):
            raise ValidationError("Change type must be a ChangeType enum", "change_type")
        
        if not self.section_id or not isinstance(self.section_id, str):
            raise ValidationError("Section ID must be a non-empty string", "section_id")
        
        if self.old_content is not None and not isinstance(self.old_content, str):
            raise ValidationError("Old content must be None or a string", "old_content")
        
        if self.new_content is not None and not isinstance(self.new_content, str):
            raise ValidationError("New content must be None or a string", "new_content")
        
        if not isinstance(self.detected_at, datetime):
            raise ValidationError("Detected at must be a datetime", "detected_at")
        
        if not isinstance(self.impact_score, (int, float)) or not (0.0 <= self.impact_score <= 1.0):
            raise ValidationError("Impact score must be a number between 0.0 and 1.0", "impact_score")
        
        if not isinstance(self.classification, ChangeClassification):
            raise ValidationError("Classification must be a ChangeClassification enum", "classification")
        
        if not isinstance(self.confidence_score, (int, float)) or not (0.0 <= self.confidence_score <= 1.0):
            raise ValidationError("Confidence score must be a number between 0.0 and 1.0", "confidence_score")


@dataclass
class Digest:
    """Intelligence digest containing analyzed changes."""
    id: str
    period: DateRange
    profile_ids: Optional[List[str]]  # None for global digest
    changes: List[Change]
    summary: str
    generated_at: datetime
    format_versions: Dict[str, str] = field(default_factory=dict)  # format -> content
    scope: DigestScope = DigestScope.GLOBAL
    
    def __post_init__(self):
        """Validate digest after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate the digest."""
        if not self.id or not isinstance(self.id, str):
            raise ValidationError("ID must be a non-empty string", "id")
        
        if not isinstance(self.period, DateRange):
            raise ValidationError("Period must be a DateRange instance", "period")
        
        if self.profile_ids is not None:
            if not isinstance(self.profile_ids, list):
                raise ValidationError("Profile IDs must be None or a list", "profile_ids")
            for profile_id in self.profile_ids:
                if not isinstance(profile_id, str) or not profile_id.strip():
                    raise ValidationError("All profile IDs must be non-empty strings", "profile_ids")
        
        if not isinstance(self.changes, list):
            raise ValidationError("Changes must be a list", "changes")
        
        for i, change in enumerate(self.changes):
            if not isinstance(change, Change):
                raise ValidationError(f"Change {i} must be a Change instance", "changes")
        
        if not isinstance(self.summary, str):
            raise ValidationError("Summary must be a string", "summary")
        
        if not isinstance(self.generated_at, datetime):
            raise ValidationError("Generated at must be a datetime", "generated_at")
        
        if not isinstance(self.format_versions, dict):
            raise ValidationError("Format versions must be a dictionary", "format_versions")
        
        if not isinstance(self.scope, DigestScope):
            raise ValidationError("Scope must be a DigestScope enum", "scope")


@dataclass
class ExecutionResult:
    """Result of executing a monitoring job."""
    profile_id: Optional[str]
    execution_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    sources_discovered: int
    content_extracted: int
    changes_detected: int
    digest_generated: bool
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate execution result after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate the execution result."""
        if self.profile_id is not None and (not isinstance(self.profile_id, str) or not self.profile_id.strip()):
            raise ValidationError("Profile ID must be None or a non-empty string", "profile_id")
        
        if not self.execution_id or not isinstance(self.execution_id, str):
            raise ValidationError("Execution ID must be a non-empty string", "execution_id")
        
        if not isinstance(self.started_at, datetime):
            raise ValidationError("Started at must be a datetime", "started_at")
        
        if self.completed_at is not None and not isinstance(self.completed_at, datetime):
            raise ValidationError("Completed at must be None or a datetime", "completed_at")
        
        if not isinstance(self.sources_discovered, int) or self.sources_discovered < 0:
            raise ValidationError("Sources discovered must be a non-negative integer", "sources_discovered")
        
        if not isinstance(self.content_extracted, int) or self.content_extracted < 0:
            raise ValidationError("Content extracted must be a non-negative integer", "content_extracted")
        
        if not isinstance(self.changes_detected, int) or self.changes_detected < 0:
            raise ValidationError("Changes detected must be a non-negative integer", "changes_detected")
        
        if not isinstance(self.digest_generated, bool):
            raise ValidationError("Digest generated must be a boolean", "digest_generated")
        
        if not isinstance(self.errors, list):
            raise ValidationError("Errors must be a list", "errors")
        
        for error in self.errors:
            if not isinstance(error, str):
                raise ValidationError("All errors must be strings", "errors")
        
        if not isinstance(self.metadata, dict):
            raise ValidationError("Metadata must be a dictionary", "metadata")