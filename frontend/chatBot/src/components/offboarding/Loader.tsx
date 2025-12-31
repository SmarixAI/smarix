'use client';

import { Loader2 } from 'lucide-react';

interface LoaderProps {
  darkMode?: boolean;
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  fullScreen?: boolean;
}

export default function Loader({ 
  darkMode = false, 
  message = 'Loading...', 
  size = 'md',
  fullScreen = false 
}: LoaderProps) {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16'
  };

  const spinnerSize = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  };

  const content = (
    <div className="text-center">
      <div className={`${sizeClasses[size]} mx-auto mb-4 flex items-center justify-center`}>
        <Loader2 
          className={`${spinnerSize[size]} animate-spin ${
            darkMode 
              ? "text-indigo-400" 
              : "text-indigo-600"
          }`} 
        />
      </div>
      {message && (
        <p className={`text-lg font-semibold ${
          darkMode ? "text-gray-300" : "text-slate-700"
        }`}>
          {message}
        </p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className={`min-h-screen flex items-center justify-center transition-colors duration-300 ${
        darkMode 
          ? "bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800" 
          : "bg-gradient-to-br from-slate-50 via-indigo-50/30 to-purple-50/30"
      }`}>
        {content}
      </div>
    );
  }

  return (
    <div className={`flex items-center justify-center py-12 transition-colors duration-300 ${
      darkMode ? "bg-gray-800/50" : "bg-white/50"
    }`}>
      {content}
    </div>
  );
}

