import React, { useState, useRef, useEffect } from 'react';

interface AWSContentMonitorIframeProps {
  /** URL where the monitor is deployed */
  monitorUrl?: string;
  /** Height of the iframe */
  height?: string;
  /** Width of the iframe */
  width?: string;
  /** Additional CSS classes */
  className?: string;
  /** Callback when monitor sends messages */
  onMessage?: (data: any) => void;
}

const AWSContentMonitorIframe: React.FC<AWSContentMonitorIframeProps> = ({
  monitorUrl = 'http://localhost:3002',
  height = '600px',
  width = '100%',
  className = '',
  onMessage,
}) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Only accept messages from the monitor URL
      if (event.origin !== new URL(monitorUrl).origin) return;

      if (onMessage) {
        onMessage(event.data);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [monitorUrl, onMessage]);

  const handleLoad = () => {
    setIsLoading(false);
  };

  const sendMessage = (data: any) => {
    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.postMessage(data, monitorUrl);
    }
  };

  return (
    <div className={`relative ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50 rounded-lg">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      )}

      <iframe
        ref={iframeRef}
        src={monitorUrl}
        width={width}
        height={height}
        onLoad={handleLoad}
        className="border border-gray-200 rounded-lg shadow-sm"
        title="AWS Content Monitor"
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
      />
    </div>
  );
};

export default AWSContentMonitorIframe;