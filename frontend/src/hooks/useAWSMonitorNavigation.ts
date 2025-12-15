import { useNavigate, useLocation } from 'react-router-dom';
import { useCallback } from 'react';

interface UseAWSMonitorNavigationProps {
  /** Base path where monitor is mounted */
  basePath?: string;
  /** Return path when navigating back */
  returnPath?: string;
}

export const useAWSMonitorNavigation = ({
  basePath = '/aws-monitor',
  returnPath = '/',
}: UseAWSMonitorNavigationProps = {}) => {
  const navigate = useNavigate();
  const location = useLocation();

  const navigateToMonitor = useCallback((section?: string) => {
    const targetPath = section ? `${basePath}/${section}` : basePath;
    navigate(targetPath, {
      state: { returnPath: location.pathname }
    });
  }, [navigate, basePath, location.pathname]);

  const navigateBack = useCallback(() => {
    const backPath = location.state?.returnPath || returnPath;
    navigate(backPath);
  }, [navigate, location.state, returnPath]);

  const isInMonitor = location.pathname.startsWith(basePath);

  return {
    navigateToMonitor,
    navigateBack,
    isInMonitor,
    currentSection: isInMonitor
      ? location.pathname.replace(basePath, '').split('/')[1] || 'dashboard'
      : null,
  };
};

// Hook for monitor-specific navigation
export const useMonitorSections = () => {
  const navigate = useNavigate();

  const sections = [
    { id: 'dashboard', name: 'Dashboard', path: '/dashboard' },
    { id: 'profiles', name: 'Profiles', path: '/profiles' },
    { id: 'content', name: 'Content', path: '/content' },
    { id: 'changes', name: 'Changes', path: '/changes' },
    { id: 'digests', name: 'Digests', path: '/digests' },
    { id: 'analytics', name: 'Analytics', path: '/analytics' },
    { id: 'settings', name: 'Settings', path: '/settings' },
  ];

  const navigateToSection = useCallback((sectionId: string, basePath = '/aws-monitor') => {
    const section = sections.find(s => s.id === sectionId);
    if (section) {
      navigate(`${basePath}${section.path}`);
    }
  }, [navigate]);

  return {
    sections,
    navigateToSection,
  };
};