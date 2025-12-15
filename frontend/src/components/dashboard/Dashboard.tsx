import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ChartBarIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import { DashboardMetrics, ResourceProfile, Change } from '../../types';
import { apiService } from '../../services/api';
import MetricCard from './MetricCard';
import RecentChanges from './RecentChanges';
import ProfilesList from './ProfilesList';
import SystemHealth from './SystemHealth';

const Dashboard: React.FC = () => {
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: apiService.getDashboardMetrics,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: profiles, isLoading: profilesLoading } = useQuery({
    queryKey: ['profiles'],
    queryFn: apiService.getProfiles,
  });

  const { data: recentChanges, isLoading: changesLoading } = useQuery({
    queryKey: ['recent-changes'],
    queryFn: () => apiService.getRecentChanges(10),
  });

  if (metricsLoading || profilesLoading || changesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-2xl font-bold text-gray-900">AWS Content Monitor Dashboard</h1>
        <p className="text-gray-600 mt-1">Monitor AWS content changes and generate intelligence digests</p>
      </div>

      {/* System Health Alert */}
      {metrics?.system_health !== 'healthy' && (
        <div className={`rounded-md p-4 ${metrics?.system_health === 'warning' ? 'bg-yellow-50 border border-yellow-200' : 'bg-red-50 border border-red-200'
          }`}>
          <div className="flex">
            <ExclamationTriangleIcon className={`h-5 w-5 ${metrics?.system_health === 'warning' ? 'text-yellow-400' : 'text-red-400'
              }`} />
            <div className="ml-3">
              <h3 className={`text-sm font-medium ${metrics?.system_health === 'warning' ? 'text-yellow-800' : 'text-red-800'
                }`}>
                System Health Alert
              </h3>
              <p className={`text-sm mt-1 ${metrics?.system_health === 'warning' ? 'text-yellow-700' : 'text-red-700'
                }`}>
                {metrics?.system_health === 'warning'
                  ? 'Some monitoring profiles may need attention'
                  : 'Critical system issues detected. Please check the logs.'
                }
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Profiles"
          value={metrics?.total_profiles || 0}
          icon={DocumentTextIcon}
          color="blue"
          change={`${metrics?.active_profiles || 0} active`}
        />
        <MetricCard
          title="Content Sources"
          value={metrics?.total_sources || 0}
          icon={EyeIcon}
          color="green"
          change="Discovered sources"
        />
        <MetricCard
          title="Recent Changes"
          value={metrics?.recent_changes || 0}
          icon={ChartBarIcon}
          color="yellow"
          change="Last 24 hours"
        />
        <MetricCard
          title="System Status"
          value={metrics?.system_health === 'healthy' ? 'Healthy' : 'Issues'}
          icon={metrics?.system_health === 'healthy' ? CheckCircleIcon : ExclamationTriangleIcon}
          color={metrics?.system_health === 'healthy' ? 'green' : 'red'}
          change={`Last check: ${new Date().toLocaleTimeString()}`}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profiles Overview */}
        <div className="lg:col-span-2">
          <ProfilesList profiles={profiles || []} />
        </div>

        {/* Recent Changes */}
        <div>
          <RecentChanges changes={recentChanges || []} />
        </div>
      </div>

      {/* System Health Details */}
      <SystemHealth metrics={metrics} />
    </div>
  );
};

export default Dashboard;