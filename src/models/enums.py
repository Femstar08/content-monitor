"""
Enums for AWS Content Monitor system.
"""
from enum import Enum


class SourceType(Enum):
    """Types of content sources."""
    RSS = "rss"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"


class ChangeType(Enum):
    """Types of changes detected between versions."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


class ChangeClassification(Enum):
    """Classification categories for changes."""
    SECURITY = "security"
    FEATURE = "feature"
    DEPRECATION = "deprecation"
    BUGFIX = "bugfix"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


class DigestScope(Enum):
    """Scope of digest generation."""
    PROFILE = "profile"
    GLOBAL = "global"
    CUSTOM = "custom"


class OutputFormat(Enum):
    """Output formats for digests."""
    TEXT = "text"
    HTML = "html"
    PDF = "pdf"
    JSON = "json"