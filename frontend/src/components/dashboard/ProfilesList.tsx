import React from 'react';
import { ResourceProfile } from '../../types';
import { formatDistanceToNow } from 'date-fns';

interface ProfilesListProps {
  profiles: ResourceProfile[];
}

const ProfilesList: React.FC<ProfilesListProps> = ({ profiles }) => {
  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Monitoring Profiles</h3>
      </div>
      <div className="p-6">
        {profiles.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No profiles configured</p>
        ) : (
          <div className="space-y-4">
            {profiles.slice(0, 5).map((profile) => (
              <div key={profile.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">{profile.name}</h4>
                  <p className="text-sm text-gray-500">
                    {profile.starting_urls.length} source{profile.starting_urls.length !== 1 ? 's' : ''} •
                    Updated {formatDistanceToNow(new Date(profile.updated_at), { addSuffix: true })}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${profile.track_changes ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                    {profile.track_changes ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfilesList;