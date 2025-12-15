import React, { useState } from 'react';
import {
  ChevronDownIcon,
  ChevronRightIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';
import { Change, ContentSource } from '../../types';
import { formatDistanceToNow } from 'date-fns';

interface ChangeViewerProps {
  changes: Change[];
  sources: ContentSource[];
  onChangeSelect?: (change: Change) => void;
}

const ChangeViewer: React.FC<ChangeViewerProps> = ({
  changes,
  sources,
  onChangeSelect,
}) => {
  const [expandedChanges, setExpandedChanges] = useState<Set<string>>(new Set());
  const [selectedClassification, setSelectedClassification] = useState<string>('all');
  const [selectedImpact, setSelectedImpact] = useState<string>('all');

  const toggleExpanded = (changeId: string) => {
    const newExpanded = new Set(expandedChanges);
    if (newExpanded.has(changeId)) {
      newExpanded.delete(changeId);
    } else {
      newExpanded.add(changeId);
    }
    setExpandedChanges(newExpanded);
  };

  const getChangeIcon = (changeType: string) => {
    switch (changeType) {
      case 'added':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'removed':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'modified':
        return <InformationCircleIcon className="h-5 w-5 text-blue-500" />;
      default:
        return <InformationCircleIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getClassificationColor = (classification: string) => {
    switch (classification) {
      case 'security':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'feature':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'deprecation':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'bugfix':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getImpactColor = (score: number) => {
    if (score >= 0.8) return 'bg-red-500';
    if (score >= 0.6) return 'bg-yellow-500';
    if (score >= 0.4) return 'bg-blue-500';
    return 'bg-gray-500';
  };

  const filteredChanges = changes.filter(change => {
    if (selectedClassification !== 'all' && change.classification !== selectedClassification) {
      return false;
    }
    if (selectedImpact !== 'all') {
      const impactThreshold = parseFloat(selectedImpact);
      if (change.impact_score < impactThreshold) {
        return false;
      }
    }
    return true;
  });

  const getSourceUrl = (sourceId: string) => {
    const source = sources.find(s => s.id === sourceId);
    return source?.url || 'Unknown source';
  };

  return (
    <div className="bg-white shadow rounded-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Content Changes</h2>
            <p className="text-sm text-gray-600 mt-1">
              {filteredChanges.length} of {changes.length} changes
            </p>
          </div>

          {/* Filters */}
          <div className="flex space-x-4">
            <select
              value={selectedClassification}
              onChange={(e) => setSelectedClassification(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Classifications</option>
              <option value="security">Security</option>
              <option value="feature">Feature</option>
              <option value="deprecation">Deprecation</option>
              <option value="bugfix">Bug Fix</option>
              <option value="documentation">Documentation</option>
            </select>

            <select
              value={selectedImpact}
              onChange={(e) => setSelectedImpact(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Impact Levels</option>
              <option value="0.8">High Impact (0.8+)</option>
              <option value="0.6">Medium Impact (0.6+)</option>
              <option value="0.4">Low Impact (0.4+)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Changes List */}
      <div className="divide-y divide-gray-200">
        {filteredChanges.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <InformationCircleIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No changes found</h3>
            <p className="text-gray-600">
              No changes match the current filter criteria.
            </p>
          </div>
        ) : (
          filteredChanges.map((change) => (
            <div key={change.id} className="px-6 py-4">
              <div className="flex items-start space-x-4">
                {/* Change Icon */}
                <div className="flex-shrink-0 mt-1">
                  {getChangeIcon(change.change_type)}
                </div>

                {/* Change Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-sm font-medium text-gray-900">
                        {change.section_id}
                      </h3>

                      {/* Classification Badge */}
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getClassificationColor(change.classification)}`}>
                        {change.classification}
                      </span>

                      {/* Impact Score */}
                      <div className="flex items-center space-x-1">
                        <div className={`w-2 h-2 rounded-full ${getImpactColor(change.impact_score)}`}></div>
                        <span className="text-xs text-gray-500">
                          Impact: {(change.impact_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    {/* Expand Button */}
                    <button
                      onClick={() => toggleExpanded(change.id)}
                      className="flex items-center text-gray-400 hover:text-gray-600"
                    >
                      {expandedChanges.has(change.id) ? (
                        <ChevronDownIcon className="h-5 w-5" />
                      ) : (
                        <ChevronRightIcon className="h-5 w-5" />
                      )}
                    </button>
                  </div>

                  {/* Change Metadata */}
                  <div className="mt-1 text-sm text-gray-600">
                    <p>
                      {change.change_type.charAt(0).toUpperCase() + change.change_type.slice(1)} in{' '}
                      <span className="font-medium">{getSourceUrl(change.source_id)}</span>
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatDistanceToNow(new Date(change.detected_at), { addSuffix: true })} •{' '}
                      Confidence: {(change.confidence_score * 100).toFixed(0)}%
                    </p>
                  </div>

                  {/* Expanded Content */}
                  {expandedChanges.has(change.id) && (
                    <div className="mt-4 space-y-4">
                      {/* Old Content */}
                      {change.old_content && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 mb-2">Previous Content:</h4>
                          <div className="bg-red-50 border border-red-200 rounded-md p-3">
                            <pre className="text-sm text-gray-800 whitespace-pre-wrap">
                              {change.old_content}
                            </pre>
                          </div>
                        </div>
                      )}

                      {/* New Content */}
                      {change.new_content && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 mb-2">New Content:</h4>
                          <div className="bg-green-50 border border-green-200 rounded-md p-3">
                            <pre className="text-sm text-gray-800 whitespace-pre-wrap">
                              {change.new_content}
                            </pre>
                          </div>
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex space-x-3">
                        <button
                          onClick={() => onChangeSelect?.(change)}
                          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                        >
                          View Full Context
                        </button>
                        <button className="text-sm text-gray-600 hover:text-gray-800">
                          Export Change
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ChangeViewer;