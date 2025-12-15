import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import AWSContentMonitor from '../src/components/embedded/AWSContentMonitor';
import AWSContentMonitorModal from '../src/components/embedded/AWSContentMonitorModal';
import { useAWSMonitorNavigation } from '../src/hooks/useAWSMonitorNavigation';

// Your existing app component
const ExistingApp: React.FC = () => {
  const [showMonitorModal, setShowMonitorModal] = useState(false);
  const { navigateToMonitor, navigateBack, isInMonitor } = useAWSMonitorNavigation();

  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        {/* Your existing navigation */}
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center space-x-8">
                <Link to="/" className="text-xl font-bold text-gray-900">
                  My App
                </Link>
                <Link to="/dashboard" className="text-gray-600 hover:text-gray-900">
                  Dashboard
                </Link>
                <Link to="/users" className="text-gray-600 hover:text-gray-900">
                  Users
                </Link>

                {/* AWS Monitor Navigation Options */}
                <div className="relative group">
                  <button className="text-gray-600 hover:text-gray-900 flex items-center">
                    AWS Monitor
                    <svg className="ml-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {/* Dropdown menu */}
                  <div className="absolute left-0 mt-2 w-48 bg-white rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                    <div className="py-1">
                      <button
                        onClick={() => navigateToMonitor('dashboard')}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        📊 Open Dashboard
                      </button>
                      <button
                        onClick={() => navigateToMonitor('profiles')}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        📋 Manage Profiles
                      </button>
                      <button
                        onClick={() => setShowMonitorModal(true)}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        🪟 Open in Modal
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Back button when in monitor */}
              {isInMonitor && (
                <button
                  onClick={navigateBack}
                  className="flex items-center text-gray-600 hover:text-gray-900"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  Back to App
                </button>
              )}
            </div>
          </div>
        </nav>

        {/* Main content */}
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            {/* Your existing routes */}
            <Route path="/" element={<HomePage />} />
            <Route path="/dashboard" element={<AppDashboard />} />
            <Route path="/users" element={<UsersPage />} />

            {/* AWS Monitor routes */}
            <Route
              path="/aws-monitor/*"
              element={
                <AWSContentMonitor
                  basePath="/aws-monitor"
                  onNavigateBack={navigateBack}
                  apiBaseUrl="http://localhost:8001/api"
                />
              }
            />
          </Routes>
        </main>

        {/* Modal integration */}
        <AWSContentMonitorModal
          isOpen={showMonitorModal}
          onClose={() => setShowMonitorModal(false)}
          apiBaseUrl="http://localhost:8001/api"
          size="full"
        />
      </div>
    </Router>
  );
};

// Your existing components
const HomePage = () => (
  <div className="bg-white rounded-lg shadow p-6">
    <h1 className="text-2xl font-bold mb-4">Welcome to My App</h1>
    <p>This is your existing application with integrated AWS Content Monitor.</p>
  </div>
);

const AppDashboard = () => (
  <div className="bg-white rounded-lg shadow p-6">
    <h1 className="text-2xl font-bold mb-4">App Dashboard</h1>
    <p>Your existing dashboard content.</p>
  </div>
);

const UsersPage = () => (
  <div className="bg-white rounded-lg shadow p-6">
    <h1 className="text-2xl font-bold mb-4">Users</h1>
    <p>Your existing users page.</p>
  </div>
);

export default ExistingApp;