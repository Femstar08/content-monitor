# AWS Content Monitor Design Document

## Overview

The AWS Content Monitor is a flexible document monitoring system that allows users to define, scrape, monitor, and analyze any set of AWS-related resources or documents. The system supports both user-specified resources and automatic monitoring of AWS-wide content sources, generating intelligence digests based on detected changes.

The system follows a pipeline architecture with distinct stages for resource profile management, source discovery, content extraction, version management, change detection, and digest generation. Users can define Resource Profiles that specify exactly what content to monitor, from single URLs to entire document families like the AWS Well-Architected Framework.

The system operates as a scheduled job that can be deployed in cloud environments, processing content from user-defined resources, AWS RSS feeds, documentation pages, and downloadable documents. All data is persisted for historical analysis and audit purposes.

## Architecture

The system follows a modular pipeline architecture with the following high-level flow:

```
RSS Feeds → Source Discovery → Content Extraction → Version Management → Change Detection → Intelligence Digest
    ↓              ↓                ↓                    ↓                    ↓                ↓
Storage Layer ←────────────────────────────────────────────────────────────────────────────────┘
```

### Core Components

1. **Resource Profile Manager**: Manages user-defined resource collections and scraping configurations
2. **Source Discovery Engine**: Monitors AWS RSS feeds and discovers content from user-defined resources
3. **Content Extractor**: Normalizes diverse content formats into comparable text
4. **Version Manager**: Stores and manages document versions with unique identifiers
5. **Change Detector**: Identifies and classifies changes between document versions
6. **Intelligence Digest Generator**: Creates human-readable reports for specific profiles or global changes
7. **Storage Layer**: Persists all data with audit trails and historical access
8. **Execution Controller**: Orchestrates workflows for user-defined resources and scheduled monitoring

## Components and Interfaces

### Resource Profile Manager

**Purpose**: Manage user-defined resource collections and scraping configurations.

**Key Methods**:

- `create_profile(name: str, config: ResourceConfig) -> ResourceProfile`
- `update_profile(profile_id: str, config: ResourceConfig) -> ResourceProfile`
- `delete_profile(profile_id: str) -> bool`
- `get_profile(profile_id: str) -> ResourceProfile`
- `list_profiles() -> List[ResourceProfile]`
- `execute_profile(profile_id: str) -> ExecutionResult`

**Interfaces**:

- Input: Resource profile configurations, URLs, inclusion/exclusion rules
- Output: Managed resource profiles with associated content sources

### Source Discovery Engine

**Purpose**: Discover and track content sources from both user-defined resources and AWS feeds.

**Key Methods**:

- `discover_from_profile(profile: ResourceProfile) -> List[ContentSource]`
- `discover_from_feeds(feed_urls: List[str]) -> List[ContentSource]`
- `extract_links(content: str, depth: int, rules: InclusionRules) -> List[str]`
- `is_duplicate(source: ContentSource) -> bool`
- `validate_source(url: str) -> bool`

**Interfaces**:

- Input: Resource profiles, RSS feed URLs, scraping depth, inclusion rules
- Output: List of discovered content sources with metadata and profile associations

### Content Extractor

**Purpose**: Convert diverse document formats into normalized, comparable text while preserving structure.

**Key Methods**:

- `extract_html(url: str) -> ExtractedContent`
- `extract_pdf(file_path: str) -> ExtractedContent`
- `normalize_text(raw_content: str) -> str`
- `preserve_structure(content: str) -> StructuredContent`

**Interfaces**:

- Input: URLs, file paths, raw content
- Output: Normalized text with preserved logical structure

### Version Manager

**Purpose**: Manage document versions and provide unique identification for change tracking.

**Key Methods**:

- `store_version(content: ExtractedContent) -> VersionId`
- `get_version(version_id: VersionId) -> ExtractedContent`
- `get_latest_version(source_id: str) -> ExtractedContent`
- `list_versions(source_id: str) -> List[VersionId]`

**Interfaces**:

- Input: Extracted content, version queries
- Output: Version identifiers, stored content

### Change Detector

**Purpose**: Identify and classify changes between document versions at section level.

**Key Methods**:

- `detect_changes(old_version: ExtractedContent, new_version: ExtractedContent) -> List[Change]`
- `classify_change(change: Change) -> ChangeType`
- `calculate_impact(changes: List[Change]) -> ImpactScore`

**Interfaces**:

- Input: Two document versions
- Output: Classified changes with impact assessment

### Intelligence Digest Generator

**Purpose**: Create human-readable reports explaining changes and their significance for specific profiles or global changes.

**Key Methods**:

- `generate_digest(changes: List[Change], period: DateRange, profile_ids: Optional[List[str]]) -> Digest`
- `generate_profile_digest(profile_id: str, period: DateRange) -> Digest`
- `generate_global_digest(period: DateRange) -> Digest`
- `prioritize_changes(changes: List[Change]) -> List[Change]`
- `explain_significance(change: Change) -> str`
- `format_output(digest: Digest, format: OutputFormat) -> str`

**Interfaces**:

- Input: Detected changes, reporting period, optional profile filters
- Output: Formatted digest in multiple formats with profile context

## Data Models

### ResourceProfile

```python
@dataclass
class ResourceProfile:
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
```

### InclusionRules

```python
@dataclass
class InclusionRules:
    domains: List[str]
    url_patterns: List[str]
    file_types: List[str]
    content_types: List[str]
```

### ExclusionRules

```python
@dataclass
class ExclusionRules:
    domains: List[str]
    url_patterns: List[str]
    file_types: List[str]
    keywords: List[str]
```

### ContentSource

```python
@dataclass
class ContentSource:
    id: str
    url: str
    source_type: SourceType  # RSS, HTML, PDF
    profile_id: Optional[str]  # Associated resource profile
    discovered_at: datetime
    last_checked: datetime
    metadata: Dict[str, Any]
```

### ExtractedContent

```python
@dataclass
class ExtractedContent:
    source_id: str
    content_hash: str
    sections: List[ContentSection]
    extracted_at: datetime
    extraction_metadata: Dict[str, Any]
```

### ContentSection

```python
@dataclass
class ContentSection:
    id: str
    heading: str
    content: str
    level: int
    position: int
```

### Change

```python
@dataclass
class Change:
    id: str
    source_id: str
    change_type: ChangeType  # ADDED, REMOVED, MODIFIED
    section_id: str
    old_content: Optional[str]
    new_content: Optional[str]
    detected_at: datetime
    impact_score: float
    classification: ChangeClassification  # SECURITY, FEATURE, DEPRECATION, etc.
```

### Digest

```python
@dataclass
class Digest:
    id: str
    period: DateRange
    profile_ids: Optional[List[str]]  # None for global digest
    changes: List[Change]
    summary: str
    generated_at: datetime
    format_versions: Dict[str, str]  # text, pdf, html
    scope: DigestScope  # PROFILE, GLOBAL, CUSTOM
```

## Correctness Properties

_A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees._

### Property Reflection

After analyzing all acceptance criteria, several properties can be consolidated to eliminate redundancy:

- Properties related to content extraction (3.1-3.5, 7.1-7.3) can be combined into comprehensive extraction properties
- Properties about data storage completeness (6.1-6.4) can be unified into storage integrity properties
- Properties about change detection and classification (4.3, 8.2, 8.3) can be consolidated into change management properties
- Properties about output generation (1.1, 1.5, 5.4) can be combined into comprehensive output properties

### Core Properties

**Property 1: Digest Generation Completeness**
_For any_ set of detected changes and reporting period, generating a digest should produce a human-readable report that highlights high-impact changes and includes both text and downloadable formats
**Validates: Requirements 1.1, 1.5**

**Property 2: Change Classification Consistency**
_For any_ detected change, the system should assign both importance and security relevance classifications with confidence indicators
**Validates: Requirements 1.2, 8.3**

**Property 3: Source Reference Integrity**
_For any_ ingested content or detected change, the system should maintain complete, traceable references to original source locations
**Validates: Requirements 1.4, 2.5**

**Property 4: Deduplication Effectiveness**
_For any_ content source, running ingestion multiple times should not create duplicate entries in the system
**Validates: Requirements 2.3**

**Property 5: Content Extraction Consistency**
_For any_ document, processing it multiple times should produce identical normalized output suitable for comparison
**Validates: Requirements 3.3, 3.4**

**Property 6: Structure Preservation**
_For any_ structured document, extraction should preserve logical hierarchy including headings, sections, and hierarchical relationships
**Validates: Requirements 3.2, 7.3**

**Property 7: Version Uniqueness**
_For any_ stored document version, the system should assign a unique identifier that never conflicts with other versions
**Validates: Requirements 4.1**

**Property 8: Change Evidence Completeness**
_For any_ detected change, the system should record sufficient evidence including classification, source modifications, and audit trails
**Validates: Requirements 4.4, 8.2**

**Property 9: Workflow Execution Order**
_For any_ monitoring job execution, the system should perform ingestion, comparison, and digest generation in the correct sequence
**Validates: Requirements 5.2**

**Property 10: Output Structure Compliance**
_For any_ system execution, outputs should conform to structured formats with required metadata and execution summaries
**Validates: Requirements 5.3, 5.4**

**Property 11: Data Persistence Completeness**
_For any_ stored data (content, versions, changes, digests), the system should include complete metadata, timestamps, and integrity validation
**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 8.1**

**Property 12: Error Handling Continuity**
_For any_ parsing or processing error, the system should log detailed error information and continue processing other content without stopping
**Validates: Requirements 7.4, 8.4**

## Error Handling

The system implements comprehensive error handling across all components:

### Content Extraction Errors

- **Parsing Failures**: Log detailed error information and continue with other content
- **Format Conversion Issues**: Attempt alternative extraction methods before failing
- **Network Timeouts**: Implement retry logic with exponential backoff
- **Invalid Content**: Mark as failed but preserve source reference for manual review

### Version Management Errors

- **Storage Failures**: Ensure atomic operations to prevent partial writes
- **Comparison Errors**: Fall back to basic text comparison if advanced algorithms fail
- **Corruption Detection**: Use checksums to validate data integrity on read/write

### Digest Generation Errors

- **Classification Failures**: Assign default classifications with low confidence scores
- **Format Generation Issues**: Ensure at least one output format succeeds
- **Template Errors**: Use fallback templates to maintain service availability

### System-Level Error Handling

- **Resource Exhaustion**: Implement circuit breakers and graceful degradation
- **External Service Failures**: Cache previous results and continue with available data
- **Configuration Errors**: Validate configuration on startup and provide clear error messages

## Testing Strategy

The system employs a dual testing approach combining unit tests and property-based tests to ensure comprehensive coverage and correctness validation.

### Unit Testing Approach

Unit tests focus on specific examples, edge cases, and integration points:

- **Component Integration**: Test interfaces between Source Discovery, Content Extraction, and Version Management
- **Edge Cases**: Empty content, malformed HTML, corrupted PDFs, network failures
- **Specific Examples**: Known AWS announcement formats, typical change patterns
- **Error Conditions**: Invalid inputs, resource exhaustion, external service failures

Unit tests provide concrete validation of expected behaviors and catch specific bugs during development.

### Property-Based Testing Approach

Property-based tests verify universal properties across all valid inputs using **Hypothesis** for Python:

- **Minimum 100 iterations** per property test to ensure statistical confidence
- **Smart generators** that create realistic AWS content, document structures, and change scenarios
- **Comprehensive input space coverage** including edge cases and boundary conditions

Each property-based test will be tagged with comments explicitly referencing the correctness property:

- Format: `# Feature: aws-content-monitor, Property {number}: {property_text}`
- Each correctness property implemented by a SINGLE property-based test
- Tests validate universal behaviors that should hold across all valid executions

### Testing Framework Configuration

- **Primary Framework**: pytest with Hypothesis for property-based testing
- **Coverage Target**: Minimum 80% code coverage across all components
- **Test Organization**: Co-located test files using `.test.py` suffix
- **Continuous Integration**: Automated test execution on all code changes

The combination of unit and property-based tests ensures both concrete correctness validation and universal property verification, providing confidence in system reliability across diverse real-world scenarios.
