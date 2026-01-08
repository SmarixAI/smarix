'use client';

import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import ModuleCard from '../cards/ReadingOverview/ModuleCard';
import OverviewModal from '../modals/ReadingOverview/ContentModal';
import { modules } from '../constants/ReadingOverview/modules';
import { useModuleContent } from '../hooks/ReadingOverview/useModuleContent';
import type { Module } from '../../../../types/onboarding';

interface ReadingOverviewProps {
  darkMode: boolean;
  mousePosition: { x: number; y: number };
  employeeId?: string | null;
  activeRepos?: string[];
  onboardingData?: any;
  onUpdateProgress?: (section: string, itemId: string, updates: any) => void;
}

export default function ReadingOverview({ darkMode, mousePosition, employeeId, activeRepos = [], onboardingData, onUpdateProgress }: ReadingOverviewProps) {
  // Initialize all modules as visible to prevent disappearing
  const [visibleModules, setVisibleModules] = useState<Set<string>>(
    new Set(modules.map(m => `module-${m.id}`))
  );
  const moduleRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedModule, setSelectedModule] = useState<Module | null>(null);
  
  const { content, isLoading, error, fetchContent, clearContent } = useModuleContent();

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        setVisibleModules((prevVisible) => {
          const newVisibleModules = new Set(prevVisible);
          let hasChanges = false;

          entries.forEach((entry) => {
            if (entry.isIntersecting && !newVisibleModules.has(entry.target.id)) {
              newVisibleModules.add(entry.target.id);
              hasChanges = true;
            }
            // Keep modules visible once they've been seen - don't remove them
          });

          return hasChanges ? newVisibleModules : prevVisible;
        });
      },
      { threshold: 0.1, rootMargin: '0px' }
    );

    Object.values(moduleRefs.current).forEach((ref) => {
      if (ref) observer.observe(ref);
    });

    return () => observer.disconnect();
  }, []);

  const handleCardClick = useCallback(async (moduleId: string) => {
    const module = modules.find((m) => m.id === moduleId);
    if (!module || module.locked) return;

    setSelectedModule(module);
    setIsModalOpen(true);
    
    // Use the first active repo if available
    const repo = activeRepos.length > 0 ? activeRepos[0] : undefined;
    fetchContent(moduleId, repo);
  }, [fetchContent, activeRepos]);

  const handleModalClose = useCallback(() => {
    setIsModalOpen(false);
    clearContent();
    setTimeout(() => setSelectedModule(null), 300);
  }, [clearContent]);

  const memoizedModules = useMemo(() => modules, []);

  return (
    <>
      <div className="mb-6 animate-slide-in-right">
        <h2
          className={`text-4xl font-bold mb-2 ${
            darkMode
              ? 'bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent'
              : 'bg-gradient-to-r from-indigo-600 via-cyan-600 to-teal-600 bg-clip-text text-transparent'
          }`}
        >
          Reading & Overview
        </h2>
        <p className={`text-base ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>
          Start your journey with these essential topics. Get familiar with the basics before diving deeper.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-5 mb-5">
        {memoizedModules.map((module, index) => (
          <ModuleCard
            key={module.id}
            module={module}
            index={index}
            darkMode={darkMode}
            mousePosition={mousePosition}
            isVisible={visibleModules.has(`module-${module.id}`)}
            onCardClick={handleCardClick}
            ref={(el) => {
              if (el) {
                moduleRefs.current[`module-${module.id}`] = el;
              }
            }}
          />
        ))}
      </div>

      {error && (
        <div className="fixed bottom-4 right-4 z-50 animate-slide-in-up">
          <div
            className={`px-6 py-3 rounded-xl shadow-lg ${
              darkMode ? 'bg-red-900/90 text-red-200' : 'bg-red-100 text-red-900'
            }`}
          >
            {error}
          </div>
        </div>
      )}

      {selectedModule && (
        <OverviewModal
          isOpen={isModalOpen}
          onClose={handleModalClose}
          darkMode={darkMode}
          title={selectedModule.title}
          moduleId={selectedModule.id}
          activeRepos={activeRepos}
        />
      )}
    </>
  );
}
