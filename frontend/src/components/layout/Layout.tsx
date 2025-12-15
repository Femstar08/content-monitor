import React from 'react';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <main className="flex-1 overflow-y-auto">
      <div className="p-6">
        {children}
      </div>
    </main>
  );
};

export default Layout;