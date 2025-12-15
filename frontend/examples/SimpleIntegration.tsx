import React, { useState } from 'react';
import AWSContentMonitorModal from '../src/components/embedded/AWSContentMonitorModal';

const SimpleIntegration: React.FC = () => {
  const [showMonitor, setShowMonitor] = useState(false);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">My Existing Application</h1>

      {/* Your existing content */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="font-semibold mb-2">Feature 1</h3>
          <p className="text-gray-600">Your existing feature content</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="font-semibold mb-2">Feature 2</h3>
          <p className="text-gray-600">Your existing feature content</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="font-semibold mb-2">AWS Monitor</h3>
          <p className="text-gray-600 mb-4">Monitor AWS content changes</p>
          <button
            onClick={() => setShowMonitor(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            Open Monitor
          </button>
        </div>
      </div>

      {/* Floating Action Button */}
      <button
        onClick={() => setShowMonitor(true)}
        className="fixed bottom-6 right-6 bg-blue-600 text-white p-4 rounded-full shadow-lg hover:bg-blue-700 transition-colors z-40"
        title="Open AWS Content Monitor"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      </button>

      {/* AWS Content Monitor Modal */}
      <AWSContentMonitorModal
        isOpen={showMonitor}
        onClose={() => setShowMonitor(false)}
        apiBaseUrl="http://localhost:8001/api"
      />
    </div>
  );
};

export default SimpleIntegration;