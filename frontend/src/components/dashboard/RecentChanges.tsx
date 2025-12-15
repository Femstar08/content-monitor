import React from 'react';
import { Change } from '../../types';
import { formatDistanceToNow } from 'date-fns';

interface RecentChangesProps {
  changes: Change[];
}

const RecentChanges: React.FC<RecentChangesProps> = ({ changes }) => {
  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Recent Changes</h3>
      </div>
      <div className="p-6">
        {changes.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No recent changes</p>
        ) : (
          <div className="space-y-4">
            {changes.slice(0, 5).map((change) => (
              <div key={change.id} className="flex items-start space-x-3">
                <div className={`w-2 h-2 rounded-full mt-2 ${change.change_type === 'added' ? 'bg-green-500' :
                    change.change_type === 'removed' ? 'bg-red-500' : 'bg-blue-500'
                  }`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {change.section_id}
                  </p>
                  <p className="text-sm text-gray-500">
                    {change.change_type} • {formatDistanceToNow(new Date(change.detected_at), { addSuffix: true })}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default RecentChanges;