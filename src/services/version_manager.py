"""
Version Manager for AWS Content Monitor.
"""
import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import sqlite3
from contextlib import contextmanager

from ..models.base import ExtractedContent, ContentSection, ValidationError


class ContentVersion:
    """Represents a stored version of content."""
    
    def __init__(self, version_id: str, source_id: str, content_hash: str,
                 sections: List[ContentSection], stored_at: datetime,
                 metadata: Optional[Dict[str, Any]] = None):
        self.version_id = version_id
        self.source_id = source_id
        self.content_hash = content_hash
        self.sections = sections
        self.stored_at = stored_at
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'version_id': self.version_id,
            'source_id': self.source_id,
            'content_hash': self.content_hash,
            'sections': [self._section_to_dict(s) for s in self.sections],
            'stored_at': self.stored_at.isoformat(),
            'metadata': self.metadata
        }
    
    def _section_to_dict(self, section: ContentSection) -> Dict[str, Any]:
        """Convert section to dictionary."""
        return {
            'id': section.id,
            'heading': section.heading,
            'content': section.content,
            'level': section.level,
            'position': section.position
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentVersion':
        """Create from dictionary."""
        sections = [cls._section_from_dict(s) for s in data['sections']]
        return cls(
            version_id=data['version_id'],
            source_id=data['source_id'],
            content_hash=data['content_hash'],
            sections=sections,
            stored_at=datetime.fromisoformat(data['stored_at']),
            metadata=data.get('metadata', {})
        )
    
    @classmethod
    def _section_from_dict(cls, data: Dict[str, Any]) -> ContentSection:
        """Create section from dictionary."""
        return ContentSection(
            id=data['id'],
            heading=data['heading'],
            content=data['content'],
            level=data['level'],
            position=data['position']
        )


class VersionManager:
    """Manages content versions with unique ID generation and section-based storage."""
    
    def __init__(self, storage_path: str = "./data/versions"):
        """Initialize the version manager with storage path."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize SQLite database for version metadata
        self.db_path = self.storage_path / "versions.db"
        self._init_database()
        
        # In-memory cache for recent versions
        self._version_cache: Dict[str, ContentVersion] = {}
        self._cache_size_limit = 100
    
    def _init_database(self) -> None:
        """Initialize the SQLite database schema."""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Versions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS versions (
                    version_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    stored_at TEXT NOT NULL,
                    metadata TEXT,
                    file_path TEXT NOT NULL,
                    UNIQUE(source_id, content_hash)
                )
            ''')
            
            # Sections table for granular tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    section_id TEXT NOT NULL,
                    version_id TEXT NOT NULL,
                    section_hash TEXT NOT NULL,
                    heading TEXT NOT NULL,
                    content_length INTEGER NOT NULL,
                    level INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    FOREIGN KEY (version_id) REFERENCES versions (version_id),
                    UNIQUE(version_id, section_id)
                )
            ''')
            
            # Version lineage table for tracking relationships
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS version_lineage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    previous_version_id TEXT,
                    current_version_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (previous_version_id) REFERENCES versions (version_id),
                    FOREIGN KEY (current_version_id) REFERENCES versions (version_id)
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_versions_source_id ON versions (source_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_versions_stored_at ON versions (stored_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sections_version_id ON sections (version_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_lineage_source_id ON version_lineage (source_id)')
            
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection with proper error handling."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def generate_unique_version_id(self, source_id: str, content_hash: str) -> str:
        """Generate a unique version ID based on source and content."""
        # Combine source ID, content hash, and timestamp for uniqueness
        timestamp = datetime.now(timezone.utc).isoformat()
        unique_string = f"{source_id}:{content_hash}:{timestamp}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]
    
    def store_version(self, content: ExtractedContent) -> str:
        """Store a new version of content and return version ID."""
        # Generate unique version ID
        version_id = self.generate_unique_version_id(content.source_id, content.content_hash)
        
        # Check if this exact version already exists
        existing_version = self._get_version_by_hash(content.source_id, content.content_hash)
        if existing_version:
            return existing_version.version_id
        
        # Create content version
        version = ContentVersion(
            version_id=version_id,
            source_id=content.source_id,
            content_hash=content.content_hash,
            sections=content.sections,
            stored_at=content.extracted_at,
            metadata=content.extraction_metadata
        )
        
        # Store version data to file
        version_file = self.storage_path / f"{version_id}.json"
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(version.to_dict(), f, indent=2, ensure_ascii=False)
        
        # Store metadata in database
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Insert version record
            cursor.execute('''
                INSERT INTO versions (version_id, source_id, content_hash, stored_at, metadata, file_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                version_id,
                content.source_id,
                content.content_hash,
                content.extracted_at.isoformat(),
                json.dumps(content.extraction_metadata),
                str(version_file)
            ))
            
            # Insert section records
            for section in content.sections:
                section_hash = self._calculate_section_hash(section)
                cursor.execute('''
                    INSERT INTO sections (section_id, version_id, section_hash, heading, 
                                        content_length, level, position)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    section.id,
                    version_id,
                    section_hash,
                    section.heading,
                    len(section.content),
                    section.level,
                    section.position
                ))
            
            # Update version lineage
            previous_version = self.get_latest_version(content.source_id)
            cursor.execute('''
                INSERT INTO version_lineage (source_id, previous_version_id, current_version_id, created_at)
                VALUES (?, ?, ?, ?)
            ''', (
                content.source_id,
                previous_version.version_id if previous_version else None,
                version_id,
                datetime.now(timezone.utc).isoformat()
            ))
            
            conn.commit()
        
        # Add to cache
        self._add_to_cache(version)
        
        return version_id
    
    def get_version(self, version_id: str) -> Optional[ContentVersion]:
        """Retrieve a specific version by ID."""
        # Check cache first
        if version_id in self._version_cache:
            return self._version_cache[version_id]
        
        # Query database for version metadata
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT version_id, source_id, content_hash, stored_at, metadata, file_path
                FROM versions WHERE version_id = ?
            ''', (version_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Load version data from file
            try:
                with open(row['file_path'], 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                
                version = ContentVersion.from_dict(version_data)
                self._add_to_cache(version)
                return version
                
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Warning: Failed to load version {version_id}: {e}")
                return None
    
    def get_latest_version(self, source_id: str) -> Optional[ContentVersion]:
        """Get the most recent version for a source."""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT version_id FROM versions 
                WHERE source_id = ? 
                ORDER BY stored_at DESC 
                LIMIT 1
            ''', (source_id,))
            
            row = cursor.fetchone()
            if row:
                return self.get_version(row['version_id'])
            
            return None
    
    def get_version_history(self, source_id: str, limit: Optional[int] = None) -> List[ContentVersion]:
        """Get version history for a source, ordered by most recent first."""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT version_id FROM versions 
                WHERE source_id = ? 
                ORDER BY stored_at DESC
            '''
            params = [source_id]
            
            if limit:
                query += ' LIMIT ?'
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            versions = []
            for row in rows:
                version = self.get_version(row['version_id'])
                if version:
                    versions.append(version)
            
            return versions
    
    def compare_versions(self, version1_id: str, version2_id: str) -> Dict[str, Any]:
        """Compare two versions and return detailed comparison."""
        version1 = self.get_version(version1_id)
        version2 = self.get_version(version2_id)
        
        if not version1 or not version2:
            raise ValidationError("One or both versions not found", "version_id")
        
        comparison = {
            'version1_id': version1_id,
            'version2_id': version2_id,
            'identical': version1.content_hash == version2.content_hash,
            'section_changes': [],
            'summary': {
                'sections_added': 0,
                'sections_removed': 0,
                'sections_modified': 0,
                'total_changes': 0
            }
        }
        
        # Create section mappings by position for better comparison
        v1_sections_by_id = {s.id: s for s in version1.sections}
        v2_sections_by_id = {s.id: s for s in version2.sections}
        
        # Also create position-based mapping for detecting structural changes
        v1_sections_by_pos = {s.position: s for s in version1.sections}
        v2_sections_by_pos = {s.position: s for s in version2.sections}
        
        all_section_ids = set(v1_sections_by_id.keys()) | set(v2_sections_by_id.keys())
        
        for section_id in all_section_ids:
            s1 = v1_sections_by_id.get(section_id)
            s2 = v2_sections_by_id.get(section_id)
            
            if s1 and s2:
                # Section exists in both versions - check for changes
                s1_hash = self._calculate_section_hash(s1)
                s2_hash = self._calculate_section_hash(s2)
                
                if s1_hash != s2_hash or s1.content != s2.content or s1.heading != s2.heading:
                    comparison['section_changes'].append({
                        'section_id': section_id,
                        'change_type': 'modified',
                        'old_heading': s1.heading,
                        'new_heading': s2.heading,
                        'content_changed': s1.content != s2.content,
                        'heading_changed': s1.heading != s2.heading,
                        'level_changed': s1.level != s2.level
                    })
                    comparison['summary']['sections_modified'] += 1
            elif s1 and not s2:
                # Section removed
                comparison['section_changes'].append({
                    'section_id': section_id,
                    'change_type': 'removed',
                    'heading': s1.heading
                })
                comparison['summary']['sections_removed'] += 1
            elif s2 and not s1:
                # Section added
                comparison['section_changes'].append({
                    'section_id': section_id,
                    'change_type': 'added',
                    'heading': s2.heading
                })
                comparison['summary']['sections_added'] += 1
        
        comparison['summary']['total_changes'] = len(comparison['section_changes'])
        
        return comparison
    
    def get_section_history(self, source_id: str, section_id: str) -> List[Tuple[str, ContentSection]]:
        """Get history of a specific section across versions."""
        versions = self.get_version_history(source_id)
        section_history = []
        
        for version in versions:
            for section in version.sections:
                if section.id == section_id:
                    section_history.append((version.version_id, section))
                    break
        
        return section_history
    
    def cleanup_old_versions(self, source_id: str, keep_count: int = 10) -> int:
        """Clean up old versions, keeping only the most recent ones."""
        versions = self.get_version_history(source_id)
        
        if len(versions) <= keep_count:
            return 0  # Nothing to clean up
        
        versions_to_delete = versions[keep_count:]
        deleted_count = 0
        
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            for version in versions_to_delete:
                try:
                    # Delete from database
                    cursor.execute('DELETE FROM sections WHERE version_id = ?', (version.version_id,))
                    cursor.execute('DELETE FROM version_lineage WHERE current_version_id = ? OR previous_version_id = ?', 
                                 (version.version_id, version.version_id))
                    cursor.execute('DELETE FROM versions WHERE version_id = ?', (version.version_id,))
                    
                    # Delete file
                    version_file = self.storage_path / f"{version.version_id}.json"
                    if version_file.exists():
                        version_file.unlink()
                    
                    # Remove from cache
                    if version.version_id in self._version_cache:
                        del self._version_cache[version.version_id]
                    
                    deleted_count += 1
                    
                except Exception as e:
                    print(f"Warning: Failed to delete version {version.version_id}: {e}")
            
            conn.commit()
        
        return deleted_count
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get statistics about version storage."""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Count versions by source
            cursor.execute('''
                SELECT source_id, COUNT(*) as version_count
                FROM versions
                GROUP BY source_id
            ''')
            source_stats = {row['source_id']: row['version_count'] for row in cursor.fetchall()}
            
            # Total statistics
            cursor.execute('SELECT COUNT(*) as total_versions FROM versions')
            total_versions = cursor.fetchone()['total_versions']
            
            cursor.execute('SELECT COUNT(*) as total_sections FROM sections')
            total_sections = cursor.fetchone()['total_sections']
            
            cursor.execute('SELECT COUNT(DISTINCT source_id) as unique_sources FROM versions')
            unique_sources = cursor.fetchone()['unique_sources']
            
            # Storage size
            total_size = sum(f.stat().st_size for f in self.storage_path.glob("*.json"))
            
            return {
                'total_versions': total_versions,
                'total_sections': total_sections,
                'unique_sources': unique_sources,
                'storage_size_bytes': total_size,
                'storage_size_mb': round(total_size / (1024 * 1024), 2),
                'cache_size': len(self._version_cache),
                'versions_by_source': source_stats
            }
    
    def _get_version_by_hash(self, source_id: str, content_hash: str) -> Optional[ContentVersion]:
        """Get version by source ID and content hash."""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT version_id FROM versions 
                WHERE source_id = ? AND content_hash = ?
            ''', (source_id, content_hash))
            
            row = cursor.fetchone()
            if row:
                return self.get_version(row['version_id'])
            
            return None
    
    def _calculate_section_hash(self, section: ContentSection) -> str:
        """Calculate hash for a section."""
        section_data = f"{section.heading}:{section.content}:{section.level}"
        return hashlib.md5(section_data.encode('utf-8')).hexdigest()
    
    def _add_to_cache(self, version: ContentVersion) -> None:
        """Add version to cache with size limit."""
        if len(self._version_cache) >= self._cache_size_limit:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._version_cache))
            del self._version_cache[oldest_key]
        
        self._version_cache[version.version_id] = version
    
    def validate_version_integrity(self, version_id: str) -> Dict[str, Any]:
        """Validate the integrity of a stored version."""
        version = self.get_version(version_id)
        if not version:
            return {'valid': False, 'error': 'Version not found'}
        
        validation_result = {
            'valid': True,
            'version_id': version_id,
            'checks': {},
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check content hash integrity
            calculated_hash = self._calculate_content_hash(version.sections)
            validation_result['checks']['content_hash_match'] = calculated_hash == version.content_hash
            
            if not validation_result['checks']['content_hash_match']:
                validation_result['errors'].append('Content hash mismatch - data may be corrupted')
                validation_result['valid'] = False
            
            # Check section integrity
            section_ids = [s.id for s in version.sections]
            validation_result['checks']['unique_section_ids'] = len(section_ids) == len(set(section_ids))
            
            if not validation_result['checks']['unique_section_ids']:
                validation_result['errors'].append('Duplicate section IDs found')
                validation_result['valid'] = False
            
            # Check section positions
            positions = [s.position for s in version.sections]
            expected_positions = list(range(len(positions)))
            validation_result['checks']['sequential_positions'] = sorted(positions) == expected_positions
            
            if not validation_result['checks']['sequential_positions']:
                validation_result['warnings'].append('Section positions are not sequential')
            
            # Check database consistency
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) as count FROM sections WHERE version_id = ?', (version_id,))
                db_section_count = cursor.fetchone()['count']
                
                validation_result['checks']['section_count_match'] = db_section_count == len(version.sections)
                
                if not validation_result['checks']['section_count_match']:
                    validation_result['errors'].append('Section count mismatch between file and database')
                    validation_result['valid'] = False
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f'Validation failed: {str(e)}')
        
        return validation_result
    
    def _calculate_content_hash(self, sections: List[ContentSection]) -> str:
        """Calculate content hash from sections."""
        content_str = ''.join(f"{s.heading}:{s.content}" for s in sections)
        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()