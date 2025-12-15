import React from 'react';
import { DashboardMetrics } from '../../types';

interface SystemHealthProps {
  metrics?: DashboardMetrics;
}

const SystemHealth: React.FC<SystemHealthProps> = ({ metrics }) => {
  if (!metrics) return null;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">System Health</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="text-center">
          <div className={`w-4 h-4 rounded-full mx-auto mb-2 ${metrics.system_health === 'healthy' ? 'bg-green-500' :
              metrics.system_health === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
            }`} />
          <p className="text-sm font-medium text-gray-900">Overall Status</p>
          <p className="text-sm text-gray-500 capitalize">{metrics.system_health}</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-gray-900">{metrics.active_profiles}</p>
          <p className="text-sm text-gray-500">Active Profiles</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-gray-900">{metrics.total_sources}</p>
          <p className="text-sm text-gray-500">Total Sources</p>
        </div>
      </div>
    </div>
  );
};

export default SystemHealth;