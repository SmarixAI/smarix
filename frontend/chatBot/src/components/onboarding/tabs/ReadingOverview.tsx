'use client';

import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import ModuleCard from '../cards/ReadingOverview/ModuleCard';
import OverviewModal from '../modals/ReadingOverview/ContentModal';
import { modules } from '../constants/ReadingOverview/modules';
import { useModuleContent } from '../hooks/ReadingOverview/useModuleContent';
import type { Module } from '../../../../types/onboarding';

interface ReadingOverviewProps {
  employeeId?: string | null;
  activeRepos?: string[];
  onboardingData?: any;
  onUpdateProgress?: (section: string, itemId: string, updates: any) => void;
}

export default function ReadingOverview({ employeeId, activeRepos = [], onboardingData, onUpdateProgress }: ReadingOverviewProps) {
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
      <div className="mb-6">
        <h2 className="text-xl font-bold tracking-tight mb-2 text-[#0E1B2E]">
          Reading & Overview
        </h2>
        <p className="text-sm text-[#0E1B2E]/60">
          Start your journey with these essential topics. Get familiar with the basics before diving deeper.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-5 mb-5">
        {memoizedModules.map((module, index) => (
          <ModuleCard
            key={module.id}
            module={module}
            index={index}
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
        <div className="fixed bottom-4 right-4 z-50">
          <div className="px-6 py-3 rounded-lg shadow-lg bg-red-100 text-red-900 border border-red-200">
            {error}
          </div>
        </div>
      )}

      {selectedModule && (
        <OverviewModal
          isOpen={isModalOpen}
          onClose={handleModalClose}
          title={selectedModule.title}
          moduleId={selectedModule.id}
          activeRepos={activeRepos}
        />
      )}
    </>
  );
}
