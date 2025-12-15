"""
Tests for data models.
"""
import pytest
from datetime import datetime
from src.models.base import (
    ResourceProfile, InclusionRules, ExclusionRules, 
    ContentSource, ExtractedContent, ContentSection, Change, Digest
)
from src.models.enums import SourceType, ChangeType, ChangeClassification, DigestScope
from src.models.apify_schema import ApifyOutputAdapter


class TestDataModels:
    """Test data model creation and validation."""
    
    def test_resource_profile_creation(self):
        """Test ResourceProfile creation with valid data."""
        inclusion_rules = InclusionRules(
            domains=["aws.amazon.com"],
            url_patterns=["*/whitepapers/*"],
            file_types=["pdf"],
            content_types=["application/pdf"]
        )
        
        exclusion_rules = ExclusionRules(
            domains=["example.com"],
            url_patterns=["*/archive/*"],
            file_types=["zip"],
            keywords=["deprecated"]
        )
        
        profile = ResourceProfile(
            id="profile-1",
            name="AWS Whitepapers",
            starting_urls=["https://aws.amazon.com/whitepapers/"],
            inclusion_rules=inclusion_rules,
            exclusion_rules=exclusion_rules,
            scraping_depth=2,
            include_downloads=True,
            track_changes=True,
            check_frequency="0 0 * * *",  # Daily
            generate_digest=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert profile.id == "profile-1"
        assert profile.name == "AWS Whitepapers"
        assert len(profile.starting_urls) == 1
        assert profile.scraping_depth == 2
        assert profile.include_downloads is True
    
    def test_content_source_creation(self):
        """Test ContentSource creation."""
        source = ContentSource(
            id="source-1",
            url="https://aws.amazon.com/whitepapers/example.pdf",
            source_type=SourceType.PDF,
            profile_id="profile-1",
            discovered_at=datetime.now(),
            last_checked=datetime.now(),
            metadata={"size": 1024, "title": "Example Whitepaper"}
        )
        
        assert source.id == "source-1"
        assert source.source_type == SourceType.PDF
        assert source.profile_id == "profile-1"
        assert "size" in source.metadata
    
    def test_change_creation(self):
        """Test Change creation."""
        change = Change(
            id="change-1",
            source_id="source-1",
            change_type=ChangeType.MODIFIED,
            section_id="section-1",
            old_content="Old content",
            new_content="New content",
            detected_at=datetime.now(),
            impact_score=0.8,
            classification=ChangeClassification.SECURITY,
            confidence_score=0.9
        )
        
        assert change.id == "change-1"
        assert change.change_type == ChangeType.MODIFIED
        assert change.classification == ChangeClassification.SECURITY
        assert change.impact_score == 0.8


class TestApifyOutputAdapter:
    """Test Apify output adapter functionality."""
    
    def test_convert_content_source(self):
        """Test converting ContentSource to Apify format."""
        source = ContentSource(
            id="source-1",
            url="https://aws.amazon.com/example",
            source_type=SourceType.HTML,
            profile_id="profile-1",
            discovered_at=datetime(2024, 1, 1, 12, 0, 0),
            last_checked=datetime(2024, 1, 1, 12, 30, 0),
            metadata={"title": "Example Page"}
        )
        
        apify_source = ApifyOutputAdapter.convert_content_source(source, "Test Profile")
        
        assert apify_source.url == source.url
        assert apify_source.source_type == "html"
        assert apify_source.profile_name == "Test Profile"
        assert apify_source._source == "aws-content-monitor"
        assert "title" in apify_source.metadata
    
    def test_convert_change(self):
        """Test converting Change to Apify format."""
        change = Change(
            id="change-1",
            source_id="source-1",
            change_type=ChangeType.ADDED,
            section_id="New Section",
            old_content=None,
            new_content="New content added",
            detected_at=datetime(2024, 1, 1, 12, 0, 0),
            impact_score=0.7,
            classification=ChangeClassification.FEATURE,
            confidence_score=0.8
        )
        
        apify_change = ApifyOutputAdapter.convert_change(change, "https://example.com")
        
        assert apify_change.source_url == "https://example.com"
        assert apify_change.change_type == "added"
        assert apify_change.section_heading == "New Section"
        assert apify_change.impact_score == 0.7
        assert apify_change.classification == "feature"
        assert apify_change._source == "aws-content-monitor"