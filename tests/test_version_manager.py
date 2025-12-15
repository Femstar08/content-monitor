"""
Unit tests for Version Manager.
"""
import pytest
import tempfile
import shutil
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from src.models.base import ExtractedContent, ContentSection, ValidationError
from src.services.version_manager import VersionManager, ContentVersion


class TestVersionManager:
    """Test cases for VersionManager."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def version_manager(self, temp_storage):
        """Create version manager with temporary storage."""
        return VersionManager(storage_path=temp_storage)
    
    @pytest.fixture
    def sample_content(self):
        """Create sample extracted content."""
        sections = [
            ContentSection(
                id="section_0",
                heading="Introduction",
                content="This is the introduction section.",
                level=1,
                position=0
            ),
            ContentSection(
                id="section_1",
                heading="Main Content",
                content="This is the main content section with detailed information.",
                level=2,
                position=1
            )
        ]
        
        # Calculate the correct hash for these sections
        content_str = ''.join(f"{s.heading}:{s.content}" for s in sections)
        content_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
        
        return ExtractedContent(
            source_id="test_source_123",
            content_hash=content_hash,
            sections=sections,
            extracted_at=datetime.now(timezone.utc),
            extraction_metadata={"url": "https://example.com", "method": "html"}
        )
    
    def test_version_manager_initialization(self, temp_storage):
        """Test version manager initialization."""
        vm = VersionManager(storage_path=temp_storage)
        
        # Check storage path creation
        assert Path(temp_storage).exists()
        
        # Check database initialization
        db_path = Path(temp_storage) / "versions.db"
        assert db_path.exists()
    
    def test_generate_unique_version_id(self, version_manager):
        """Test unique version ID generation."""
        source_id = "test_source"
        content_hash = "test_hash"
        
        # Generate multiple IDs
        id1 = version_manager.generate_unique_version_id(source_id, content_hash)
        id2 = version_manager.generate_unique_version_id(source_id, content_hash)
        
        # Should be different due to timestamp
        assert id1 != id2
        assert len(id1) == 16  # Truncated SHA256
        assert len(id2) == 16
    
    def test_store_version(self, version_manager, sample_content):
        """Test storing a new version."""
        version_id = version_manager.store_version(sample_content)
        
        assert version_id is not None
        assert len(version_id) == 16
        
        # Verify version can be retrieved
        stored_version = version_manager.get_version(version_id)
        assert stored_version is not None
        assert stored_version.source_id == sample_content.source_id
        assert stored_version.content_hash == sample_content.content_hash
        assert len(stored_version.sections) == len(sample_content.sections)
    
    def test_store_duplicate_version(self, version_manager, sample_content):
        """Test storing duplicate version returns same ID."""
        version_id1 = version_manager.store_version(sample_content)
        version_id2 = version_manager.store_version(sample_content)
        
        # Should return the same version ID for identical content
        assert version_id1 == version_id2
    
    def test_get_version_not_found(self, version_manager):
        """Test getting non-existent version."""
        version = version_manager.get_version("nonexistent_id")
        assert version is None
    
    def test_get_latest_version(self, version_manager, sample_content):
        """Test getting latest version for a source."""
        # Store first version
        version_id1 = version_manager.store_version(sample_content)
        
        # Create new content with different sections (don't modify in place)
        modified_sections = [
            ContentSection(
                id="section_0",
                heading="Introduction",
                content="Modified introduction content.",
                level=1,
                position=0
            ),
            ContentSection(
                id="section_1",
                heading="Main Content",
                content="This is the main content section with detailed information.",
                level=2,
                position=1
            )
        ]
        
        # Calculate hash for modified content
        content_str = ''.join(f"{s.heading}:{s.content}" for s in modified_sections)
        modified_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
        
        modified_content = ExtractedContent(
            source_id=sample_content.source_id,
            content_hash=modified_hash,
            sections=modified_sections,
            extracted_at=datetime.now(timezone.utc),
            extraction_metadata=sample_content.extraction_metadata
        )
        
        version_id2 = version_manager.store_version(modified_content)
        
        # Get latest version
        latest = version_manager.get_latest_version(sample_content.source_id)
        assert latest is not None
        assert latest.content_hash == modified_hash
    
    def test_get_version_history(self, version_manager, sample_content):
        """Test getting version history."""
        # Store multiple versions with different content
        stored_hashes = []
        
        for i in range(3):
            # Create new sections for each version
            sections = [
                ContentSection(
                    id="section_0",
                    heading="Introduction",
                    content=f"Content version {i}",
                    level=1,
                    position=0
                ),
                ContentSection(
                    id="section_1",
                    heading="Main Content",
                    content="This is the main content section with detailed information.",
                    level=2,
                    position=1
                )
            ]
            
            # Calculate hash for this version
            content_str = ''.join(f"{s.heading}:{s.content}" for s in sections)
            content_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
            stored_hashes.append(content_hash)
            
            content = ExtractedContent(
                source_id=sample_content.source_id,
                content_hash=content_hash,
                sections=sections,
                extracted_at=datetime.now(timezone.utc),
                extraction_metadata=sample_content.extraction_metadata
            )
            
            version_manager.store_version(content)
        
        # Get history
        history = version_manager.get_version_history(sample_content.source_id)
        assert len(history) == 3
        
        # Should be ordered by most recent first
        assert history[0].content_hash == stored_hashes[-1]  # Most recent
        assert history[-1].content_hash == stored_hashes[0]  # Oldest
        
        # Test with limit
        limited_history = version_manager.get_version_history(sample_content.source_id, limit=2)
        assert len(limited_history) == 2
    
    def test_compare_versions(self, version_manager, sample_content):
        """Test version comparison."""
        # Store first version
        version_id1 = version_manager.store_version(sample_content)
        
        # Create modified content with new sections (don't modify in place)
        modified_sections = [
            ContentSection(
                id="section_0",
                heading="Introduction",
                content="Modified introduction content.",  # Changed content
                level=1,
                position=0
            ),
            ContentSection(
                id="section_1",
                heading="Main Content",
                content="This is the main content section with detailed information.",
                level=2,
                position=1
            ),
            ContentSection(
                id="section_2",
                heading="New Section",
                content="This is a new section.",
                level=2,
                position=2
            )
        ]
        
        modified_content = ExtractedContent(
            source_id=sample_content.source_id,
            content_hash="modified_hash",
            sections=modified_sections,
            extracted_at=datetime.now(timezone.utc),
            extraction_metadata=sample_content.extraction_metadata
        )
        
        version_id2 = version_manager.store_version(modified_content)
        
        # Compare versions
        comparison = version_manager.compare_versions(version_id1, version_id2)
        
        assert not comparison['identical']
        assert comparison['summary']['sections_modified'] >= 1
        assert comparison['summary']['sections_added'] >= 1
        assert comparison['summary']['total_changes'] >= 2
    
    def test_compare_versions_invalid(self, version_manager):
        """Test comparing with invalid version IDs."""
        with pytest.raises(ValidationError):
            version_manager.compare_versions("invalid1", "invalid2")
    
    def test_get_section_history(self, version_manager, sample_content):
        """Test getting section history."""
        section_id = "section_0"
        
        # Store multiple versions with changes to the section
        for i in range(3):
            sample_content.content_hash = f"hash_{i}"
            sample_content.sections[0].content = f"Section content version {i}"
            version_manager.store_version(sample_content)
        
        # Get section history
        history = version_manager.get_section_history(sample_content.source_id, section_id)
        assert len(history) == 3
        
        # Check that we get version_id and section pairs
        for version_id, section in history:
            assert isinstance(version_id, str)
            assert isinstance(section, ContentSection)
            assert section.id == section_id
    
    def test_cleanup_old_versions(self, version_manager, sample_content):
        """Test cleaning up old versions."""
        # Store multiple versions
        for i in range(5):
            sample_content.content_hash = f"hash_{i}"
            sample_content.sections[0].content = f"Content {i}"
            version_manager.store_version(sample_content)
        
        # Clean up, keeping only 3 versions
        deleted_count = version_manager.cleanup_old_versions(sample_content.source_id, keep_count=3)
        assert deleted_count == 2
        
        # Verify only 3 versions remain
        history = version_manager.get_version_history(sample_content.source_id)
        assert len(history) == 3
    
    def test_get_storage_statistics(self, version_manager, sample_content):
        """Test getting storage statistics."""
        # Store some versions
        for i in range(3):
            sample_content.source_id = f"source_{i}"
            sample_content.content_hash = f"hash_{i}"
            version_manager.store_version(sample_content)
        
        stats = version_manager.get_storage_statistics()
        
        assert stats['total_versions'] == 3
        assert stats['unique_sources'] == 3
        assert stats['total_sections'] > 0
        assert stats['storage_size_bytes'] > 0
        assert 'versions_by_source' in stats
    
    def test_validate_version_integrity(self, version_manager, sample_content):
        """Test version integrity validation."""
        version_id = version_manager.store_version(sample_content)
        
        validation = version_manager.validate_version_integrity(version_id)
        
        assert validation['valid'] is True
        assert validation['checks']['content_hash_match'] is True
        assert validation['checks']['unique_section_ids'] is True
        assert len(validation['errors']) == 0
    
    def test_validate_version_integrity_not_found(self, version_manager):
        """Test validation of non-existent version."""
        validation = version_manager.validate_version_integrity("nonexistent")
        
        assert validation['valid'] is False
        assert validation['error'] == 'Version not found'


class TestContentVersion:
    """Test cases for ContentVersion class."""
    
    @pytest.fixture
    def sample_sections(self):
        """Create sample sections."""
        return [
            ContentSection(
                id="section_0",
                heading="Test Heading",
                content="Test content",
                level=1,
                position=0
            )
        ]
    
    def test_content_version_creation(self, sample_sections):
        """Test ContentVersion creation."""
        version = ContentVersion(
            version_id="test_version",
            source_id="test_source",
            content_hash="test_hash",
            sections=sample_sections,
            stored_at=datetime.now(timezone.utc),
            metadata={"test": "data"}
        )
        
        assert version.version_id == "test_version"
        assert version.source_id == "test_source"
        assert version.content_hash == "test_hash"
        assert len(version.sections) == 1
        assert version.metadata["test"] == "data"
    
    def test_content_version_serialization(self, sample_sections):
        """Test ContentVersion to_dict and from_dict."""
        original = ContentVersion(
            version_id="test_version",
            source_id="test_source",
            content_hash="test_hash",
            sections=sample_sections,
            stored_at=datetime.now(timezone.utc),
            metadata={"test": "data"}
        )
        
        # Serialize to dict
        data = original.to_dict()
        assert isinstance(data, dict)
        assert data['version_id'] == "test_version"
        
        # Deserialize from dict
        restored = ContentVersion.from_dict(data)
        assert restored.version_id == original.version_id
        assert restored.source_id == original.source_id
        assert restored.content_hash == original.content_hash
        assert len(restored.sections) == len(original.sections)
        assert restored.sections[0].heading == original.sections[0].heading


class TestVersionManagerEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def version_manager(self):
        """Create version manager with temporary storage."""
        temp_dir = tempfile.mkdtemp()
        vm = VersionManager(storage_path=temp_dir)
        yield vm
        shutil.rmtree(temp_dir)
    
    def test_empty_sections(self, version_manager):
        """Test handling content with no sections."""
        content = ExtractedContent(
            source_id="empty_source",
            content_hash="empty_hash",
            sections=[],
            extracted_at=datetime.now(timezone.utc),
            extraction_metadata={}
        )
        
        version_id = version_manager.store_version(content)
        stored_version = version_manager.get_version(version_id)
        
        assert stored_version is not None
        assert len(stored_version.sections) == 0
    
    def test_large_content(self, version_manager):
        """Test handling large content."""
        large_content = "x" * 10000  # 10KB content
        sections = [
            ContentSection(
                id="large_section",
                heading="Large Section",
                content=large_content,
                level=1,
                position=0
            )
        ]
        
        content = ExtractedContent(
            source_id="large_source",
            content_hash="large_hash",
            sections=sections,
            extracted_at=datetime.now(timezone.utc),
            extraction_metadata={}
        )
        
        version_id = version_manager.store_version(content)
        stored_version = version_manager.get_version(version_id)
        
        assert stored_version is not None
        assert len(stored_version.sections[0].content) == 10000
    
    def test_unicode_content(self, version_manager):
        """Test handling Unicode content."""
        unicode_content = "测试内容 🚀 émojis and spëcial chars"
        sections = [
            ContentSection(
                id="unicode_section",
                heading="Unicode Heading 测试",
                content=unicode_content,
                level=1,
                position=0
            )
        ]
        
        content = ExtractedContent(
            source_id="unicode_source",
            content_hash="unicode_hash",
            sections=sections,
            extracted_at=datetime.now(timezone.utc),
            extraction_metadata={}
        )
        
        version_id = version_manager.store_version(content)
        stored_version = version_manager.get_version(version_id)
        
        assert stored_version is not None
        assert stored_version.sections[0].content == unicode_content
        assert stored_version.sections[0].heading == "Unicode Heading 测试"