"""
Resource Profile Manager for AWS Content Monitor.
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Callable
import json
import os
import re
from pathlib import Path
from croniter import croniter

from ..models.base import ResourceProfile, InclusionRules, ExclusionRules, ExecutionResult, ValidationError


class ResourceProfileManager:
    """Manages user-defined resource collections and scraping configurations."""
    
    def __init__(self, storage_path: str = "./data/profiles"):
        """Initialize the profile manager with storage path."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._profiles: Dict[str, ResourceProfile] = {}
        self._load_profiles()
    
    def _load_profiles(self) -> None:
        """Load existing profiles from storage."""
        for profile_file in self.storage_path.glob("*.json"):
            try:
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                    profile = self._deserialize_profile(data)
                    self._profiles[profile.id] = profile
            except Exception as e:
                print(f"Warning: Failed to load profile from {profile_file}: {e}")
    
    def _save_profile(self, profile: ResourceProfile) -> None:
        """Save a profile to storage."""
        profile_file = self.storage_path / f"{profile.id}.json"
        with open(profile_file, 'w') as f:
            json.dump(self._serialize_profile(profile), f, indent=2, default=str)
    
    def _serialize_profile(self, profile: ResourceProfile) -> Dict:
        """Serialize a profile to dictionary."""
        return {
            "id": profile.id,
            "name": profile.name,
            "starting_urls": profile.starting_urls,
            "inclusion_rules": {
                "domains": profile.inclusion_rules.domains,
                "url_patterns": profile.inclusion_rules.url_patterns,
                "file_types": profile.inclusion_rules.file_types,
                "content_types": profile.inclusion_rules.content_types
            },
            "exclusion_rules": {
                "domains": profile.exclusion_rules.domains,
                "url_patterns": profile.exclusion_rules.url_patterns,
                "file_types": profile.exclusion_rules.file_types,
                "keywords": profile.exclusion_rules.keywords
            },
            "scraping_depth": profile.scraping_depth,
            "include_downloads": profile.include_downloads,
            "track_changes": profile.track_changes,
            "check_frequency": profile.check_frequency,
            "generate_digest": profile.generate_digest,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat()
        }
    
    def _deserialize_profile(self, data: Dict) -> ResourceProfile:
        """Deserialize a profile from dictionary."""
        inclusion_rules = InclusionRules(
            domains=data["inclusion_rules"]["domains"],
            url_patterns=data["inclusion_rules"]["url_patterns"],
            file_types=data["inclusion_rules"]["file_types"],
            content_types=data["inclusion_rules"]["content_types"]
        )
        
        exclusion_rules = ExclusionRules(
            domains=data["exclusion_rules"]["domains"],
            url_patterns=data["exclusion_rules"]["url_patterns"],
            file_types=data["exclusion_rules"]["file_types"],
            keywords=data["exclusion_rules"]["keywords"]
        )
        
        return ResourceProfile(
            id=data["id"],
            name=data["name"],
            starting_urls=data["starting_urls"],
            inclusion_rules=inclusion_rules,
            exclusion_rules=exclusion_rules,
            scraping_depth=data["scraping_depth"],
            include_downloads=data["include_downloads"],
            track_changes=data["track_changes"],
            check_frequency=data.get("check_frequency"),
            generate_digest=data["generate_digest"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )
    
    def create_profile(self, name: str, starting_urls: List[str], 
                      inclusion_rules: Optional[InclusionRules] = None,
                      exclusion_rules: Optional[ExclusionRules] = None,
                      scraping_depth: int = 2,
                      include_downloads: bool = True,
                      track_changes: bool = True,
                      check_frequency: Optional[str] = None,
                      generate_digest: bool = True) -> ResourceProfile:
        """Create a new resource profile."""
        profile_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        if inclusion_rules is None:
            inclusion_rules = InclusionRules()
        
        if exclusion_rules is None:
            exclusion_rules = ExclusionRules()
        
        profile = ResourceProfile(
            id=profile_id,
            name=name,
            starting_urls=starting_urls,
            inclusion_rules=inclusion_rules,
            exclusion_rules=exclusion_rules,
            scraping_depth=scraping_depth,
            include_downloads=include_downloads,
            track_changes=track_changes,
            check_frequency=check_frequency,
            generate_digest=generate_digest,
            created_at=now,
            updated_at=now
        )
        
        # Validation happens in __post_init__
        self._profiles[profile_id] = profile
        self._save_profile(profile)
        
        return profile
    
    def update_profile(self, profile_id: str, **kwargs) -> ResourceProfile:
        """Update an existing resource profile."""
        if profile_id not in self._profiles:
            raise ValidationError(f"Profile with ID {profile_id} not found", "profile_id")
        
        profile = self._profiles[profile_id]
        
        # Update fields if provided
        if 'name' in kwargs:
            profile.name = kwargs['name']
        if 'starting_urls' in kwargs:
            profile.starting_urls = kwargs['starting_urls']
        if 'inclusion_rules' in kwargs:
            profile.inclusion_rules = kwargs['inclusion_rules']
        if 'exclusion_rules' in kwargs:
            profile.exclusion_rules = kwargs['exclusion_rules']
        if 'scraping_depth' in kwargs:
            profile.scraping_depth = kwargs['scraping_depth']
        if 'include_downloads' in kwargs:
            profile.include_downloads = kwargs['include_downloads']
        if 'track_changes' in kwargs:
            profile.track_changes = kwargs['track_changes']
        if 'check_frequency' in kwargs:
            profile.check_frequency = kwargs['check_frequency']
        if 'generate_digest' in kwargs:
            profile.generate_digest = kwargs['generate_digest']
        
        profile.updated_at = datetime.utcnow()
        
        # Re-validate after updates
        profile.validate()
        
        self._save_profile(profile)
        return profile
    
    def delete_profile(self, profile_id: str) -> bool:
        """Delete a resource profile."""
        if profile_id not in self._profiles:
            return False
        
        # Remove from memory
        del self._profiles[profile_id]
        
        # Remove from storage
        profile_file = self.storage_path / f"{profile_id}.json"
        if profile_file.exists():
            profile_file.unlink()
        
        return True
    
    def get_profile(self, profile_id: str) -> Optional[ResourceProfile]:
        """Get a resource profile by ID."""
        return self._profiles.get(profile_id)
    
    def list_profiles(self) -> List[ResourceProfile]:
        """List all resource profiles."""
        return list(self._profiles.values())
    
    def execute_profile(self, profile_id: str, 
                       source_discovery_engine=None,
                       content_extractor=None,
                       version_manager=None,
                       change_detector=None,
                       digest_generator=None) -> ExecutionResult:
        """Execute a resource profile with full workflow."""
        if profile_id not in self._profiles:
            raise ValidationError(f"Profile with ID {profile_id} not found", "profile_id")
        
        profile = self._profiles[profile_id]
        execution_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        errors = []
        
        try:
            # Initialize counters
            sources_discovered = 0
            content_extracted = 0
            changes_detected = 0
            digest_generated = False
            
            # Step 1: Source Discovery (if engine provided)
            if source_discovery_engine:
                try:
                    discovered_sources = source_discovery_engine.discover_from_profile(profile)
                    sources_discovered = len(discovered_sources)
                except Exception as e:
                    errors.append(f"Source discovery failed: {str(e)}")
                    discovered_sources = []
            else:
                discovered_sources = []
                errors.append("Source discovery engine not provided")
            
            # Step 2: Content Extraction (if extractor provided)
            extracted_content = []
            if content_extractor and discovered_sources:
                for source in discovered_sources:
                    try:
                        if source.source_type.value == 'html':
                            content = content_extractor.extract_html(source.url)
                        elif source.source_type.value == 'pdf':
                            content = content_extractor.extract_pdf(source.url)
                        else:
                            continue
                        extracted_content.append(content)
                        content_extracted += 1
                    except Exception as e:
                        errors.append(f"Content extraction failed for {source.url}: {str(e)}")
            elif not content_extractor:
                errors.append("Content extractor not provided")
            
            # Step 3: Version Management and Change Detection (if managers provided)
            detected_changes = []
            if version_manager and change_detector and extracted_content:
                for content in extracted_content:
                    try:
                        # Store new version
                        version_id = version_manager.store_version(content)
                        
                        # Get previous version for comparison
                        previous_version = version_manager.get_latest_version(content.source_id)
                        
                        if previous_version and previous_version.content_hash != content.content_hash:
                            # Detect changes
                            changes = change_detector.detect_changes(previous_version, content)
                            detected_changes.extend(changes)
                            changes_detected += len(changes)
                    except Exception as e:
                        errors.append(f"Change detection failed for {content.source_id}: {str(e)}")
            
            # Step 4: Digest Generation (if generator provided and profile configured)
            if digest_generator and profile.generate_digest and detected_changes:
                try:
                    from ..models.base import DateRange
                    period = DateRange(
                        start_date=started_at.replace(day=1),  # Start of month
                        end_date=started_at
                    )
                    digest = digest_generator.generate_profile_digest(profile_id, period)
                    digest_generated = True
                except Exception as e:
                    errors.append(f"Digest generation failed: {str(e)}")
            
            # Create execution result
            completed_at = datetime.utcnow()
            
            return ExecutionResult(
                profile_id=profile_id,
                execution_id=execution_id,
                started_at=started_at,
                completed_at=completed_at,
                sources_discovered=sources_discovered,
                content_extracted=content_extracted,
                changes_detected=changes_detected,
                digest_generated=digest_generated,
                errors=errors,
                metadata={
                    "profile_name": profile.name,
                    "execution_duration_seconds": (completed_at - started_at).total_seconds(),
                    "scraping_depth": profile.scraping_depth,
                    "include_downloads": profile.include_downloads
                }
            )
            
        except Exception as e:
            # Handle unexpected errors
            errors.append(f"Execution failed: {str(e)}")
            return ExecutionResult(
                profile_id=profile_id,
                execution_id=execution_id,
                started_at=started_at,
                completed_at=None,
                sources_discovered=0,
                content_extracted=0,
                changes_detected=0,
                digest_generated=False,
                errors=errors,
                metadata={"profile_name": profile.name}
            )
    
    def validate_profile_config(self, config: Dict) -> None:
        """Validate a profile configuration dictionary."""
        required_fields = ["name", "starting_urls"]
        
        for field in required_fields:
            if field not in config:
                raise ValidationError(f"Missing required field: {field}", field)
        
        if not isinstance(config["name"], str) or not config["name"].strip():
            raise ValidationError("Name must be a non-empty string", "name")
        
        if not isinstance(config["starting_urls"], list) or not config["starting_urls"]:
            raise ValidationError("Starting URLs must be a non-empty list", "starting_urls")
        
        for url in config["starting_urls"]:
            if not isinstance(url, str) or not (url.startswith('http://') or url.startswith('https://')):
                raise ValidationError(f"Invalid URL: {url}", "starting_urls")
    
    def validate_cron_expression(self, cron_expr: str) -> bool:
        """Validate a cron expression."""
        try:
            croniter(cron_expr)
            return True
        except (ValueError, TypeError):
            return False
    
    def get_next_execution_time(self, profile_id: str) -> Optional[datetime]:
        """Get the next scheduled execution time for a profile."""
        profile = self.get_profile(profile_id)
        if not profile or not profile.check_frequency:
            return None
        
        try:
            cron = croniter(profile.check_frequency, datetime.utcnow())
            return cron.get_next(datetime)
        except (ValueError, TypeError):
            return None
    
    def get_profiles_due_for_execution(self, current_time: Optional[datetime] = None) -> List[ResourceProfile]:
        """Get profiles that are due for execution based on their schedule."""
        if current_time is None:
            current_time = datetime.utcnow()
        
        due_profiles = []
        
        for profile in self._profiles.values():
            if not profile.check_frequency:
                continue
            
            try:
                cron = croniter(profile.check_frequency, current_time)
                # Check if the profile should have run in the last minute
                prev_time = cron.get_prev(datetime)
                if (current_time - prev_time).total_seconds() < 60:
                    due_profiles.append(profile)
            except (ValueError, TypeError):
                continue
        
        return due_profiles
    
    def execute_scheduled_profiles(self, **execution_kwargs) -> List[ExecutionResult]:
        """Execute all profiles that are due for execution."""
        due_profiles = self.get_profiles_due_for_execution()
        results = []
        
        for profile in due_profiles:
            try:
                result = self.execute_profile(profile.id, **execution_kwargs)
                results.append(result)
            except Exception as e:
                # Create error result for failed execution
                error_result = ExecutionResult(
                    profile_id=profile.id,
                    execution_id=str(uuid.uuid4()),
                    started_at=datetime.utcnow(),
                    completed_at=None,
                    sources_discovered=0,
                    content_extracted=0,
                    changes_detected=0,
                    digest_generated=False,
                    errors=[f"Scheduled execution failed: {str(e)}"],
                    metadata={"profile_name": profile.name}
                )
                results.append(error_result)
        
        return results
    
    def get_execution_summary(self, results: List[ExecutionResult]) -> Dict:
        """Generate a summary of execution results."""
        total_profiles = len(results)
        successful_executions = len([r for r in results if r.completed_at is not None])
        failed_executions = total_profiles - successful_executions
        
        total_sources = sum(r.sources_discovered for r in results)
        total_content = sum(r.content_extracted for r in results)
        total_changes = sum(r.changes_detected for r in results)
        total_digests = len([r for r in results if r.digest_generated])
        
        all_errors = []
        for result in results:
            all_errors.extend(result.errors)
        
        return {
            "execution_summary": {
                "total_profiles_executed": total_profiles,
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "total_sources_discovered": total_sources,
                "total_content_extracted": total_content,
                "total_changes_detected": total_changes,
                "total_digests_generated": total_digests,
                "total_errors": len(all_errors),
                "error_details": all_errors[:10]  # Limit to first 10 errors
            }
        }