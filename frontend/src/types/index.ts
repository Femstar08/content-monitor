// TypeScript types for the AWS Content Monitor frontend

export interface ResourceProfile {
  id: string;
  name: string;
  starting_urls: string[];
  inclusion_rules: InclusionRules;
  exclusion_rules: ExclusionRules;
  scraping_depth: number;
  include_downloads: boolean;
  track_changes: boolean;
  check_frequency?: string;
  generate_digest: boolean;
  created_at: string;
  updated_at: string;
}

export interface InclusionRules {
  domains: string[];
  url_patterns: string[];
  file_types: string[];
  content_types: string[];
}

export interface ExclusionRules {
  domains: string[];
  url_patterns: string[];
  file_types: string[];
  keywords: string[];
}

export interface ContentSource {
  id: string;
  url: string;
  source_type: 'html' | 'pdf' | 'docx' | 'txt' | 'rss';
  profile_id?: string;
  discovered_at: string;
  last_checked: string;
  metadata: Record<string, any>;
}

export interface ContentSection {
  id: string;
  heading: string;
  content: string;
  level: number;
  position: number;
}

export interface ExtractedContent {
  source_id: string;
  content_hash: string;
  sections: ContentSection[];
  extracted_at: string;
  extraction_metadata: Record<string, any>;
}

export interface Change {
  id: string;
  source_id: string;
  change_type: 'added' | 'removed' | 'modified';
  section_id: string;
  old_content?: string;
  new_content?: string;
  detected_at: string;
  impact_score: number;
  classification: 'security' | 'feature' | 'deprecation' | 'bugfix' | 'documentation' | 'configuration' | 'unknown';
  confidence_score: number;
}

export interface Digest {
  id: string;
  period: {
    start_date: string;
    end_date: string;
  };
  profile_ids?: string[];
  changes: Change[];
  summary: string;
  generated_at: string;
  format_versions: Record<string, string>;
  scope: 'profile' | 'global' | 'custom';
}

export interface ExecutionResult {
  profile_id?: string;
  execution_id: string;
  started_at: string;
  completed_at?: string;
  sources_discovered: number;
  content_extracted: number;
  changes_detected: number;
  digest_generated: boolean;
  errors: string[];
  metadata: Record<string, any>;
}

export interface DashboardMetrics {
  total_profiles: number;
  active_profiles: number;
  total_sources: number;
  recent_changes: number;
  last_execution: string;
  system_health: 'healthy' | 'warning' | 'error';
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}