import axios, { AxiosResponse } from 'axios';
import {
  ResourceProfile,
  ContentSource,
  Change,
  Digest,
  ExecutionResult,
  DashboardMetrics,
  ApiResponse
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth tokens
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Mock data for development
const mockData = {
  dashboardMetrics: {
    total_profiles: 5,
    active_profiles: 3,
    total_sources: 42,
    recent_changes: 12,
    last_execution: new Date().toISOString(),
    system_health: 'healthy' as const,
  },
  profiles: [
    {
      id: '1',
      name: 'AWS Security Updates',
      starting_urls: ['https://aws.amazon.com/security/'],
      inclusion_rules: { domains: ['aws.amazon.com'], url_patterns: [], file_types: [], content_types: [] },
      exclusion_rules: { domains: [], url_patterns: [], file_types: [], keywords: [] },
      scraping_depth: 2,
      include_downloads: true,
      track_changes: true,
      check_frequency: '0 0 * * *',
      generate_digest: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ],
  changes: [
    {
      id: '1',
      source_id: 'src1',
      change_type: 'modified' as const,
      section_id: 'Security Best Practices',
      old_content: 'Old security guidelines...',
      new_content: 'Updated security guidelines...',
      detected_at: new Date().toISOString(),
      impact_score: 0.8,
      classification: 'security' as const,
      confidence_score: 0.9,
    },
  ],
};

export const apiService = {
  // Dashboard
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    // Mock API call - replace with real API when backend is ready
    return new Promise((resolve) => {
      setTimeout(() => resolve(mockData.dashboardMetrics), 500);
    });
  },

  // Profiles
  async getProfiles(): Promise<ResourceProfile[]> {
    return new Promise((resolve) => {
      setTimeout(() => resolve(mockData.profiles), 300);
    });
  },

  async getProfile(id: string): Promise<ResourceProfile> {
    const response = await apiClient.get<ApiResponse<ResourceProfile>>(`/profiles/${id}`);
    return response.data.data!;
  },

  async createProfile(profile: Omit<ResourceProfile, 'id' | 'created_at' | 'updated_at'>): Promise<ResourceProfile> {
    const response = await apiClient.post<ApiResponse<ResourceProfile>>('/profiles', profile);
    return response.data.data!;
  },

  async updateProfile(id: string, profile: Partial<ResourceProfile>): Promise<ResourceProfile> {
    const response = await apiClient.put<ApiResponse<ResourceProfile>>(`/profiles/${id}`, profile);
    return response.data.data!;
  },

  async deleteProfile(id: string): Promise<void> {
    await apiClient.delete(`/profiles/${id}`);
  },

  async executeProfile(id: string): Promise<ExecutionResult> {
    const response = await apiClient.post<ApiResponse<ExecutionResult>>(`/profiles/${id}/execute`);
    return response.data.data!;
  },

  async validateProfile(profile: any): Promise<{ valid: boolean; errors: string[] }> {
    const response = await apiClient.post<ApiResponse<{ valid: boolean; errors: string[] }>>('/profiles/validate', profile);
    return response.data.data!;
  },

  // Content Sources
  async getContentSources(profileId?: string): Promise<ContentSource[]> {
    const params = profileId ? { profile_id: profileId } : {};
    const response = await apiClient.get<ApiResponse<ContentSource[]>>('/sources', { params });
    return response.data.data!;
  },

  async getContentSource(id: string): Promise<ContentSource> {
    const response = await apiClient.get<ApiResponse<ContentSource>>(`/sources/${id}`);
    return response.data.data!;
  },

  // Changes
  async getChanges(params?: {
    profile_id?: string;
    source_id?: string;
    classification?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }): Promise<Change[]> {
    const response = await apiClient.get<ApiResponse<Change[]>>('/changes', { params });
    return response.data.data!;
  },

  async getRecentChanges(limit: number = 10): Promise<Change[]> {
    return new Promise((resolve) => {
      setTimeout(() => resolve(mockData.changes.slice(0, limit)), 200);
    });
  },

  async getChange(id: string): Promise<Change> {
    const response = await apiClient.get<ApiResponse<Change>>(`/changes/${id}`);
    return response.data.data!;
  },

  // Digests
  async getDigests(params?: {
    profile_id?: string;
    start_date?: string;
    end_date?: string;
    scope?: string;
  }): Promise<Digest[]> {
    const response = await apiClient.get<ApiResponse<Digest[]>>('/digests', { params });
    return response.data.data!;
  },

  async getDigest(id: string): Promise<Digest> {
    const response = await apiClient.get<ApiResponse<Digest>>(`/digests/${id}`);
    return response.data.data!;
  },

  async generateDigest(params: {
    profile_ids?: string[];
    start_date: string;
    end_date: string;
    scope?: 'profile' | 'global' | 'custom';
  }): Promise<Digest> {
    const response = await apiClient.post<ApiResponse<Digest>>('/digests/generate', params);
    return response.data.data!;
  },

  async exportDigest(id: string, format: 'html' | 'pdf' | 'text'): Promise<Blob> {
    const response = await apiClient.get(`/digests/${id}/export/${format}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Execution Results
  async getExecutionResults(profileId?: string): Promise<ExecutionResult[]> {
    const params = profileId ? { profile_id: profileId } : {};
    const response = await apiClient.get<ApiResponse<ExecutionResult[]>>('/executions', { params });
    return response.data.data!;
  },

  async getExecutionResult(id: string): Promise<ExecutionResult> {
    const response = await apiClient.get<ApiResponse<ExecutionResult>>(`/executions/${id}`);
    return response.data.data!;
  },

  // System
  async getSystemHealth(): Promise<{ status: string; details: any }> {
    const response = await apiClient.get<ApiResponse<{ status: string; details: any }>>('/system/health');
    return response.data.data!;
  },

  async getSystemLogs(params?: {
    level?: string;
    limit?: number;
    start_date?: string;
    end_date?: string;
  }): Promise<any[]> {
    const response = await apiClient.get<ApiResponse<any[]>>('/system/logs', { params });
    return response.data.data!;
  },

  // Analytics
  async getAnalytics(params: {
    metric: string;
    start_date: string;
    end_date: string;
    profile_id?: string;
  }): Promise<any> {
    const response = await apiClient.get<ApiResponse<any>>('/analytics', { params });
    return response.data.data!;
  },
};

export default apiService;