import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Import your existing components
import Dashboard from '../dashboard/Dashboard';
import ProfilesPage from '../../pages/ProfilesPage';
import ContentPage from '../../pages/ContentPage';
import ChangesPage from '../../pages/ChangesPage';
import DigestsPage from '../../pages/DigestsPage';
import AnalyticsPage from '../../pages/AnalyticsPage';
import SettingsPage from '../../pages/SettingsPage';

interface AWSContentMonitorProps {
  /** Base path for routing (e.g., '/aws-monitor') */
  basePath?: string;
  /** API base URL for the backend */
  apiBaseUrl?: string;
  /** Custom theme/styling */
  theme?: 'light' | 'dark';
  /** Callback when user wants to navigate back to parent app */
  onNavigateBack?: () => void;
  /** Show/hide the back button */
  showBackButton?: boolean;
  /** Custom header content */
  headerContent?: React.ReactNode;
}

// Create a separate query client for the monitor
const createQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

const AWSContentMonitor: React.FC<AWSContentMonitorProps> = ({
  basePath = '/aws-monitor',
  apiBaseUrl = 'http://localhost:8001/api',
  theme = 'light',
  onNavigateBack,
  showBackButton = true,
  headerContent,
}) => {
  const queryClient = React.useMemo(() => createQueryClient(), []);

  // Set API base URL globally (you'd need to modify your API service)
  React.useEffect(() => {
    if (window.AWS_MONITOR_CONFIG) {
      window.AWS_MONITOR_CONFIG.apiBaseUrl = apiBaseUrl;
    } else {
      window.AWS_MONITOR_CONFIG = { apiBaseUrl };
    }
  }, [apiBaseUrl]);

  return (
    <QueryClientProvider client={queryClient}>
      <div className={`aws-content-monitor ${theme === 'dark' ? 'dark' : ''}`}>
        {/* Header with back button */}
        {(showBackButton || headerContent) && (
          <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {showBackButton && onNavigateBack && (
                <button
                  onClick={onNavigateBack}
                  className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  Back to App
                </button>
              )}
              <h1 className="text-xl font-semibold text-gray-900">AWS Content Monitor</h1>
            </div>
            {headerContent && <div>{headerContent}</div>}
          </div>
        )}

        {/* Monitor Content */}
        <div className="flex h-screen bg-gray-50">
          {/* Simplified Sidebar for embedded mode */}
          <EmbeddedSidebar basePath={basePath} />

          {/* Main Content */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="flex-1 overflow-y-auto p-6">
              <Routes>
                <Route path={`${basePath}`} element={<Navigate to={`${basePath}/dashboard`} replace />} />
                <Route path={`${basePath}/dashboard`} element={<Dashboard />} />
                <Route path={`${basePath}/profiles/*`} element={<ProfilesPage />} />
                <Route path={`${basePath}/content/*`} element={<ContentPage />} />
                <Route path={`${basePath}/changes/*`} element={<ChangesPage />} />
                <Route path={`${basePath}/digests/*`} element={<DigestsPage />} />
                <Route path={`${basePath}/analytics`} element={<AnalyticsPage />} />
                <Route path={`${basePath}/settings`} element={<SettingsPage />} />
              </Routes>
            </div>
          </div>
        </div>

        {/* Toast Notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
          }}
        />
      </div>
    </QueryClientProvider>
  );
};

// Simplified sidebar for embedded mode
const EmbeddedSidebar: React.FC<{ basePath: string }> = ({ basePath }) => {
  const navigation = [
    { name: 'Dashboard', href: `${basePath}/dashboard`, icon: '📊' },
    { name: 'Profiles', href: `${basePath}/profiles`, icon: '📋' },
    { name: 'Content', href: `${basePath}/content`, icon: '👁️' },
    { name: 'Changes', href: `${basePath}/changes`, icon: '⚠️' },
    { name: 'Digests', href: `${basePath}/digests`, icon: '📰' },
    { name: 'Analytics', href: `${basePath}/analytics`, icon: '📈' },
  ];

  return (
    <div className="w-64 bg-white border-r border-gray-200">
      <nav className="mt-4 px-2 space-y-1">
        {navigation.map((item) => (
          <a
            key={item.name}
            href={item.href}
            className="group flex items-center px-2 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-50 hover:text-gray-900"
          >
            <span className="mr-3 text-lg">{item.icon}</span>
            {item.name}
          </a>
        ))}
      </nav>
    </div>
  );
};

export default AWSContentMonitor;