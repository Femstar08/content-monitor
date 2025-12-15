import React, { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  PlusIcon,
  TrashIcon,
  InformationCircleIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { ResourceProfile, InclusionRules, ExclusionRules } from '../../types';

const profileSchema = z.object({
  name: z.string().min(1, 'Profile name is required'),
  starting_urls: z.array(z.string().url('Invalid URL format')).min(1, 'At least one URL is required'),
  inclusion_rules: z.object({
    domains: z.array(z.string()),
    url_patterns: z.array(z.string()),
    file_types: z.array(z.string()),
    content_types: z.array(z.string()),
  }),
  exclusion_rules: z.object({
    domains: z.array(z.string()),
    url_patterns: z.array(z.string()),
    file_types: z.array(z.string()),
    keywords: z.array(z.string()),
  }),
  scraping_depth: z.number().min(1).max(10),
  include_downloads: z.boolean(),
  track_changes: z.boolean(),
  check_frequency: z.string().optional(),
  generate_digest: z.boolean(),
});

type ProfileFormData = z.infer<typeof profileSchema>;

interface ProfileFormProps {
  profile?: ResourceProfile;
  onSubmit: (data: ProfileFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const ProfileForm: React.FC<ProfileFormProps> = ({
  profile,
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const [activeTab, setActiveTab] = useState<'basic' | 'rules' | 'advanced'>('basic');

  const {
    register,
    control,
    handleSubmit,
    watch,
    formState: { errors, isValid },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: profile ? {
      name: profile.name,
      starting_urls: profile.starting_urls,
      inclusion_rules: profile.inclusion_rules,
      exclusion_rules: profile.exclusion_rules,
      scraping_depth: profile.scraping_depth,
      include_downloads: profile.include_downloads,
      track_changes: profile.track_changes,
      check_frequency: profile.check_frequency || '',
      generate_digest: profile.generate_digest,
    } : {
      name: '',
      starting_urls: [''],
      inclusion_rules: { domains: [], url_patterns: [], file_types: [], content_types: [] },
      exclusion_rules: { domains: [], url_patterns: [], file_types: [], keywords: [] },
      scraping_depth: 2,
      include_downloads: true,
      track_changes: true,
      check_frequency: '',
      generate_digest: true,
    },
  });

  const { fields: urlFields, append: appendUrl, remove: removeUrl } = useFieldArray({
    control,
    name: 'starting_urls',
  });

  const tabs = [
    { id: 'basic', name: 'Basic Settings', icon: InformationCircleIcon },
    { id: 'rules', name: 'Filtering Rules', icon: CheckIcon },
    { id: 'advanced', name: 'Advanced', icon: XMarkIcon },
  ];

  return (
    <div className="bg-white shadow-lg rounded-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">
          {profile ? 'Edit Profile' : 'Create New Profile'}
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          Configure monitoring settings for AWS content sources
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.name}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="p-6">
        {/* Basic Settings Tab */}
        {activeTab === 'basic' && (
          <div className="space-y-6">
            {/* Profile Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Profile Name
              </label>
              <input
                {...register('name')}
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., AWS Security Updates"
              />
              {errors.name && (
                <p className="text-red-600 text-sm mt-1">{errors.name.message}</p>
              )}
            </div>

            {/* Starting URLs */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Starting URLs
              </label>
              <div className="space-y-2">
                {urlFields.map((field, index) => (
                  <div key={field.id} className="flex space-x-2">
                    <input
                      {...register(`starting_urls.${index}`)}
                      type="url"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="https://aws.amazon.com/..."
                    />
                    {urlFields.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeUrl(index)}
                        className="px-3 py-2 text-red-600 hover:text-red-800"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    )}
                  </div>
                ))}
                <button
                  type="button"
                  onClick={() => appendUrl('')}
                  className="flex items-center space-x-2 text-blue-600 hover:text-blue-800"
                >
                  <PlusIcon className="h-4 w-4" />
                  <span>Add URL</span>
                </button>
              </div>
              {errors.starting_urls && (
                <p className="text-red-600 text-sm mt-1">{errors.starting_urls.message}</p>
              )}
            </div>

            {/* Basic Options */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Scraping Depth
                </label>
                <select
                  {...register('scraping_depth', { valueAsNumber: true })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {[1, 2, 3, 4, 5].map(depth => (
                    <option key={depth} value={depth}>
                      {depth} level{depth > 1 ? 's' : ''}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-4">
                <label className="flex items-center">
                  <input
                    {...register('include_downloads')}
                    type="checkbox"
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Include downloadable files</span>
                </label>

                <label className="flex items-center">
                  <input
                    {...register('track_changes')}
                    type="checkbox"
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Track content changes</span>
                </label>

                <label className="flex items-center">
                  <input
                    {...register('generate_digest')}
                    type="checkbox"
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Generate intelligence digest</span>
                </label>
              </div>
            </div>
          </div>
        )}

        {/* Rules Tab */}
        {activeTab === 'rules' && (
          <div className="space-y-8">
            {/* Inclusion Rules */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Inclusion Rules</h3>
              <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-4">
                <p className="text-sm text-green-800">
                  Content matching these rules will be included in monitoring
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Allowed Domains
                  </label>
                  <textarea
                    {...register('inclusion_rules.domains')}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="aws.amazon.com&#10;docs.aws.amazon.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    URL Patterns
                  </label>
                  <textarea
                    {...register('inclusion_rules.url_patterns')}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="*/whitepapers/*&#10;*/security/*"
                  />
                </div>
              </div>
            </div>

            {/* Exclusion Rules */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Exclusion Rules</h3>
              <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
                <p className="text-sm text-red-800">
                  Content matching these rules will be excluded from monitoring
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Excluded Domains
                  </label>
                  <textarea
                    {...register('exclusion_rules.domains')}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="marketing.aws.amazon.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Excluded Keywords
                  </label>
                  <textarea
                    {...register('exclusion_rules.keywords')}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="advertisement&#10;promotion&#10;marketing"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Advanced Tab */}
        {activeTab === 'advanced' && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Check Frequency (Cron Expression)
              </label>
              <input
                {...register('check_frequency')}
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="0 0 * * * (daily at midnight)"
              />
              <p className="text-sm text-gray-500 mt-1">
                Leave empty for manual execution only
              </p>
            </div>
          </div>
        )}

        {/* Form Actions */}
        <div className="flex justify-end space-x-4 mt-8 pt-6 border-t border-gray-200">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!isValid || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Saving...' : profile ? 'Update Profile' : 'Create Profile'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ProfileForm;